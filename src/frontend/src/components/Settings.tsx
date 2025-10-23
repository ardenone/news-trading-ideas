import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card';
import { Button } from './ui/Button';
import { Badge } from './ui/Badge';
import { Loader2, Plus, Trash2, RefreshCw, CheckCircle2, XCircle, Clock } from 'lucide-react';
import { formatDateTime } from '@/lib/utils';

export function Settings() {
  const queryClient = useQueryClient();
  const [showAddFeed, setShowAddFeed] = useState(false);
  const [newFeedUrl, setNewFeedUrl] = useState('');
  const [newFeedName, setNewFeedName] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['feeds'],
    queryFn: () => apiClient.getFeeds(),
  });

  const refreshMutation = useMutation({
    mutationFn: () => apiClient.refreshFeeds(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['feeds'] });
    },
  });

  const addFeedMutation = useMutation({
    mutationFn: () => apiClient.addFeed(newFeedUrl, newFeedName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['feeds'] });
      setNewFeedUrl('');
      setNewFeedName('');
      setShowAddFeed(false);
    },
  });

  const deleteFeedMutation = useMutation({
    mutationFn: (id: number) => apiClient.deleteFeed(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['feeds'] });
    },
  });

  const handleAddFeed = (e: React.FormEvent) => {
    e.preventDefault();
    if (newFeedUrl && newFeedName) {
      addFeedMutation.mutate();
    }
  };

  const getStatusIcon = (feed: any) => {
    if (feed.is_active && feed.error_count === 0) {
      return <CheckCircle2 className="h-5 w-5 text-green-600" />;
    }
    if (feed.error_count > 0) {
      return <XCircle className="h-5 w-5 text-red-600" />;
    }
    return <Clock className="h-5 w-5 text-yellow-600" />;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold mb-2">Settings</h1>
          <p className="text-muted-foreground">Manage RSS feeds and system configuration</p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => refreshMutation.mutate()}
            disabled={refreshMutation.isPending}
          >
            {refreshMutation.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
            ) : (
              <RefreshCw className="h-4 w-4 mr-2" />
            )}
            Refresh All
          </Button>
          <Button onClick={() => setShowAddFeed(!showAddFeed)}>
            <Plus className="h-4 w-4 mr-2" />
            Add Feed
          </Button>
        </div>
      </div>

      {/* Add Feed Form */}
      {showAddFeed && (
        <Card>
          <CardHeader>
            <CardTitle>Add New RSS Feed</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleAddFeed} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Feed Name</label>
                <input
                  type="text"
                  value={newFeedName}
                  onChange={(e) => setNewFeedName(e.target.value)}
                  placeholder="e.g., Reuters Business"
                  className="w-full border rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Feed URL</label>
                <input
                  type="url"
                  value={newFeedUrl}
                  onChange={(e) => setNewFeedUrl(e.target.value)}
                  placeholder="https://example.com/rss"
                  className="w-full border rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
                  required
                />
              </div>
              <div className="flex gap-2">
                <Button type="submit" disabled={addFeedMutation.isPending}>
                  {addFeedMutation.isPending ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin mr-2" />
                      Adding...
                    </>
                  ) : (
                    'Add Feed'
                  )}
                </Button>
                <Button type="button" variant="outline" onClick={() => setShowAddFeed(false)}>
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Feeds List */}
      <Card>
        <CardHeader>
          <CardTitle>RSS Feeds</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center h-32">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
          ) : data?.feeds && data.feeds.length > 0 ? (
            <div className="space-y-4">
              {data.feeds.map((feed) => (
                <div
                  key={feed.id}
                  className="flex items-center justify-between p-4 border rounded-lg hover:bg-accent/50 transition-colors"
                >
                  <div className="flex items-center gap-4 flex-1">
                    {getStatusIcon(feed)}
                    <div className="flex-1">
                      <div className="font-medium">{feed.feed_name}</div>
                      <div className="text-sm text-muted-foreground truncate max-w-md">
                        {feed.feed_url}
                      </div>
                      <div className="flex gap-4 mt-1 text-xs text-muted-foreground">
                        <span>{feed.article_count} articles</span>
                        {feed.last_fetch_at && (
                          <span>Last fetch: {formatDateTime(feed.last_fetch_at)}</span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {feed.is_active ? (
                      <Badge variant="default">Active</Badge>
                    ) : (
                      <Badge variant="secondary">Inactive</Badge>
                    )}
                    {feed.error_count > 0 && (
                      <Badge variant="destructive">{feed.error_count} errors</Badge>
                    )}
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => deleteFeedMutation.mutate(feed.id)}
                      disabled={deleteFeedMutation.isPending}
                    >
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              No RSS feeds configured. Add your first feed to get started.
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
