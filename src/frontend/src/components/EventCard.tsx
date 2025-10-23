import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card';
import { Badge } from './ui/Badge';
import { Button } from './ui/Button';
import type { Event } from '@/types';
import { formatDate, getPriorityIcon, truncateText } from '@/lib/utils';
import { ExternalLink } from 'lucide-react';

interface EventCardProps {
  event: Event;
  onViewDetails: (event: Event) => void;
}

export function EventCard({ event, onViewDetails }: EventCardProps) {
  const priorityIcon = getPriorityIcon(event.source_count);
  const isRecent = new Date(event.latest_at).getTime() > Date.now() - 5 * 60 * 1000; // 5 minutes

  return (
    <Card className="hover:shadow-md transition-shadow cursor-pointer" onClick={() => onViewDetails(event)}>
      <CardHeader>
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-2 flex-1">
            <span className="text-2xl">{priorityIcon}</span>
            <div className="flex-1">
              <CardTitle className="text-lg mb-2">{event.name}</CardTitle>
              <div className="flex flex-wrap gap-2 text-sm text-muted-foreground">
                <span className="font-medium">{event.source_count} sources</span>
                <span>•</span>
                <span>{event.article_count} articles</span>
                <span>•</span>
                <span>{formatDate(event.latest_at)}</span>
                {isRecent && (
                  <>
                    <span>•</span>
                    <Badge variant="secondary" className="text-xs">
                      New
                    </Badge>
                  </>
                )}
              </div>
            </div>
          </div>
          {event.has_trading_idea && (
            <Button size="sm" variant="outline" onClick={() => onViewDetails(event)}>
              <ExternalLink className="h-4 w-4 mr-1" />
              View Idea
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">{truncateText(event.description || '', 200)}</p>
        <div className="mt-3">
          {event.has_trading_idea ? (
            <Badge variant="default" className="bg-green-600">
              Trading thesis generated
            </Badge>
          ) : (
            <Badge variant="outline">No thesis available</Badge>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
