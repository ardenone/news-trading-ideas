import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card';
import { EventCard } from './EventCard';
import { TradingIdeaCard } from './TradingIdeaCard';
import { usePolling } from '@/hooks/usePolling';
import { Loader2, TrendingUp, FileText, Newspaper, Activity } from 'lucide-react';
import type { Event } from '@/types';

interface DashboardProps {
  onEventClick: (event: Event) => void;
}

export function Dashboard({ onEventClick }: DashboardProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard'],
    queryFn: () => apiClient.getDashboard(),
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  usePolling({
    queryKey: ['dashboard'],
    interval: 30000,
    enabled: true,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-destructive bg-destructive/10 p-4">
        <p className="text-sm text-destructive">Failed to load dashboard data. Please try again.</p>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  const stats = [
    {
      title: 'Total Articles',
      value: data.stats.total_articles.toLocaleString(),
      icon: Newspaper,
      change: `+${data.stats.articles_last_24h} today`,
    },
    {
      title: 'News Events',
      value: data.stats.total_events.toLocaleString(),
      icon: FileText,
      change: `+${data.stats.events_last_24h} today`,
    },
    {
      title: 'Trading Ideas',
      value: data.stats.total_ideas.toLocaleString(),
      icon: TrendingUp,
      change: 'Generated',
    },
    {
      title: 'Active Feeds',
      value: data.stats.active_feeds.toString(),
      icon: Activity,
      change: 'Live monitoring',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <Card key={stat.title}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">{stat.title}</CardTitle>
                <Icon className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stat.value}</div>
                <p className="text-xs text-muted-foreground">{stat.change}</p>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Recent Events */}
      <div>
        <h2 className="text-2xl font-bold mb-4">Recent Events</h2>
        {data.recent_events && data.recent_events.length > 0 ? (
          <div className="grid gap-4">
            {data.recent_events.map((event) => (
              <EventCard key={event.id} event={event} onViewDetails={onEventClick} />
            ))}
          </div>
        ) : (
          <Card>
            <CardContent className="py-8 text-center text-muted-foreground">
              No recent events available
            </CardContent>
          </Card>
        )}
      </div>

      {/* Recent Trading Ideas */}
      <div>
        <h2 className="text-2xl font-bold mb-4">Recent Trading Ideas</h2>
        {data.recent_ideas && data.recent_ideas.length > 0 ? (
          <div className="grid gap-4">
            {data.recent_ideas.map((idea) => (
              <TradingIdeaCard key={idea.id} idea={idea} showEvent={true} />
            ))}
          </div>
        ) : (
          <Card>
            <CardContent className="py-8 text-center text-muted-foreground">
              No trading ideas available yet. Ideas will be generated for top-ranked events.
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
