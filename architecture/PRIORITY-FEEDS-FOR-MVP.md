# PRIORITY RSS FEEDS FOR MVP - Trading System
**Last Updated:** October 22, 2025
**Purpose:** Critical feeds for minimum viable product launch

---

## 🎯 MVP PHILOSOPHY

**Goal:** Maximum market coverage with minimum feed complexity
**Criteria:**
- Real-time or hourly updates
- High reliability (verified working)
- Market-moving content
- Free or accessible feeds (avoid authentication issues)

---

## 🔴 TOP 20 MUST-HAVE FEEDS FOR MVP

### Markets & Finance (10 feeds)

| Priority | Source | Feed URL | Why Critical | Update Freq | Backup Feed |
|----------|--------|----------|-------------|-------------|-------------|
| **#1** | **CNBC Markets** | `https://www.cnbc.com/id/15838459/device/rss/rss.html` | Real-time breaking market news | Real-time | Yahoo Finance |
| **#2** | **Yahoo Finance** | `https://finance.yahoo.com/news/rssindex` | Free, comprehensive, aggregates multiple sources | Real-time | MarketWatch |
| **#3** | **Seeking Alpha** | `https://seekingalpha.com/feed.xml` | Community sentiment, stock analysis | Hourly | Benzinga |
| **#4** | **WSJ Markets** | `https://feeds.content.dowjones.io/public/rss/markets` | Premium institutional news | Hourly | CNBC |
| **#5** | **BBC Business** | `http://feeds.bbci.co.uk/news/business/rss.xml` | International market perspective | Hourly | Reuters (workaround) |
| **#6** | **Benzinga** | `https://www.benzinga.com/feed` | Trading-focused, real-time alerts | Real-time | TheStreet |
| **#7** | **CNBC Investing** | `https://www.cnbc.com/id/19794221/device/rss/rss.html` | Investment news and analysis | Real-time | Yahoo Finance |
| **#8** | **TheStreet** | `https://www.thestreet.com/.rss/full` | Market analysis, trading ideas | Real-time | Motley Fool |
| **#9** | **Barron's** | `https://www.barrons.com/topics/markets` | Weekend analysis, investment insights | Daily | WSJ |
| **#10** | **FT Home** | `https://www.ft.com/rss/home` | Global markets, institutional coverage | Hourly | Bloomberg (workaround) |

### Politics & Policy (5 feeds)

| Priority | Source | Feed URL | Why Critical | Update Freq | Backup Feed |
|----------|--------|----------|-------------|-------------|-------------|
| **#11** | **The Hill - All News** | `https://thehill.com/homenews/feed/` | Congressional news, policy changes | Hourly | Roll Call |
| **#12** | **Washington Post Politics** | `https://feeds.washingtonpost.com/rss/politics` | Breaking political news | Hourly | NPR Politics |
| **#13** | **NPR Politics** | `https://feeds.npr.org/1014/rss.xml` | Analysis, policy impact | Daily | The Hill |
| **#14** | **Fox News Politics** | `https://moxie.foxnews.com/google-publisher/politics.xml` | Conservative perspective, breaking | Real-time | National Review |
| **#15** | **The Hill - Administration** | `https://thehill.com/homenews/administration/feed/` | Executive actions, regulatory news | Hourly | Washington Post |

### General News - Breaking (5 feeds)

| Priority | Source | Feed URL | Why Critical | Update Freq | Backup Feed |
|----------|--------|----------|-------------|-------------|-------------|
| **#16** | **NBC News - Top Stories** | `https://feeds.nbcnews.com/nbcnews/public/news` | Breaking national news | Real-time | ABC News |
| **#17** | **CBS News - Main** | `https://www.cbsnews.com/latest/rss/main` | National breaking news | Real-time | NBC News |
| **#18** | **The Guardian US** | `https://www.theguardian.com/us-news/rss` | International perspective on US news | Hourly | BBC News |
| **#19** | **TechCrunch** | `https://techcrunch.com/feed` | Tech sector news (market-moving) | Real-time | The Verge |
| **#20** | **ProPublica** | `https://www.propublica.org/feeds/propublica/main` | Investigative journalism, scandals | Daily | The Intercept |

---

## 📊 MVP FEED STATISTICS

### Coverage Analysis:
- **Markets/Finance:** 50% (10 feeds)
- **Politics/Policy:** 25% (5 feeds)
- **General/Breaking News:** 25% (5 feeds)

### Update Frequency:
- **Real-time (< 5 min):** 9 feeds (45%)
- **Hourly:** 9 feeds (45%)
- **Daily:** 2 feeds (10%)

### Access Type:
- **Fully Free:** 17 feeds (85%)
- **Freemium (Headlines):** 3 feeds (15%)
- **Premium:** 0 feeds (0% - by design for MVP)

### Reliability:
- **Verified Working:** 18 feeds (90%)
- **Working (Unverified):** 2 feeds (10%)
- **Requires Workaround:** 0 feeds (0% - by design)

### Political Balance:
- **Neutral/Center:** 15 feeds (75%)
- **Conservative:** 1 feed (5%)
- **Liberal:** 4 feeds (20%)

---

## 🚀 IMPLEMENTATION PRIORITY ORDER

### Phase 1: Core Markets (Days 1-3)
**Goal:** Get market-moving news flowing

1. **CNBC Markets** - Highest priority, real-time
2. **Yahoo Finance** - Broad coverage, free
3. **Seeking Alpha** - Sentiment analysis
4. **WSJ Markets** - Institutional news
5. **Benzinga** - Trading signals

**Success Metric:** Detecting earnings announcements within 5 minutes

### Phase 2: Policy & Politics (Days 4-5)
**Goal:** Capture regulatory and policy news

6. **The Hill - All News** - Congressional actions
7. **Washington Post Politics** - Breaking political news
8. **Fox News Politics** - Balance perspective
9. **The Hill - Administration** - Executive actions
10. **NPR Politics** - Policy analysis

**Success Metric:** Detecting policy announcements within 1 hour

### Phase 3: General & Tech News (Days 6-7)
**Goal:** Capture broader market-moving events

11. **NBC News** - Breaking national news
12. **CBS News** - National coverage
13. **TechCrunch** - Tech sector moves
14. **The Guardian US** - International perspective
15. **ProPublica** - Investigative/scandal detection

**Success Metric:** Comprehensive coverage of major events

### Phase 4: Enhancement & Backup (Days 8-10)
**Goal:** Add depth and redundancy

16. **CNBC Investing** - Additional market coverage
17. **TheStreet** - Trading analysis
18. **Barron's** - Weekend insights
19. **FT Home** - Global markets
20. **BBC Business** - International business

**Success Metric:** 99.9% uptime with feed redundancy

---

## ⚡ POLLING SCHEDULE FOR MVP

### Real-Time Tier (Poll every 5 minutes):
```
CNBC Markets
CNBC Investing
Yahoo Finance
Benzinga
TheStreet
NBC News
CBS News
TechCrunch
Fox News Politics
```

### Hourly Tier (Poll every 30 minutes):
```
WSJ Markets
BBC Business
FT Home
The Hill (all feeds)
Washington Post Politics
The Guardian US
```

### Daily Tier (Poll every 2 hours):
```
Barron's
NPR Politics
ProPublica
```

### Total Bandwidth:
- **5-min polls:** 9 feeds × 12/hour = 108 requests/hour
- **30-min polls:** 7 feeds × 2/hour = 14 requests/hour
- **2-hour polls:** 4 feeds × 0.5/hour = 2 requests/hour
- **Total:** ~124 requests/hour (~3,000/day)

---

## 🔧 TECHNICAL SPECIFICATIONS

### Feed Parser Requirements:
```javascript
{
  "formats_supported": ["RSS 2.0", "Atom"],
  "timeout": 10000, // 10 seconds
  "retry_attempts": 3,
  "retry_delay": 5000, // 5 seconds
  "user_agent": "NewsTrading/1.0 (compatible; trading system)",
  "respect_robots_txt": true
}
```

### Deduplication Logic:
```javascript
function deduplicateArticle(article) {
  // Primary: Use GUID/link
  const primaryKey = article.guid || article.link;

  // Secondary: Title + first 200 chars
  const secondaryKey = hash(
    article.title + article.description.substring(0, 200)
  );

  return { primaryKey, secondaryKey };
}
```

### Error Handling:
```javascript
const ERROR_STRATEGIES = {
  "timeout": "retry_with_exponential_backoff",
  "404": "disable_feed_and_alert",
  "403": "check_robots_txt_and_user_agent",
  "429": "implement_rate_limiting",
  "500": "retry_after_delay",
  "invalid_xml": "log_and_skip",
  "no_new_items": "continue_normal_polling"
};
```

---

## 📈 EXPECTED ARTICLE VOLUME

### Per Hour (Conservative Estimate):
- **Markets (10 feeds):** 50-100 articles/hour
- **Politics (5 feeds):** 20-40 articles/hour
- **General News (5 feeds):** 30-60 articles/hour
- **Total:** 100-200 articles/hour

### Per Day:
- **2,400-4,800 articles/day**
- **After deduplication:** ~1,500-3,000 unique articles/day
- **After filtering (markets-relevant):** ~500-1,000 articles/day

### Storage Requirements (30 days):
- **Articles:** 45,000-90,000 articles
- **Text content:** ~2-5 GB (compressed)
- **Metadata:** ~500 MB
- **Total:** ~3-6 GB/month

---

## 🎯 SUCCESS CRITERIA FOR MVP

### Latency:
- ✅ Breaking market news detected within **5 minutes**
- ✅ Earnings announcements captured within **5 minutes**
- ✅ Policy announcements detected within **60 minutes**
- ✅ General news captured within **30 minutes**

### Coverage:
- ✅ 90%+ of major market-moving events captured
- ✅ All S&P 500 earnings announcements detected
- ✅ Major political/regulatory announcements captured
- ✅ Tech sector M&A and funding news covered

### Reliability:
- ✅ 99.5% feed uptime
- ✅ < 5% failed parsing rate
- ✅ Duplicate rate < 10% after deduplication
- ✅ Zero data loss (all articles stored)

### Performance:
- ✅ Feed fetch time < 10 seconds
- ✅ Parse time < 2 seconds per feed
- ✅ Deduplication < 1 second per article
- ✅ Total latency (fetch to database) < 15 seconds

---

## 🚨 RISK MITIGATION

### Feed Failure Scenarios:

**Scenario 1: CNBC Markets Down**
- **Backup:** Yahoo Finance (same polling frequency)
- **Alert:** Email + Slack notification
- **Recovery:** Auto-switch to backup, monitor primary

**Scenario 2: All WSJ/Dow Jones Feeds Down**
- **Backup:** BBC Business + FT Home
- **Alert:** Critical alert to ops team
- **Recovery:** Manual intervention, consider Reuters workaround

**Scenario 3: The Hill Feeds Down**
- **Backup:** Washington Post Politics + NPR Politics
- **Alert:** Warning notification
- **Recovery:** Increase polling on backups

**Scenario 4: Feed Format Change**
- **Detection:** XML validation failure
- **Response:** Log sample, switch to backup
- **Recovery:** Update parser, test, re-enable

### Feed Blocking Scenarios:

**Scenario 5: 403 Forbidden (Bot Detection)**
- **Response:** Rotate user-agent, add delays
- **Backup:** Switch to alternative source
- **Long-term:** Contact publisher for API access

**Scenario 6: 429 Rate Limited**
- **Response:** Exponential backoff, reduce frequency
- **Adjustment:** Increase polling interval by 2x
- **Monitor:** Track rate limit headers

---

## 📝 EXPANSION ROADMAP (Post-MVP)

### Wave 2 (25 additional feeds):
1. **Bloomberg** (via OpenRSS workaround)
2. **Reuters** (via Google News workaround)
3. **MarketWatch** (via Dow Jones alternative)
4. **The Intercept** (investigative)
5. **Mother Jones** (progressive politics)
6. **National Review** (conservative analysis)
7. **The Verge** (tech culture)
8. **Ars Technica** (deep tech)
9. **ESPN** (sports business impact)
10. **Variety** (entertainment M&A)
... (15 more)

### Wave 3 (Regional Coverage):
1. **Chicago Tribune**
2. **Seattle Times** (Amazon, Microsoft, Boeing)
3. **Denver Post**
4. Regional business journals
5. Local political news

### Wave 4 (Specialty Coverage):
1. **Scientific American** (science policy)
2. **MIT Tech Review** (emerging tech)
3. **Motley Fool** (retail sentiment)
4. **Zacks** (earnings analysis)
5. Sector-specific trade publications

---

## 🔐 LEGAL & COMPLIANCE

### Terms of Service Compliance:
- ✅ All feeds used for **personal/non-commercial research** (initially)
- ✅ Proper attribution for all sources
- ✅ No content redistribution
- ⚠️ For commercial trading use, obtain licenses from:
  - Dow Jones (WSJ, Barron's, MarketWatch)
  - Financial Times
  - Washington Post
  - Others as needed

### Data Privacy:
- RSS feeds are public data
- No personal information collected
- GDPR not applicable (US news sources)
- Data retention: 90 days (adjustable)

### Rate Limiting & Ethics:
- Respect robots.txt for all sources
- Implement polite crawling (5-30 min intervals)
- Do not hammer servers (exponential backoff)
- Monitor for rate limit signals

---

## 📊 MONITORING DASHBOARD

### Key Metrics to Track:

**Feed Health:**
```
- Feeds online: 20/20 (100%)
- Average fetch time: 3.2s
- Failed fetches (24h): 12 (0.4%)
- Stale feeds (>2hr): 0
```

**Article Metrics:**
```
- Articles/hour: 147
- Unique articles/hour: 112 (76% after dedup)
- Market-relevant: 68 (61%)
- Storage used: 2.3 GB
```

**Latency:**
```
- Average article age at ingestion: 4.2 min
- Earnings detection: 3.1 min average
- Breaking news: 6.5 min average
- 95th percentile: 12 min
```

**Errors:**
```
- Parse errors: 3 (0.2%)
- Network timeouts: 8 (0.6%)
- Rate limits: 0
- Feed format changes: 0
```

---

## ✅ MVP LAUNCH CHECKLIST

### Pre-Launch (Week 1):
- [ ] Set up feed parsing infrastructure
- [ ] Implement all 20 feeds
- [ ] Test deduplication logic
- [ ] Set up error handling & logging
- [ ] Configure alerts (email + Slack)
- [ ] Test backup feed switching
- [ ] Set up monitoring dashboard
- [ ] Load test (1000 articles/hour)

### Launch Day:
- [ ] Enable all 20 feeds
- [ ] Monitor for 24 hours continuously
- [ ] Verify article ingestion
- [ ] Check deduplication rates
- [ ] Validate market event detection
- [ ] Review error logs
- [ ] Tune polling frequencies

### Post-Launch (Week 2):
- [ ] Analyze coverage gaps
- [ ] Optimize polling frequencies
- [ ] Fine-tune deduplication
- [ ] Add missing categories
- [ ] Plan Wave 2 expansion
- [ ] Document lessons learned

---

## 🎓 LESSONS FROM RESEARCH

### What Worked:
1. ✅ Multiple feeds per category (redundancy)
2. ✅ Mix of free and freemium sources
3. ✅ Avoiding feeds requiring workarounds (for MVP)
4. ✅ Balancing real-time and hourly sources
5. ✅ Including international perspectives (BBC, Guardian, FT)

### What Didn't Work:
1. ❌ Politico feeds (all blocked)
2. ❌ NY Times Politics (blocked)
3. ❌ MarketWatch direct feed (blocked)
4. ❌ Bloomberg official feed (doesn't exist)
5. ❌ Reuters official feed (deprecated)

### Surprises:
1. 💡 CNBC has 40+ individual feeds (highly segmented)
2. 💡 Yahoo Finance most reliable free source
3. 💡 The Hill better than Politico for politics (working feeds)
4. 💡 BBC/Guardian provide excellent US coverage
5. 💡 Many premium sources offer headline feeds for free

---

## 📞 SUPPORT CONTACTS

### For Feed Issues:
- **CNBC:** Check official RSS directory
- **WSJ/Dow Jones:** https://www.dowjones.com/contact/
- **Financial Times:** https://help.ft.com/
- **The Hill:** Use contact form
- **Washington Post:** https://helpcenter.washingtonpost.com/

### For Technical Issues:
- **RSS Validators:** validator.w3.org/feed
- **Feed Generators:** RSS.app, OpenRSS.org
- **Community:** Reddit r/rss, StackOverflow

---

**Document Version:** 1.0
**Last Updated:** October 22, 2025
**Next Review:** Post-MVP launch (Week 2)
**Owner:** Trading System Product Team
