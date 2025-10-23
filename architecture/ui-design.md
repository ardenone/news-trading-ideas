# News Trading Ideas System - UI Design Document

## Executive Summary

A lightweight, three-view interface for monitoring RSS feeds, tracking news events, and reviewing AI-generated trading theses. Built with vanilla JavaScript and minimal dependencies for fast loading and real-time updates.

---

## Technology Stack Recommendation

### Core Framework
- **Frontend**: Vanilla JavaScript with Web Components
- **Styling**: CSS3 with CSS Grid/Flexbox (no framework)
- **Real-time**: Server-Sent Events (SSE) for updates
- **Build**: Optional Vite for development (production uses plain HTML/JS/CSS)

### Rationale
- Zero framework overhead (~2KB gzipped JS vs 40KB+ for React)
- Native Web Components for encapsulation
- SSE simpler than WebSocket for one-way server→client updates
- Works without build step in production
- Fast page loads (<100ms)

### Dependencies (Minimal)
```json
{
  "dependencies": {},
  "devDependencies": {
    "vite": "^5.0.0"  // Optional, for dev server only
  }
}
```

---

## Application Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    App Shell (index.html)                │
├─────────────────────────────────────────────────────────┤
│  Navigation Bar                                          │
│  [RSS Feeds] [News Events] [Trading Thesis]             │
└─────────────────────────────────────────────────────────┘
         │                    │                   │
         ▼                    ▼                   ▼
┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐
│   View 1:       │  │   View 2:       │  │   View 3:    │
│  RSS Manager    │  │  Events Board   │  │ Thesis View  │
│                 │  │                 │  │              │
│ <feed-list>     │  │ <event-list>    │  │ <thesis-card>│
│ <feed-form>     │  │ <event-filter>  │  │ <strategy-   │
│ <feed-status>   │  │ <event-card>    │  │  list>       │
└─────────────────┘  └─────────────────┘  └──────────────┘
```

### Component Structure

```javascript
// Custom Web Components
- <app-shell>           // Main app container
- <app-nav>             // Navigation tabs
- <feed-list>           // RSS feed table
- <feed-form>           // Add/edit feed form
- <feed-status>         // Real-time status indicator
- <event-list>          // News events dashboard
- <event-card>          // Individual event summary
- <event-filter>        // Filter controls
- <thesis-viewer>       // Trading thesis display
- <thesis-card>         // Thesis content
- <strategy-list>       // Trading strategies
- <status-badge>        // Reusable status indicator
```

---

## View 1: RSS Feed Management

### ASCII Mockup

```
┌─────────────────────────────────────────────────────────────────────────┐
│  RSS FEED MANAGEMENT                                    [+ Add Feed]    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ Feed URL                         │ Interval │ Next Fetch │ Status│  │
│  ├──────────────────────────────────────────────────────────────────┤  │
│  │ https://rss.cnn.com/money        │ 5 min    │ in 2m 34s  │ ✓     │  │
│  │ https://feeds.reuters.com/money  │ 10 min   │ in 8m 12s  │ ✓     │  │
│  │ https://feeds.bloomberg.com/...  │ 15 min   │ in 14m 3s  │ ⟳     │  │
│  │ https://rss.wsj.com/xml/rss/...  │ 5 min    │ FAILED     │ ✗     │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  Last Update: 2 minutes ago                   Active Feeds: 3/4         │
│                                                                          │
│  ┌─── ADD/EDIT FEED ──────────────────────────────────────────────┐    │
│  │                                                                 │    │
│  │  Feed URL: [_____________________________________________]      │    │
│  │                                                                 │    │
│  │  Update Interval: [5] minutes  [○ 5min ○ 10min ○ 15min ○ 30min]│    │
│  │                                                                 │    │
│  │  [Test Feed]  [Save]  [Cancel]                                 │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

### Features

**Feed Table**
- Sortable columns
- Inline edit for interval
- Quick delete with confirmation
- Color-coded status:
  - Green (✓): Healthy
  - Yellow (⟳): Fetching
  - Red (✗): Error
  - Gray (⏸): Paused

**Real-time Updates**
- Countdown timer to next fetch (updates every second)
- Status badge changes on fetch events
- Toast notifications for errors

**Form Validation**
- URL format validation
- Duplicate feed detection
- Test fetch before saving

### Component: `<feed-list>`

```html
<feed-list>
  <table class="feed-table">
    <thead>
      <tr>
        <th>Feed URL</th>
        <th>Interval</th>
        <th>Next Fetch</th>
        <th>Status</th>
        <th>Actions</th>
      </tr>
    </thead>
    <tbody id="feed-rows">
      <!-- Dynamically populated -->
    </tbody>
  </table>
</feed-list>
```

### State Management

```javascript
// feeds.state.js
class FeedState {
  constructor() {
    this.feeds = [];
    this.listeners = [];
  }

  subscribe(listener) {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  setFeeds(feeds) {
    this.feeds = feeds;
    this.notify();
  }

  updateFeed(id, changes) {
    const index = this.feeds.findIndex(f => f.id === id);
    if (index >= 0) {
      this.feeds[index] = { ...this.feeds[index], ...changes };
      this.notify();
    }
  }

  notify() {
    this.listeners.forEach(listener => listener(this.feeds));
  }
}

export const feedState = new FeedState();
```

---

## View 2: News Events Dashboard

### ASCII Mockup

```
┌─────────────────────────────────────────────────────────────────────────┐
│  NEWS EVENTS DASHBOARD                                                  │
├─────────────────────────────────────────────────────────────────────────┤
│  Filters: [Show All ▼] [Last 24h ▼] [With Thesis Only ☐]      🔄 Live  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ 🔥 Federal Reserve announces rate decision                       │  │
│  │    8 sources • First reported 12 minutes ago        [View Thesis]│  │
│  │    Latest: "Fed holds rates steady at 5.25%-5.50%"               │  │
│  │    ✓ Trading thesis generated                                    │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ Apple announces Q4 earnings beat                                 │  │
│  │    5 sources • First reported 1 hour ago            [View Thesis]│  │
│  │    Latest: "iPhone sales exceed expectations"                    │  │
│  │    ✓ Trading thesis generated                                    │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ Tesla stock surges on delivery numbers                           │  │
│  │    3 sources • First reported 3 hours ago           [View Thesis]│  │
│  │    Latest: "Record quarterly deliveries reported"                │  │
│  │    ⟳ Generating thesis...                                        │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ Oil prices drop 3% on supply concerns                            │  │
│  │    2 sources • First reported 6 hours ago                        │  │
│  │    Latest: "OPEC output increases unexpectedly"                  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  Showing 4 events • Last updated: 5 seconds ago                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Features

**Event Cards**
- Ranked by source count (primary), then time (secondary)
- Visual indicators:
  - 🔥 High-priority (8+ sources)
  - ⚡ Medium-priority (4-7 sources)
  - 📰 Standard (1-3 sources)
- Thesis status badges:
  - ✓ Generated (green)
  - ⟳ Processing (yellow)
  - ⏳ Queued (gray)
  - — None (hidden)

**Real-time Updates**
- New events slide in from top
- Source count increments live
- Auto-hide events >24h old
- "New" badge for events <5min old

**Filtering**
- Time range: All, 1h, 6h, 24h
- Thesis status: All, With Thesis, Processing
- Sort: Sources (default), Time, Alphabetical

### Component: `<event-card>`

```html
<event-card data-event-id="evt-123">
  <div class="event-header">
    <span class="priority-icon">🔥</span>
    <h3 class="event-title">Federal Reserve announces rate decision</h3>
    <button class="view-thesis-btn">View Thesis</button>
  </div>
  <div class="event-meta">
    <span class="source-count">8 sources</span>
    <span class="time-ago">12 minutes ago</span>
  </div>
  <p class="event-latest">Fed holds rates steady at 5.25%-5.50%</p>
  <div class="event-status">
    <status-badge type="success">Trading thesis generated</status-badge>
  </div>
</event-card>
```

### Real-time Logic

```javascript
// sse-client.js
class EventStream {
  constructor(url) {
    this.eventSource = new EventSource(url);
    this.handlers = {};
  }

  on(eventType, handler) {
    this.handlers[eventType] = handler;
    this.eventSource.addEventListener(eventType, (e) => {
      const data = JSON.parse(e.data);
      handler(data);
    });
  }

  connect() {
    this.eventSource.onopen = () => {
      console.log('SSE connected');
      document.querySelector('.live-indicator').classList.add('active');
    };

    this.eventSource.onerror = () => {
      console.error('SSE error');
      document.querySelector('.live-indicator').classList.remove('active');
    };
  }

  disconnect() {
    this.eventSource.close();
  }
}

// Usage
const stream = new EventStream('/api/events/stream');
stream.on('new-event', (event) => {
  eventState.addEvent(event);
});
stream.on('event-updated', (event) => {
  eventState.updateEvent(event.id, event);
});
stream.connect();
```

---

## View 3: Trading Thesis Viewer

### ASCII Mockup

```
┌─────────────────────────────────────────────────────────────────────────┐
│  TRADING THESIS                                    [← Prev] [Next →]    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Event: Federal Reserve announces rate decision                         │
│  Sources: 8 • First Reported: 12 minutes ago                           │
│  Generated: 5 minutes ago                                               │
│                                                                          │
│  ┌─── EVENT SUMMARY ─────────────────────────────────────────────────┐ │
│  │                                                                    │ │
│  │  The Federal Reserve has announced its decision to maintain       │ │
│  │  interest rates at the current level of 5.25%-5.50%, in line     │ │
│  │  with market expectations. Chairman Powell's comments suggest     │ │
│  │  the central bank is taking a data-dependent approach to future   │ │
│  │  policy adjustments. Key themes across reporting include...       │ │
│  │                                                                    │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│  ┌─── TRADING THESIS ────────────────────────────────────────────────┐ │
│  │                                                                    │ │
│  │  The rate hold decision presents a neutral-to-bullish catalyst    │ │
│  │  for risk assets in the near term. With inflation moderating and  │ │
│  │  employment remaining stable, the Fed's pause provides clarity    │ │
│  │  for equity markets. Sectors to watch:                            │ │
│  │                                                                    │ │
│  │  • Technology: Benefits from sustained higher rates ending        │ │
│  │  • Financials: Net interest margins remain favorable              │ │
│  │  • Real Estate: Relief from rate hike fears                       │ │
│  │                                                                    │ │
│  │  Risk factors include potential hawkish pivot if inflation        │ │
│  │  re-accelerates, and geopolitical tensions affecting sentiment.   │ │
│  │                                                                    │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│  ┌─── TRADING STRATEGIES ────────────────────────────────────────────┐ │
│  │                                                                    │ │
│  │  Strategy 1: Long Tech Equities (QQQ)                             │ │
│  │  Entry: Current levels ($372-$375)                                │ │
│  │  Exit: $385 target / $368 stop                                    │ │
│  │  Horizon: 2-3 weeks                                               │ │
│  │  Rationale: Rate stability removes overhang on growth stocks      │ │
│  │  ────────────────────────────────────────────────────────────────  │ │
│  │  Strategy 2: Short US Dollar Index (DXY)                          │ │
│  │  Entry: 106.5-107.0                                               │ │
│  │  Exit: 104.0 target / 108.0 stop                                  │ │
│  │  Horizon: 1-2 weeks                                               │ │
│  │  Rationale: End of rate hikes weakens dollar outlook              │ │
│  │  ────────────────────────────────────────────────────────────────  │ │
│  │  Strategy 3: Long XLF (Financial Sector ETF)                      │ │
│  │  Entry: $38.50-$39.00                                             │ │
│  │  Exit: $40.50 target / $37.80 stop                                │ │
│  │  Horizon: 3-4 weeks                                               │ │
│  │  Rationale: Banks benefit from extended high-rate environment     │ │
│  │                                                                    │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│  [⭐ Bookmark]  [📤 Export PDF]  [✓ Mark Reviewed]                      │
└─────────────────────────────────────────────────────────────────────────┘
```

### Features

**Navigation**
- Prev/Next buttons cycle through events (sorted by rank)
- Deep-linkable URLs: `/thesis/{event-id}`
- Keyboard shortcuts: ← → for navigation

**Content Display**
- Expandable sections for long content
- Syntax highlighting for strategy parameters
- Copy-to-clipboard for individual strategies

**Actions**
- Bookmark: Save to personal watchlist
- Export: Generate PDF report
- Mark Reviewed: Track which theses you've read
- Share: Copy shareable link

### Component: `<thesis-viewer>`

```html
<thesis-viewer data-event-id="evt-123">
  <header class="thesis-header">
    <h2 class="event-title">Federal Reserve announces rate decision</h2>
    <div class="thesis-nav">
      <button class="nav-btn" data-dir="prev">← Prev</button>
      <button class="nav-btn" data-dir="next">Next →</button>
    </div>
  </header>

  <div class="thesis-meta">
    <span>Sources: <strong>8</strong></span>
    <span>First Reported: <time>12 minutes ago</time></span>
    <span>Generated: <time>5 minutes ago</time></span>
  </div>

  <section class="thesis-section">
    <h3>Event Summary</h3>
    <div class="thesis-content" id="event-summary">
      <!-- AI-generated summary -->
    </div>
  </section>

  <section class="thesis-section">
    <h3>Trading Thesis</h3>
    <div class="thesis-content" id="trading-thesis">
      <!-- AI-generated thesis -->
    </div>
  </section>

  <section class="thesis-section">
    <h3>Trading Strategies</h3>
    <strategy-list id="strategies">
      <!-- Strategy cards -->
    </strategy-list>
  </section>

  <footer class="thesis-actions">
    <button class="action-btn" data-action="bookmark">⭐ Bookmark</button>
    <button class="action-btn" data-action="export">📤 Export PDF</button>
    <button class="action-btn" data-action="reviewed">✓ Mark Reviewed</button>
  </footer>
</thesis-viewer>
```

### Strategy Card Component

```html
<strategy-card data-strategy-id="strat-1">
  <div class="strategy-header">
    <h4>Strategy 1: Long Tech Equities (QQQ)</h4>
    <button class="copy-btn" aria-label="Copy strategy">📋</button>
  </div>
  <dl class="strategy-details">
    <dt>Entry:</dt>
    <dd>Current levels ($372-$375)</dd>
    <dt>Exit:</dt>
    <dd>$385 target / $368 stop</dd>
    <dt>Horizon:</dt>
    <dd>2-3 weeks</dd>
    <dt>Rationale:</dt>
    <dd>Rate stability removes overhang on growth stocks</dd>
  </dl>
</strategy-card>
```

---

## API Endpoints Required

### Feed Management

```typescript
GET    /api/feeds                    // List all feeds
POST   /api/feeds                    // Add new feed
PUT    /api/feeds/:id                // Update feed
DELETE /api/feeds/:id                // Remove feed
GET    /api/feeds/:id/test           // Test feed URL
```

**Response Example:**
```json
{
  "feeds": [
    {
      "id": "feed-123",
      "url": "https://rss.cnn.com/money",
      "interval": 5,
      "nextFetch": "2025-10-22T14:30:00Z",
      "status": "healthy",
      "lastFetch": "2025-10-22T14:25:00Z",
      "errorMessage": null
    }
  ]
}
```

### Events

```typescript
GET    /api/events                   // List events (with filters)
GET    /api/events/:id               // Get single event
GET    /api/events/stream            // SSE endpoint for real-time
```

**Query Parameters:**
- `timeRange`: 1h, 6h, 24h, all
- `withThesis`: true, false
- `sortBy`: sources, time, alpha
- `limit`: number

**Response Example:**
```json
{
  "events": [
    {
      "id": "evt-123",
      "headline": "Federal Reserve announces rate decision",
      "description": "The Fed has decided to...",
      "sourceCount": 8,
      "firstReported": "2025-10-22T14:12:00Z",
      "latestUpdate": "2025-10-22T14:24:00Z",
      "latestHeadline": "Fed holds rates steady at 5.25%-5.50%",
      "thesisStatus": "generated",
      "thesisId": "thesis-456",
      "priority": "high"
    }
  ],
  "total": 42,
  "page": 1
}
```

### Trading Thesis

```typescript
GET    /api/thesis/:eventId          // Get thesis for event
POST   /api/thesis/:thesisId/bookmark // Bookmark thesis
POST   /api/thesis/:thesisId/reviewed // Mark as reviewed
GET    /api/thesis/:thesisId/export  // Export PDF
```

**Response Example:**
```json
{
  "thesis": {
    "id": "thesis-456",
    "eventId": "evt-123",
    "eventSummary": "The Federal Reserve has announced...",
    "tradingThesis": "The rate hold decision presents...",
    "strategies": [
      {
        "id": "strat-1",
        "title": "Long Tech Equities (QQQ)",
        "entry": "Current levels ($372-$375)",
        "exit": "$385 target / $368 stop",
        "horizon": "2-3 weeks",
        "rationale": "Rate stability removes overhang..."
      }
    ],
    "generatedAt": "2025-10-22T14:19:00Z",
    "isBookmarked": false,
    "isReviewed": false
  }
}
```

### SSE Event Types

```typescript
// Server-sent event formats
event: new-event
data: { "event": { /* full event object */ } }

event: event-updated
data: { "eventId": "evt-123", "changes": { "sourceCount": 9 } }

event: thesis-generated
data: { "eventId": "evt-123", "thesisId": "thesis-456" }

event: feed-status
data: { "feedId": "feed-123", "status": "fetching" }
```

---

## State Management Architecture

### Single-Source-of-Truth Pattern

```javascript
// state/app.state.js
class AppState {
  constructor() {
    this.feeds = [];
    this.events = [];
    this.currentThesis = null;
    this.filters = {
      timeRange: '24h',
      withThesis: false,
      sortBy: 'sources'
    };
    this.listeners = new Map();
  }

  // Subscribe to specific state slices
  subscribe(key, listener) {
    if (!this.listeners.has(key)) {
      this.listeners.set(key, []);
    }
    this.listeners.get(key).push(listener);

    // Return unsubscribe function
    return () => {
      const listeners = this.listeners.get(key);
      const index = listeners.indexOf(listener);
      if (index > -1) listeners.splice(index, 1);
    };
  }

  // Notify specific listeners
  notify(key) {
    const listeners = this.listeners.get(key) || [];
    listeners.forEach(listener => listener(this[key]));
  }

  // Feed actions
  setFeeds(feeds) {
    this.feeds = feeds;
    this.notify('feeds');
  }

  updateFeed(id, changes) {
    const index = this.feeds.findIndex(f => f.id === id);
    if (index >= 0) {
      this.feeds[index] = { ...this.feeds[index], ...changes };
      this.notify('feeds');
    }
  }

  // Event actions
  setEvents(events) {
    this.events = events;
    this.notify('events');
  }

  addEvent(event) {
    this.events.unshift(event);
    this.notify('events');
  }

  updateEvent(id, changes) {
    const index = this.events.findIndex(e => e.id === id);
    if (index >= 0) {
      this.events[index] = { ...this.events[index], ...changes };
      this.notify('events');
    }
  }

  // Thesis actions
  setCurrentThesis(thesis) {
    this.currentThesis = thesis;
    this.notify('currentThesis');
  }

  // Filter actions
  setFilter(key, value) {
    this.filters[key] = value;
    this.notify('filters');
  }
}

export const appState = new AppState();
```

### Component Binding Example

```javascript
// components/feed-list.js
class FeedListComponent extends HTMLElement {
  connectedCallback() {
    // Subscribe to feeds state
    this.unsubscribe = appState.subscribe('feeds', (feeds) => {
      this.render(feeds);
    });

    // Initial render
    this.render(appState.feeds);
  }

  disconnectedCallback() {
    // Clean up subscription
    this.unsubscribe();
  }

  render(feeds) {
    this.innerHTML = `
      <table class="feed-table">
        <thead>
          <tr>
            <th>Feed URL</th>
            <th>Interval</th>
            <th>Next Fetch</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          ${feeds.map(feed => `
            <tr data-feed-id="${feed.id}">
              <td>${feed.url}</td>
              <td>${feed.interval} min</td>
              <td class="next-fetch" data-timestamp="${feed.nextFetch}">
                ${this.formatCountdown(feed.nextFetch)}
              </td>
              <td><status-badge type="${feed.status}"></status-badge></td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  }

  formatCountdown(timestamp) {
    const ms = new Date(timestamp) - new Date();
    if (ms < 0) return 'Now';
    const minutes = Math.floor(ms / 60000);
    const seconds = Math.floor((ms % 60000) / 1000);
    return `in ${minutes}m ${seconds}s`;
  }
}

customElements.define('feed-list', FeedListComponent);
```

---

## CSS Architecture

### Design System

```css
/* design-system.css */
:root {
  /* Colors */
  --color-primary: #2563eb;
  --color-success: #10b981;
  --color-warning: #f59e0b;
  --color-error: #ef4444;
  --color-neutral-100: #f3f4f6;
  --color-neutral-200: #e5e7eb;
  --color-neutral-800: #1f2937;
  --color-neutral-900: #111827;

  /* Typography */
  --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --font-mono: "SF Mono", Monaco, "Cascadia Code", monospace;
  --font-size-xs: 0.75rem;
  --font-size-sm: 0.875rem;
  --font-size-base: 1rem;
  --font-size-lg: 1.125rem;
  --font-size-xl: 1.25rem;

  /* Spacing */
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-6: 1.5rem;
  --space-8: 2rem;

  /* Shadows */
  --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
  --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);

  /* Border radius */
  --radius-sm: 0.25rem;
  --radius-md: 0.375rem;
  --radius-lg: 0.5rem;
}

/* Base styles */
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: var(--font-sans);
  font-size: var(--font-size-base);
  line-height: 1.5;
  color: var(--color-neutral-900);
  background: var(--color-neutral-100);
}

/* Utility classes */
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--space-4);
}

.card {
  background: white;
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  box-shadow: var(--shadow-md);
}

.btn {
  padding: var(--space-2) var(--space-4);
  border: none;
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: var(--color-primary);
  color: white;
}

.btn-primary:hover {
  background: #1d4ed8;
}
```

### Component-Specific Styles

```css
/* components/event-card.css */
event-card {
  display: block;
  background: white;
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  margin-bottom: var(--space-3);
  box-shadow: var(--shadow-sm);
  transition: box-shadow 0.2s;
  border-left: 4px solid transparent;
}

event-card:hover {
  box-shadow: var(--shadow-md);
}

event-card[data-priority="high"] {
  border-left-color: var(--color-error);
}

event-card[data-priority="medium"] {
  border-left-color: var(--color-warning);
}

.event-header {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-2);
}

.event-title {
  flex: 1;
  font-size: var(--font-size-lg);
  font-weight: 600;
}

.event-meta {
  display: flex;
  gap: var(--space-4);
  font-size: var(--font-size-sm);
  color: var(--color-neutral-600);
  margin-bottom: var(--space-2);
}

.event-latest {
  color: var(--color-neutral-700);
  margin-bottom: var(--space-3);
}
```

---

## Performance Optimization

### Code Splitting

```javascript
// Lazy load views
const loadView = async (viewName) => {
  switch(viewName) {
    case 'feeds':
      return import('./views/feed-manager.js');
    case 'events':
      return import('./views/events-dashboard.js');
    case 'thesis':
      return import('./views/thesis-viewer.js');
  }
};

// Route handler
const router = {
  navigate(view) {
    loadView(view).then(module => {
      document.querySelector('#app-content').innerHTML = '';
      document.querySelector('#app-content').appendChild(
        new module.default()
      );
    });
  }
};
```

### Virtual Scrolling (for large event lists)

```javascript
// Virtual scroll for 1000+ events
class VirtualScroll {
  constructor(container, items, rowHeight) {
    this.container = container;
    this.items = items;
    this.rowHeight = rowHeight;
    this.visibleRows = Math.ceil(container.clientHeight / rowHeight);
    this.scrollTop = 0;

    this.container.addEventListener('scroll', () => {
      this.scrollTop = this.container.scrollTop;
      this.render();
    });

    this.render();
  }

  render() {
    const startIndex = Math.floor(this.scrollTop / this.rowHeight);
    const endIndex = startIndex + this.visibleRows + 1;
    const visibleItems = this.items.slice(startIndex, endIndex);

    this.container.innerHTML = `
      <div style="height: ${this.items.length * this.rowHeight}px; position: relative;">
        <div style="transform: translateY(${startIndex * this.rowHeight}px);">
          ${visibleItems.map(item => this.renderItem(item)).join('')}
        </div>
      </div>
    `;
  }

  renderItem(item) {
    return `<event-card data-event-id="${item.id}"></event-card>`;
  }
}
```

### Debouncing & Throttling

```javascript
// utils/performance.js
export function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

export function throttle(func, limit) {
  let inThrottle;
  return function(...args) {
    if (!inThrottle) {
      func.apply(this, args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
}

// Usage: Throttle scroll events
const handleScroll = throttle(() => {
  // Update UI
}, 100);

window.addEventListener('scroll', handleScroll);
```

---

## Accessibility

### ARIA Labels & Roles

```html
<!-- Screen reader support -->
<nav role="navigation" aria-label="Main navigation">
  <button role="tab" aria-selected="true" aria-controls="feeds-view">
    RSS Feeds
  </button>
  <button role="tab" aria-selected="false" aria-controls="events-view">
    News Events
  </button>
</nav>

<!-- Status announcements -->
<div role="status" aria-live="polite" aria-atomic="true">
  New event: Federal Reserve announces rate decision
</div>

<!-- Form labels -->
<label for="feed-url">Feed URL</label>
<input
  id="feed-url"
  type="url"
  aria-required="true"
  aria-describedby="feed-url-help"
/>
<span id="feed-url-help">Enter a valid RSS feed URL</span>
```

### Keyboard Navigation

```javascript
// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
  // Navigate thesis with arrow keys
  if (e.key === 'ArrowLeft' && currentView === 'thesis') {
    navigateThesis('prev');
  }
  if (e.key === 'ArrowRight' && currentView === 'thesis') {
    navigateThesis('next');
  }

  // Switch views with numbers
  if (e.key === '1') router.navigate('feeds');
  if (e.key === '2') router.navigate('events');
  if (e.key === '3') router.navigate('thesis');
});

// Focus management
const focusTrap = (element) => {
  const focusableElements = element.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );
  const firstElement = focusableElements[0];
  const lastElement = focusableElements[focusableElements.length - 1];

  element.addEventListener('keydown', (e) => {
    if (e.key === 'Tab') {
      if (e.shiftKey && document.activeElement === firstElement) {
        e.preventDefault();
        lastElement.focus();
      } else if (!e.shiftKey && document.activeElement === lastElement) {
        e.preventDefault();
        firstElement.focus();
      }
    }
  });
};
```

---

## Error Handling & Loading States

### Error Boundary Component

```javascript
class ErrorBoundary extends HTMLElement {
  connectedCallback() {
    this.render();
  }

  showError(error) {
    this.innerHTML = `
      <div class="error-container">
        <div class="error-icon">⚠️</div>
        <h2>Something went wrong</h2>
        <p>${error.message}</p>
        <button onclick="location.reload()">Reload Page</button>
      </div>
    `;
  }

  render() {
    this.innerHTML = '<slot></slot>';
  }
}

customElements.define('error-boundary', ErrorBoundary);

// Global error handler
window.addEventListener('error', (event) => {
  const boundary = document.querySelector('error-boundary');
  boundary.showError(event.error);
});
```

### Loading States

```javascript
// Skeleton loader component
class SkeletonLoader extends HTMLElement {
  connectedCallback() {
    this.innerHTML = `
      <div class="skeleton-card">
        <div class="skeleton-line" style="width: 60%"></div>
        <div class="skeleton-line" style="width: 40%"></div>
        <div class="skeleton-line" style="width: 80%"></div>
      </div>
    `;
  }
}

customElements.define('skeleton-loader', SkeletonLoader);
```

```css
/* Loading animations */
.skeleton-line {
  height: 1rem;
  background: linear-gradient(
    90deg,
    #f0f0f0 25%,
    #e0e0e0 50%,
    #f0f0f0 75%
  );
  background-size: 200% 100%;
  animation: loading 1.5s infinite;
  border-radius: var(--radius-sm);
  margin-bottom: var(--space-2);
}

@keyframes loading {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
```

---

## File Structure

```
news-trading-ideas/
├── frontend/
│   ├── index.html                 # Main entry point
│   ├── styles/
│   │   ├── design-system.css      # Design tokens
│   │   ├── components/            # Component styles
│   │   │   ├── feed-list.css
│   │   │   ├── event-card.css
│   │   │   └── thesis-viewer.css
│   │   └── utilities.css          # Utility classes
│   ├── scripts/
│   │   ├── main.js                # App initialization
│   │   ├── state/
│   │   │   └── app.state.js       # Global state
│   │   ├── services/
│   │   │   ├── api.service.js     # API calls
│   │   │   └── sse.service.js     # SSE connection
│   │   ├── components/
│   │   │   ├── app-shell.js
│   │   │   ├── feed-list.js
│   │   │   ├── event-card.js
│   │   │   └── thesis-viewer.js
│   │   ├── views/
│   │   │   ├── feed-manager.js
│   │   │   ├── events-dashboard.js
│   │   │   └── thesis-viewer.js
│   │   └── utils/
│   │       ├── performance.js     # Debounce, throttle
│   │       └── formatters.js      # Date, number formatting
│   ├── assets/
│   │   └── icons/                 # SVG icons
│   └── package.json
```

---

## Build Configuration (Optional)

### Vite Config

```javascript
// vite.config.js
export default {
  root: 'frontend',
  build: {
    outDir: '../dist',
    minify: 'esbuild',
    target: 'es2020',
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor': ['virtual:state'],
        }
      }
    }
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
};
```

---

## Testing Strategy

### Component Tests

```javascript
// tests/components/event-card.test.js
import { describe, it, expect } from 'vitest';
import './components/event-card.js';

describe('EventCard', () => {
  it('renders event data correctly', () => {
    const card = document.createElement('event-card');
    card.setAttribute('data-event-id', 'evt-123');
    document.body.appendChild(card);

    const event = {
      id: 'evt-123',
      headline: 'Test Event',
      sourceCount: 5,
      thesisStatus: 'generated'
    };

    card.setEvent(event);

    expect(card.querySelector('.event-title').textContent).toBe('Test Event');
    expect(card.querySelector('.source-count').textContent).toBe('5 sources');
  });

  it('displays thesis badge when generated', () => {
    const card = document.createElement('event-card');
    card.setEvent({ thesisStatus: 'generated' });

    expect(card.querySelector('status-badge[type="success"]')).toBeTruthy();
  });
});
```

### E2E Tests (Playwright)

```javascript
// tests/e2e/feed-management.spec.js
import { test, expect } from '@playwright/test';

test('can add new RSS feed', async ({ page }) => {
  await page.goto('/');
  await page.click('text=RSS Feeds');

  await page.fill('input[name="feed-url"]', 'https://example.com/rss');
  await page.selectOption('select[name="interval"]', '5');
  await page.click('button:has-text("Save")');

  await expect(page.locator('text=https://example.com/rss')).toBeVisible();
});

test('events update in real-time', async ({ page }) => {
  await page.goto('/');
  await page.click('text=News Events');

  // Wait for SSE connection
  await page.waitForSelector('.live-indicator.active');

  // Simulate server sending new event
  // (requires test backend)
  await expect(page.locator('event-card').first()).toBeVisible({ timeout: 5000 });
});
```

---

## Performance Benchmarks

### Target Metrics

- **First Contentful Paint (FCP)**: < 0.5s
- **Time to Interactive (TTI)**: < 1.5s
- **Total Bundle Size**: < 50KB gzipped
- **SSE Latency**: < 100ms
- **Event Render Time**: < 16ms (60fps)

### Optimization Checklist

- [x] Minify CSS/JS
- [x] Code splitting by view
- [x] Lazy load components
- [x] Debounce user input
- [x] Throttle scroll handlers
- [x] Virtual scrolling for lists
- [x] SSE over WebSocket (lower overhead)
- [x] Cache API responses
- [x] Preload critical resources
- [x] Use CSS containment

---

## Browser Support

### Target Browsers

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

### Polyfills (if needed)

```html
<!-- Only for older browsers -->
<script type="module">
  if (!('customElements' in window)) {
    import('https://unpkg.com/@webcomponents/webcomponentsjs@2.8.0/webcomponents-loader.js');
  }
</script>
```

---

## Deployment

### Static Hosting (Recommended)

```bash
# Build for production
npm run build

# Serve from any static host:
# - Vercel
# - Netlify
# - Cloudflare Pages
# - GitHub Pages

# Or simple Node.js server:
npx serve dist -p 3000
```

### Environment Variables

```javascript
// config.js
export const config = {
  API_BASE_URL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  SSE_ENDPOINT: import.meta.env.VITE_SSE_URL || '/api/events/stream',
  ENABLE_ANALYTICS: import.meta.env.VITE_ANALYTICS === 'true'
};
```

---

## Future Enhancements (Post-MVP)

1. **Dark Mode**: System preference detection + manual toggle
2. **PWA Support**: Offline mode, push notifications
3. **Advanced Filters**: Tag-based, sentiment, custom date ranges
4. **User Preferences**: Personalized watchlists, saved filters
5. **Charts**: Price charts embedded in thesis view
6. **Collaboration**: Share theses with team, comment threads
7. **Mobile App**: React Native wrapper
8. **AI Chat**: Ask questions about thesis

---

## Conclusion

This design prioritizes **speed, simplicity, and real-time responsiveness**. By using vanilla JavaScript with Web Components, we avoid framework overhead while maintaining clean, maintainable code. The SSE-based real-time updates provide instant feedback without WebSocket complexity. Total bundle size remains under 50KB, ensuring fast page loads even on slow connections.

The three-view structure provides clear separation of concerns:
1. **Feed management** for configuration
2. **Event dashboard** for monitoring
3. **Thesis viewer** for analysis

All connected through a lightweight state management system and powered by a simple REST + SSE backend API.
