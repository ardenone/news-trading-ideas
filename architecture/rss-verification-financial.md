# RSS Feed Verification Report - Financial/Markets Feeds
**Verification Date:** October 22, 2025
**Verified By:** RSS Feed Verification Specialist

## Summary
- **Total Feeds Tested:** 17
- **Working Feeds:** 13
- **Broken/Inaccessible Feeds:** 4
- **Feeds with Recent Content (< 48hrs):** 10
- **Feeds with Stale Content:** 3

## Detailed Results

| # | Feed URL | Status | Most Recent Article | Age (hrs) | Notes |
|---|----------|--------|-------------------|-----------|-------|
| 1 | https://www.cnbc.com/id/15838459/device/rss/rss.html | ✅ ACTIVE | Wed, 22 Oct 2025 22:46:43 GMT | ~3 hrs | Mad Money - Recent content |
| 2 | https://www.cnbc.com/id/19794221/device/rss/rss.html | ✅ ACTIVE | Wed, 22 Oct 2025 13:00:46 GMT | ~13 hrs | Europe News - Recent |
| 3 | https://www.cnbc.com/id/20910258/device/rss/rss.html | ✅ ACTIVE | Wed, 22 Oct 2025 06:12:45 GMT | ~20 hrs | Economy - Recent |
| 4 | https://www.cnbc.com/id/28282083/device/rss/rss.html | ✅ ACTIVE | Mon, 29 Sep 2025 23:50 GMT | ~23 days | **STALE** - Options Action weekly show |
| 5 | https://www.cnbc.com/id/10000664/device/rss/rss.html | ✅ ACTIVE | Wed, 22 Oct 2025 23:00 GMT | ~3 hrs | Finance - Recent |
| 6 | https://www.cnbc.com/id/10000113/device/rss/rss.html | ✅ ACTIVE | Thu, 23 Oct 2025 00:39:44 GMT | ~1 hr | Politics - Recent |
| 7 | https://www.cnbc.com/id/15838446/device/rss/rss.html | ❌ STALE | Tue, 01 Jun 2021 03:49 GMT | ~4 years | **DEAD FEED** - Kudlow's Corner discontinued |
| 8 | https://www.cnbc.com/id/38818154/device/rss/rss.html | ✅ ACTIVE | Tue, 21 Oct 2025 14:46:07 GMT | ~35 hrs | Net Net - Recent |
| 9 | https://feeds.a.dj.com/rss/RSSMarketsMain.xml | ⚠️ DATE MISMATCH | Mon, 27 Jan 2025 14:26:00 -0500 | **FUTURE DATE** | WSJ Markets - Date appears incorrect (9 months in past from verification date) |
| 10 | https://feeds.a.dj.com/rss/RSSWorldNews.xml | ⚠️ DATE MISMATCH | Mon, 27 Jan 2025 14:23:00 -0500 | **FUTURE DATE** | WSJ World - Date appears incorrect (9 months in past from verification date) |
| 11 | http://feeds.marketwatch.com/marketwatch/topstories/ | ❌ BLOCKED | N/A | N/A | **INACCESSIBLE** - Feed blocked by provider |
| 12 | https://www.ft.com/markets?format=rss | ❌ BLOCKED | N/A | N/A | **INACCESSIBLE** - Feed blocked by provider |
| 13 | https://www.ft.com/global-economy?format=rss | ❌ BLOCKED | N/A | N/A | **INACCESSIBLE** - Feed blocked by provider |
| 14 | https://www.ft.com/companies?format=rss | ❌ BLOCKED | N/A | N/A | **INACCESSIBLE** - Feed blocked by provider |
| 15 | https://finance.yahoo.com/news/rssindex | ⚠️ DATE MISMATCH | 2025-10-21T15:38:13Z | **FUTURE DATE** | Yahoo Finance - Date appears incorrect (1 day in past from verification date) |
| 16 | https://seekingalpha.com/feed.xml | ✅ ACTIVE | Wed, 22 Oct 2025 22:19:24 -0400 | ~4 hrs | All Articles - Recent |
| 17 | http://feeds.bbci.co.uk/news/business/rss.xml | ✅ ACTIVE | Thu, 23 Oct 2025 02:14:21 GMT | <1 hr | BBC Business - Very recent |

## Findings & Recommendations

### ✅ RELIABLE FEEDS (Recommended)
1. **CNBC Feeds** - Most are active with recent content:
   - Mad Money (Feed 1)
   - Europe News (Feed 2)
   - Economy (Feed 3)
   - Finance (Feed 5)
   - Politics (Feed 6)
   - Net Net (Feed 8)

2. **BBC Business** (Feed 17) - Excellent, very recent updates

3. **Seeking Alpha** (Feed 16) - Active and recent

### ⚠️ ISSUES IDENTIFIED

#### Date Mismatches (Possible Feed Errors)
- **WSJ Feeds** (Feeds 9-10): Showing dates from January 2025, which is 9 months in the past from verification date (October 2025). This appears to be a feed error or the dates may be using a different timezone/format.
- **Yahoo Finance** (Feed 15): Showing October 21, 2025, which is 1 day before verification date. This could be legitimate if it's the most recent article or a timezone issue.

#### Stale Content
- **Options Action** (Feed 4): Last update 23 days ago - This is a weekly show, so updates are less frequent
- **Kudlow's Corner** (Feed 7): Last update June 2021 - **DEAD FEED, SHOULD BE REMOVED**

#### Blocked/Inaccessible Feeds
- **MarketWatch** (Feed 11): Feed blocked or protected
- **All Financial Times Feeds** (Feeds 12-14): All three FT feeds are blocked/protected

### 🔧 RECOMMENDATIONS

1. **REMOVE DEAD FEEDS:**
   - Feed 7 (Kudlow's Corner) - Not updated since 2021

2. **REPLACE BLOCKED FEEDS:**
   - Replace MarketWatch feed with alternative
   - Replace Financial Times feeds with accessible alternatives

3. **INVESTIGATE DATE ISSUES:**
   - Verify WSJ feed dates (Feeds 9-10) - may need parser adjustment
   - Monitor Yahoo Finance feed (Feed 15) for consistency

4. **ALTERNATIVE FEEDS TO CONSIDER:**
   - Reuters Business: `http://feeds.reuters.com/reuters/businessNews`
   - Bloomberg Markets: Consider if API access available
   - Barron's: `https://www.barrons.com/articles/rss`
   - Forbes Markets: Check for available RSS feeds

5. **UPDATE FREQUENCY NOTES:**
   - Most active feeds update multiple times per hour
   - Weekly show feeds (Options Action) update once per week
   - Consider separate categories for high-frequency vs. weekly content

### 📊 FEED HEALTH SCORE

| Category | Count | Percentage |
|----------|-------|------------|
| Excellent (< 6 hrs) | 6 | 35% |
| Good (6-48 hrs) | 4 | 24% |
| Stale (> 48 hrs) | 3 | 18% |
| Blocked/Error | 4 | 24% |

**Overall Health: 59% of feeds are working with recent content**

## Next Steps

1. Remove dead feed (Kudlow's Corner)
2. Find replacements for blocked feeds (MarketWatch, Financial Times)
3. Test alternative feeds from Reuters, Barron's
4. Implement feed health monitoring
5. Set up alerts for feeds that haven't updated in 48+ hours
6. Consider categorizing feeds by update frequency (real-time vs. daily vs. weekly)

---
*Note: This verification was performed on October 22, 2025. Feed availability and content freshness may change over time. Regular monitoring recommended.*
