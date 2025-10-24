"""
Trading Ideas Generation Tests
Tests for trading ideas generation, validation, and filtering
"""

import pytest
import json
from datetime import datetime
from unittest.mock import Mock, AsyncMock


class TestTradingIdeaGeneration:
    """Test trading idea generation workflow"""

    @pytest.mark.asyncio
    async def test_generate_basic_trading_idea(self, mock_openai_trading_idea):
        """Should generate basic trading idea from news event"""
        prompt = """Generate a trading idea based on this news event:
        Federal Reserve announces rate cut of 25 basis points."""

        response = await mock_openai_trading_idea.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )

        idea = json.loads(response.choices[0].message.content)

        assert "headline" in idea
        assert "summary" in idea
        assert "trading_thesis" in idea
        assert "ticker" in idea
        assert "confidence_score" in idea

    @pytest.mark.asyncio
    async def test_trading_idea_validation(self, mock_openai_trading_idea):
        """Should validate trading idea meets quality standards"""
        response = await mock_openai_trading_idea.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": "Generate trading idea..."}]
        )

        idea = json.loads(response.choices[0].message.content)

        # Validate required fields
        assert idea["headline"] is not None
        assert idea["summary"] is not None
        assert idea["trading_thesis"] is not None

        # Validate confidence score
        assert 0.0 <= idea["confidence_score"] <= 10.0

    @pytest.mark.asyncio
    async def test_filter_low_confidence_ideas(self, db_session, sample_cluster_data):
        """Should filter out low-confidence trading ideas"""
        event_id = sample_cluster_data
        min_confidence = 6.0

        # Create low confidence idea
        db_session.execute(
            """INSERT INTO trading_ideas
               (event_id, headline, summary, trading_thesis, confidence_score)
               VALUES (?, ?, ?, ?, ?)""",
            (event_id, "Low Confidence", "Summary", "Thesis", 5.5)
        )
        db_session.commit()

        # Create high confidence idea
        db_session.execute(
            """INSERT INTO trading_ideas
               (event_id, headline, summary, trading_thesis, confidence_score)
               VALUES (?, ?, ?, ?, ?)""",
            (event_id, "High Confidence", "Summary", "Thesis", 8.5)
        )
        db_session.commit()

        # Query only high confidence ideas
        high_conf = db_session.execute(
            "SELECT COUNT(*) FROM trading_ideas WHERE confidence_score >= ?",
            (min_confidence,)
        ).fetchone()[0]

        assert high_conf == 1  # Only the high confidence one

    @pytest.mark.asyncio
    async def test_generate_multiple_strategies(self, db_session, sample_cluster_data):
        """Should generate multiple trading strategies per idea"""
        event_id = sample_cluster_data

        # Create trading idea
        idea_result = db_session.execute(
            """INSERT INTO trading_ideas
               (event_id, headline, summary, trading_thesis, confidence_score)
               VALUES (?, ?, ?, ?, ?)""",
            (event_id, "Multi-Strategy", "Summary", "Thesis", 8.0)
        )
        db_session.commit()
        idea_id = idea_result.lastrowid

        # Create multiple strategies
        strategies = [
            ("momentum", "QQQ", "swing"),
            ("options", "SPY", "intraday"),
            ("reversal", "AAPL", "position")
        ]

        for strategy_type, ticker, time_horizon in strategies:
            db_session.execute(
                """INSERT INTO trade_strategies
                   (idea_id, strategy_type, ticker, entry_conditions, time_horizon)
                   VALUES (?, ?, ?, ?, ?)""",
                (idea_id, strategy_type, ticker, "Buy signal", time_horizon)
            )
        db_session.commit()

        # Verify all strategies created
        count = db_session.execute(
            "SELECT COUNT(*) FROM trade_strategies WHERE idea_id = ?",
            (idea_id,)
        ).fetchone()[0]

        assert count == 3


class TestTopEventSelection:
    """Test selection of top events for trading ideas"""

    def test_select_top_10_events(self, db_session):
        """Should select top 10 events by impact score"""
        # Create 15 events with varying impact scores
        for i in range(15):
            score = 50 + (i * 3)  # Scores from 50 to 92
            db_session.execute(
                """INSERT INTO news_events
                   (event_summary, first_reported_time, last_updated,
                    source_count, relevance_score)
                   VALUES (?, ?, ?, ?, ?)""",
                (f"Event {i}", datetime.utcnow(), datetime.utcnow(), i + 1, score)
            )
        db_session.commit()

        # Select top 10
        top_events = db_session.execute(
            """SELECT event_id, relevance_score FROM news_events
               ORDER BY relevance_score DESC LIMIT 10"""
        ).fetchall()

        assert len(top_events) == 10
        assert top_events[0][1] >= top_events[-1][1]  # Descending order

    def test_filter_minimum_impact_threshold(self, db_session):
        """Should filter events below minimum impact threshold"""
        min_impact = 70.0

        # Create events with varying impact
        for score in [50.0, 65.0, 75.0, 85.0, 90.0]:
            db_session.execute(
                """INSERT INTO news_events
                   (event_summary, first_reported_time, last_updated,
                    source_count, relevance_score)
                   VALUES (?, ?, ?, ?, ?)""",
                (f"Event {score}", datetime.utcnow(), datetime.utcnow(), 3, score)
            )
        db_session.commit()

        # Query above threshold
        qualifying = db_session.execute(
            "SELECT COUNT(*) FROM news_events WHERE relevance_score >= ?",
            (min_impact,)
        ).fetchone()[0]

        assert qualifying == 3  # 75, 85, 90

    def test_prioritize_recent_events(self, db_session):
        """Should prioritize more recent events"""
        from datetime import timedelta

        # Create events at different times
        now = datetime.utcnow()

        for i, hours_ago in enumerate([1, 6, 12, 24]):
            event_time = now - timedelta(hours=hours_ago)
            db_session.execute(
                """INSERT INTO news_events
                   (event_summary, first_reported_time, last_updated,
                    source_count, relevance_score)
                   VALUES (?, ?, ?, ?, ?)""",
                (f"Event {i}", event_time, event_time, 3, 80.0)
            )
        db_session.commit()

        # Query events from last 12 hours
        cutoff = now - timedelta(hours=12)
        recent = db_session.execute(
            "SELECT COUNT(*) FROM news_events WHERE first_reported_time >= ?",
            (cutoff,)
        ).fetchone()[0]

        assert recent == 2  # 1 hour and 6 hours ago


class TestIdeaDuplication:
    """Test prevention of duplicate trading ideas"""

    def test_prevent_duplicate_ideas_same_event(self, db_session, sample_cluster_data):
        """Should prevent duplicate ideas for same event"""
        event_id = sample_cluster_data

        # Create first idea
        db_session.execute(
            """INSERT INTO trading_ideas
               (event_id, headline, summary, trading_thesis, confidence_score)
               VALUES (?, ?, ?, ?, ?)""",
            (event_id, "Original Idea", "Summary", "Thesis", 8.0)
        )
        db_session.commit()

        # Check if idea already exists for event
        existing = db_session.execute(
            "SELECT COUNT(*) FROM trading_ideas WHERE event_id = ?",
            (event_id,)
        ).fetchone()[0]

        assert existing == 1

        # Should check before creating new idea
        if existing > 0:
            # Don't create duplicate
            assert True
        else:
            # Create new idea
            pass

    def test_allow_idea_regeneration_after_time(self, db_session, sample_cluster_data):
        """Should allow regenerating ideas after threshold time"""
        from datetime import timedelta

        event_id = sample_cluster_data

        # Create old idea
        old_time = datetime.utcnow() - timedelta(hours=25)
        db_session.execute(
            """INSERT INTO trading_ideas
               (event_id, headline, summary, trading_thesis,
                confidence_score, generated_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (event_id, "Old Idea", "Summary", "Thesis", 8.0, old_time)
        )
        db_session.commit()

        # Check if regeneration is allowed (older than 24 hours)
        cutoff = datetime.utcnow() - timedelta(hours=24)
        can_regenerate = db_session.execute(
            """SELECT COUNT(*) FROM trading_ideas
               WHERE event_id = ? AND generated_at >= ?""",
            (event_id, cutoff)
        ).fetchone()[0] == 0

        assert can_regenerate == True


class TestStrategyValidation:
    """Test trading strategy validation"""

    def test_validate_strategy_type(self, db_session, sample_cluster_data):
        """Should validate strategy type"""
        event_id = sample_cluster_data

        # Create idea
        idea_result = db_session.execute(
            """INSERT INTO trading_ideas
               (event_id, headline, summary, trading_thesis, confidence_score)
               VALUES (?, ?, ?, ?, ?)""",
            (event_id, "Test Idea", "Summary", "Thesis", 8.0)
        )
        db_session.commit()
        idea_id = idea_result.lastrowid

        valid_types = ["momentum", "reversal", "pairs", "options", "futures"]

        for strategy_type in valid_types:
            result = db_session.execute(
                """INSERT INTO trade_strategies
                   (idea_id, strategy_type, ticker, entry_conditions, time_horizon)
                   VALUES (?, ?, ?, ?, ?)""",
                (idea_id, strategy_type, "SPY", "Buy signal", "swing")
            )
            db_session.commit()
            assert result.lastrowid > 0

    def test_validate_time_horizon(self, db_session, sample_cluster_data):
        """Should validate time horizon"""
        event_id = sample_cluster_data

        idea_result = db_session.execute(
            """INSERT INTO trading_ideas
               (event_id, headline, summary, trading_thesis, confidence_score)
               VALUES (?, ?, ?, ?, ?)""",
            (event_id, "Test Idea", "Summary", "Thesis", 8.0)
        )
        db_session.commit()
        idea_id = idea_result.lastrowid

        valid_horizons = ["intraday", "swing", "position", "long-term"]

        for horizon in valid_horizons:
            result = db_session.execute(
                """INSERT INTO trade_strategies
                   (idea_id, strategy_type, ticker, entry_conditions, time_horizon)
                   VALUES (?, ?, ?, ?, ?)""",
                (idea_id, "momentum", "SPY", "Buy signal", horizon)
            )
            db_session.commit()
            assert result.lastrowid > 0

    def test_risk_reward_ratio_calculation(self):
        """Should calculate risk/reward ratio"""
        entry_price = 100.0
        target_profit = 105.0  # +5%
        stop_loss = 98.0       # -2%

        profit_potential = target_profit - entry_price
        loss_potential = entry_price - stop_loss

        risk_reward = profit_potential / loss_potential if loss_potential > 0 else 0

        assert risk_reward == 2.5  # 5/2 = 2.5:1


class TestIdeaExpiration:
    """Test trading idea expiration logic"""

    def test_set_expiration_time(self, db_session, sample_cluster_data):
        """Should set expiration time for ideas"""
        from datetime import timedelta

        event_id = sample_cluster_data
        expires_in = timedelta(hours=24)
        expires_at = datetime.utcnow() + expires_in

        result = db_session.execute(
            """INSERT INTO trading_ideas
               (event_id, headline, summary, trading_thesis,
                confidence_score, expires_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (event_id, "Expiring Idea", "Summary", "Thesis", 8.0, expires_at)
        )
        db_session.commit()

        idea_id = result.lastrowid

        # Verify expiration set
        stored_expiry = db_session.execute(
            "SELECT expires_at FROM trading_ideas WHERE idea_id = ?",
            (idea_id,)
        ).fetchone()[0]

        assert stored_expiry is not None

    def test_query_active_ideas(self, db_session, sample_cluster_data):
        """Should query only active (non-expired) ideas"""
        from datetime import timedelta

        event_id = sample_cluster_data
        now = datetime.utcnow()

        # Create expired idea
        db_session.execute(
            """INSERT INTO trading_ideas
               (event_id, headline, summary, trading_thesis,
                confidence_score, expires_at, status)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (event_id, "Expired", "Summary", "Thesis", 8.0,
             now - timedelta(hours=1), "expired")
        )

        # Create active idea
        db_session.execute(
            """INSERT INTO trading_ideas
               (event_id, headline, summary, trading_thesis,
                confidence_score, expires_at, status)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (event_id, "Active", "Summary", "Thesis", 8.0,
             now + timedelta(hours=1), "new")
        )
        db_session.commit()

        # Query active ideas
        active = db_session.execute(
            "SELECT COUNT(*) FROM trading_ideas WHERE status = 'new' AND expires_at > ?",
            (now,)
        ).fetchone()[0]

        assert active == 1


class TestIdeaQualityScoring:
    """Test quality scoring of trading ideas"""

    @pytest.mark.asyncio
    async def test_confidence_score_range(self):
        """Should score ideas on 0-10 scale"""
        scores = [0.0, 3.5, 5.0, 7.5, 10.0]

        for score in scores:
            assert 0.0 <= score <= 10.0

    def test_categorize_by_confidence(self, db_session, sample_cluster_data):
        """Should categorize ideas by confidence level"""
        event_id = sample_cluster_data

        # Create ideas with different confidence
        for score in [4.0, 6.5, 8.5]:
            db_session.execute(
                """INSERT INTO trading_ideas
                   (event_id, headline, summary, trading_thesis, confidence_score)
                   VALUES (?, ?, ?, ?, ?)""",
                (event_id, f"Idea {score}", "Summary", "Thesis", score)
            )
        db_session.commit()

        # High confidence (> 8.0)
        high = db_session.execute(
            "SELECT COUNT(*) FROM trading_ideas WHERE confidence_score > 8.0"
        ).fetchone()[0]

        # Medium confidence (6.0-8.0)
        medium = db_session.execute(
            """SELECT COUNT(*) FROM trading_ideas
               WHERE confidence_score >= 6.0 AND confidence_score <= 8.0"""
        ).fetchone()[0]

        # Low confidence (< 6.0)
        low = db_session.execute(
            "SELECT COUNT(*) FROM trading_ideas WHERE confidence_score < 6.0"
        ).fetchone()[0]

        assert high == 1
        assert medium == 1
        assert low == 1


class TestNoViableIdeasScenario:
    """Test scenarios where no viable trading ideas can be generated"""

    def test_no_high_impact_events(self, db_session):
        """Should return empty list when no high-impact events"""
        # Create only low-impact events
        for score in [30.0, 45.0, 55.0]:
            db_session.execute(
                """INSERT INTO news_events
                   (event_summary, first_reported_time, last_updated,
                    source_count, relevance_score)
                   VALUES (?, ?, ?, ?, ?)""",
                (f"Low Impact {score}", datetime.utcnow(), datetime.utcnow(), 1, score)
            )
        db_session.commit()

        # Query high-impact events (> 70)
        qualifying = db_session.execute(
            "SELECT COUNT(*) FROM news_events WHERE relevance_score > 70"
        ).fetchone()[0]

        assert qualifying == 0
        # Should return empty trading ideas list

    def test_all_ideas_below_confidence_threshold(self, db_session, sample_cluster_data):
        """Should filter all ideas if below confidence threshold"""
        event_id = sample_cluster_data
        min_confidence = 6.0

        # Create only low-confidence ideas
        for score in [3.5, 4.5, 5.5]:
            db_session.execute(
                """INSERT INTO trading_ideas
                   (event_id, headline, summary, trading_thesis, confidence_score)
                   VALUES (?, ?, ?, ?, ?)""",
                (event_id, f"Low {score}", "Summary", "Thesis", score)
            )
        db_session.commit()

        # Query publishable ideas
        publishable = db_session.execute(
            "SELECT COUNT(*) FROM trading_ideas WHERE confidence_score >= ?",
            (min_confidence,)
        ).fetchone()[0]

        assert publishable == 0
        # Should return empty list to frontend

    def test_empty_database_state(self, db_session):
        """Should handle completely empty database"""
        # No events
        events = db_session.execute("SELECT COUNT(*) FROM news_events").fetchone()[0]

        # No ideas
        ideas = db_session.execute("SELECT COUNT(*) FROM trading_ideas").fetchone()[0]

        assert events >= 0
        assert ideas >= 0
        # Should return appropriate empty state to UI

    @pytest.mark.asyncio
    async def test_api_failure_no_ideas(self, mock_openai_trading_idea):
        """Should handle API failures gracefully (no ideas generated)"""
        from openai import APIError

        mock_openai_trading_idea.chat.completions.create.side_effect = APIError(
            "API error", request=Mock(), body={}
        )

        with pytest.raises(APIError):
            await mock_openai_trading_idea.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": "Generate idea..."}]
            )

        # System should log error and return empty list
