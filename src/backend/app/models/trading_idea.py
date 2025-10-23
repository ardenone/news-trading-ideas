"""Trading Ideas models"""

from sqlalchemy import Column, Integer, String, DateTime, Float, Text, ForeignKey, JSON, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class TradingIdea(Base):
    """Trading idea generated from a news event"""

    __tablename__ = "trading_ideas"

    idea_id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(Integer, ForeignKey("news_events.event_id", ondelete="CASCADE"), nullable=False)

    headline = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    trading_thesis = Column(Text, nullable=False)

    confidence_score = Column(Float, default=0.0)
    generated_at = Column(DateTime, server_default=func.now(), index=True)

    status = Column(
        String(20),
        default="new",
        index=True
    )  # new, reviewed, actioned, expired, rejected

    expires_at = Column(DateTime, nullable=True, index=True)

    # OpenAI API metadata
    model_used = Column(String(50))
    tokens_used = Column(Integer)
    cost_usd = Column(Float)

    # Additional context (JSON)
    research_highlights = Column(JSON, nullable=True)
    risk_warnings = Column(JSON, nullable=True)

    # Relationships
    event = relationship("NewsEvent", backref="trading_ideas")
    strategies = relationship("TradeStrategy", back_populates="idea", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_ideas_status", "status", "generated_at"),
        Index("idx_ideas_event", "event_id", "status"),
    )

    def __repr__(self):
        return f"<TradingIdea(idea_id={self.idea_id}, headline='{self.headline[:50]}...')>"


class TradeStrategy(Base):
    """Specific trade strategy for a trading idea"""

    __tablename__ = "trade_strategies"

    strategy_id = Column(Integer, primary_key=True, autoincrement=True)
    idea_id = Column(Integer, ForeignKey("trading_ideas.idea_id", ondelete="CASCADE"), nullable=False)

    strategy_type = Column(String(20), nullable=False)  # momentum, reversal, pairs, options, futures
    ticker = Column(String(20), nullable=False, index=True)

    entry_conditions = Column(Text, nullable=False)
    exit_target_profit = Column(Float, nullable=True)
    exit_target_loss = Column(Float, nullable=True)

    time_horizon = Column(String(20))  # intraday, swing, position, long-term
    position_size_pct = Column(Float, default=1.0)
    risk_reward_ratio = Column(Float, nullable=True)

    # Detailed strategy (JSON)
    entry_details = Column(JSON, nullable=True)
    exit_strategy = Column(JSON, nullable=True)
    risk_management = Column(JSON, nullable=True)
    scenarios = Column(JSON, nullable=True)

    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    status = Column(String(20), default="pending")  # pending, active, closed, cancelled

    # Relationships
    idea = relationship("TradingIdea", back_populates="strategies")

    __table_args__ = (
        Index("idx_strategies_idea", "idea_id", "status"),
        Index("idx_strategies_ticker", "ticker", "status", "created_at"),
    )

    def __repr__(self):
        return f"<TradeStrategy(strategy_id={self.strategy_id}, ticker='{self.ticker}')>"
