import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import { EventCard } from './EventCard';
import { Button } from './ui/Button';
import { Card, CardContent } from './ui/Card';
import { usePolling } from '@/hooks/usePolling';
import type { Event, EventFilters, SortBy, TimeRange } from '@/types';
import { Loader2, Search, Filter } from 'lucide-react';

interface NewsExplorerProps {
  onEventClick: (event: Event) => void;
}

export function NewsExplorer({ onEventClick }: NewsExplorerProps) {
  const [filters, setFilters] = useState<Partial<EventFilters>>({
    sortBy: 'rank',
    timeRange: '24h',
    withIdea: false,
  });
  const [searchTerm, setSearchTerm] = useState('');

  const { data, isLoading, error } = useQuery({
    queryKey: ['events', filters],
    queryFn: () => apiClient.getEvents(filters),
  });

  usePolling({
    queryKey: ['events', filters],
    interval: 30000,
    enabled: true,
  });

  const filteredEvents = data?.events.filter((event) =>
    searchTerm ? event.name.toLowerCase().includes(searchTerm.toLowerCase()) : true
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold mb-2">News Explorer</h1>
        <p className="text-muted-foreground">Browse and search through clustered news events</p>
      </div>

      {/* Search and Filters */}
      <Card>
        <CardContent className="pt-6 space-y-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search events..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>

          {/* Filters */}
          <div className="flex flex-wrap gap-4">
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium">Filters:</span>
            </div>

            {/* Time Range */}
            <select
              value={filters.timeRange}
              onChange={(e) => setFilters({ ...filters, timeRange: e.target.value as TimeRange })}
              className="border rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="1h">Last Hour</option>
              <option value="6h">Last 6 Hours</option>
              <option value="24h">Last 24 Hours</option>
              <option value="all">All Time</option>
            </select>

            {/* Sort By */}
            <select
              value={filters.sortBy}
              onChange={(e) => setFilters({ ...filters, sortBy: e.target.value as SortBy })}
              className="border rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="rank">By Rank</option>
              <option value="time">By Time</option>
              <option value="articles">By Article Count</option>
            </select>

            {/* With Ideas Only */}
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={filters.withIdea}
                onChange={(e) => setFilters({ ...filters, withIdea: e.target.checked })}
                className="rounded border-gray-300 text-primary focus:ring-primary"
              />
              <span className="text-sm">With Trading Ideas</span>
            </label>
          </div>
        </CardContent>
      </Card>

      {/* Events List */}
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : error ? (
        <Card>
          <CardContent className="py-8 text-center">
            <p className="text-sm text-destructive">Failed to load events. Please try again.</p>
          </CardContent>
        </Card>
      ) : filteredEvents && filteredEvents.length > 0 ? (
        <div className="space-y-4">
          <div className="text-sm text-muted-foreground">
            Showing {filteredEvents.length} of {data?.total} events
          </div>
          <div className="grid gap-4">
            {filteredEvents.map((event) => (
              <EventCard key={event.id} event={event} onViewDetails={onEventClick} />
            ))}
          </div>
        </div>
      ) : (
        <Card>
          <CardContent className="py-8 text-center text-muted-foreground">
            No events found matching your criteria
          </CardContent>
        </Card>
      )}
    </div>
  );
}
