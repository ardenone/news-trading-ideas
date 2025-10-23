import axios, { AxiosInstance } from 'axios';
import type {
  Event,
  TradingIdea,
  FeedMetadata,
  DashboardData,
  EventsResponse,
  TradingIdeasResponse,
  FeedsResponse,
  EventFilters,
  IdeaFilters,
} from '@/types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: `${API_BASE_URL}/api`,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 10000,
    });

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('API Error:', error);
        return Promise.reject(error);
      }
    );
  }

  // Dashboard
  async getDashboard(): Promise<DashboardData> {
    const response = await this.client.get<DashboardData>('/dashboard');
    return response.data;
  }

  // Events
  async getEvents(filters: Partial<EventFilters> = {}, limit = 50, offset = 0): Promise<EventsResponse> {
    const params = new URLSearchParams();
    params.append('limit', limit.toString());
    params.append('offset', offset.toString());

    if (filters.sortBy) params.append('sort', filters.sortBy);
    if (filters.timeRange) params.append('timeRange', filters.timeRange);
    if (filters.withIdea !== undefined) params.append('withThesis', filters.withIdea.toString());

    const response = await this.client.get<EventsResponse>('/events', { params });
    return response.data;
  }

  async getEvent(id: number): Promise<Event> {
    const response = await this.client.get<Event>(`/events/${id}`);
    return response.data;
  }

  // Trading Ideas
  async getTradingIdeas(filters: Partial<IdeaFilters> = {}, limit = 10): Promise<TradingIdeasResponse> {
    const params = new URLSearchParams();
    params.append('limit', limit.toString());

    const response = await this.client.get<TradingIdeasResponse>('/trading-ideas', { params });
    return response.data;
  }

  async getTradingIdea(eventId: number): Promise<TradingIdea> {
    const response = await this.client.get<TradingIdea>(`/thesis/${eventId}`);
    return response.data;
  }

  // Feeds
  async getFeeds(): Promise<FeedsResponse> {
    const response = await this.client.get<FeedsResponse>('/feeds');
    return response.data;
  }

  async refreshFeeds(feedIds?: number[], force = false): Promise<{ status: string; feeds_refreshed: number; new_articles: number }> {
    const response = await this.client.post('/feeds/refresh', { feed_ids: feedIds, force });
    return response.data;
  }

  async addFeed(url: string, name: string): Promise<FeedMetadata> {
    const response = await this.client.post<FeedMetadata>('/feeds', { feed_url: url, feed_name: name });
    return response.data;
  }

  async updateFeed(id: number, data: Partial<FeedMetadata>): Promise<FeedMetadata> {
    const response = await this.client.put<FeedMetadata>(`/feeds/${id}`, data);
    return response.data;
  }

  async deleteFeed(id: number): Promise<void> {
    await this.client.delete(`/feeds/${id}`);
  }

  async testFeed(url: string): Promise<{ valid: boolean; article_count?: number; error?: string }> {
    const response = await this.client.get(`/feeds/test`, { params: { url } });
    return response.data;
  }

  // Health check
  async healthCheck(): Promise<{ status: string }> {
    const response = await this.client.get('/health');
    return response.data;
  }
}

export const apiClient = new ApiClient();
