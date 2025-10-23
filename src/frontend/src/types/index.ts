// API Types matching backend schema

export interface Article {
  id: number;
  url: string;
  title: string;
  content: string;
  summary?: string;
  published_at: string;
  fetched_at: string;
  source: string;
  author?: string;
  event_id?: number;
  created_at: string;
}

export interface Event {
  id: number;
  name: string;
  description: string;
  article_count: number;
  source_count: number;
  earliest_at: string;
  latest_at: string;
  rank_score: number;
  has_trading_idea: boolean;
  created_at: string;
  updated_at: string;
  articles?: Article[];
  trading_idea?: TradingIdea;
}

export interface TradingIdea {
  id: number;
  event_id: number;
  idea_text: string;
  reasoning: string;
  instruments: string[];
  confidence: 'low' | 'medium' | 'high';
  timeframe: string;
  created_at: string;
  event?: Event;
}

export interface FeedMetadata {
  id: number;
  feed_url: string;
  feed_name: string;
  last_fetch_at?: string;
  last_success_at?: string;
  article_count: number;
  avg_articles_per_hour: number;
  next_refresh_at?: string;
  is_active: boolean;
  error_count: number;
  last_error?: string;
}

export interface DashboardStats {
  total_articles: number;
  total_events: number;
  total_ideas: number;
  articles_last_24h: number;
  events_last_24h: number;
  active_feeds: number;
}

export interface DashboardData {
  stats: DashboardStats;
  recent_events: Event[];
  recent_ideas: TradingIdea[];
}

// API Response Types
export interface EventsResponse {
  events: Event[];
  total: number;
  limit: number;
  offset: number;
}

export interface TradingIdeasResponse {
  ideas: TradingIdea[];
}

export interface FeedsResponse {
  feeds: FeedMetadata[];
}

// Filter and Sort Types
export type SortBy = 'rank' | 'time' | 'articles';
export type TimeRange = '1h' | '6h' | '24h' | 'all';
export type ConfidenceFilter = 'all' | 'low' | 'medium' | 'high';

export interface EventFilters {
  sortBy: SortBy;
  timeRange: TimeRange;
  withIdea: boolean;
  search?: string;
}

export interface IdeaFilters {
  confidence: ConfidenceFilter;
  timeRange: TimeRange;
  search?: string;
}
