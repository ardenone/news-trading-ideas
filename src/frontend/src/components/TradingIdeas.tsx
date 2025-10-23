import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import { TradingIdeaCard } from './TradingIdeaCard';
import { Card, CardContent } from './ui/Card';
import { usePolling } from '@/hooks/usePolling';
import type { IdeaFilters, ConfidenceFilter } from '@/types';
import { Loader2, Filter } from 'lucide-react';

export function TradingIdeas() {
  const [filters, setFilters] = useState<Partial<IdeaFilters>>({
    confidence: 'all',
    timeRange: '24h',
  });

  const { data, isLoading, error } = useQuery({
    queryKey: ['trading-ideas', filters],
    queryFn: () => apiClient.getTradingIdeas(filters),
  });

  usePolling({
    queryKey: ['trading-ideas', filters],
    interval: 30000,
    enabled: true,
  });

  const filteredIdeas =
    filters.confidence === 'all'
      ? data?.ideas
      : data?.ideas.filter((idea) => idea.confidence === filters.confidence);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold mb-2">Trading Ideas</h1>
        <p className="text-muted-foreground">AI-generated trading strategies for top news events</p>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-wrap gap-4">
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium">Filters:</span>
            </div>

            {/* Confidence Filter */}
            <select
              value={filters.confidence}
              onChange={(e) => setFilters({ ...filters, confidence: e.target.value as ConfidenceFilter })}
              className="border rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="all">All Confidence Levels</option>
              <option value="high">High Confidence</option>
              <option value="medium">Medium Confidence</option>
              <option value="low">Low Confidence</option>
            </select>
          </div>
        </CardContent>
      </Card>

      {/* Trading Ideas List */}
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : error ? (
        <Card>
          <CardContent className="py-8 text-center">
            <p className="text-sm text-destructive">Failed to load trading ideas. Please try again.</p>
          </CardContent>
        </Card>
      ) : filteredIdeas && filteredIdeas.length > 0 ? (
        <div className="space-y-4">
          <div className="text-sm text-muted-foreground">
            Showing {filteredIdeas.length} trading ideas
          </div>
          <div className="grid gap-4">
            {filteredIdeas.map((idea) => (
              <TradingIdeaCard key={idea.id} idea={idea} showEvent={true} />
            ))}
          </div>
        </div>
      ) : (
        <Card>
          <CardContent className="py-8 text-center">
            <div className="space-y-2">
              <p className="text-muted-foreground">No trading ideas available yet.</p>
              <p className="text-sm text-muted-foreground">
                Trading ideas are automatically generated for the top 10 ranked news events.
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
