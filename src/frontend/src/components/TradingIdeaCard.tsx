import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card';
import { Badge } from './ui/Badge';
import type { TradingIdea } from '@/types';
import { formatDate, getConfidenceColor } from '@/lib/utils';
import { TrendingUp } from 'lucide-react';

interface TradingIdeaCardProps {
  idea: TradingIdea;
  showEvent?: boolean;
}

export function TradingIdeaCard({ idea, showEvent = true }: TradingIdeaCardProps) {
  return (
    <Card className="border-l-4 border-l-primary">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            {showEvent && idea.event && (
              <div className="text-sm text-muted-foreground mb-2">{idea.event.name}</div>
            )}
            <CardTitle className="text-lg flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-primary" />
              Trading Idea
            </CardTitle>
          </div>
          <Badge className={getConfidenceColor(idea.confidence)}>{idea.confidence.toUpperCase()}</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <h4 className="font-semibold mb-2">Idea</h4>
          <p className="text-sm">{idea.idea_text}</p>
        </div>

        <div>
          <h4 className="font-semibold mb-2">Reasoning</h4>
          <p className="text-sm text-muted-foreground">{idea.reasoning}</p>
        </div>

        {idea.instruments && idea.instruments.length > 0 && (
          <div>
            <h4 className="font-semibold mb-2">Instruments</h4>
            <div className="flex flex-wrap gap-2">
              {idea.instruments.map((instrument, idx) => (
                <Badge key={idx} variant="secondary">
                  {instrument}
                </Badge>
              ))}
            </div>
          </div>
        )}

        <div className="flex items-center justify-between text-sm text-muted-foreground pt-4 border-t">
          <span>Timeframe: {idea.timeframe}</span>
          <span>{formatDate(idea.created_at)}</span>
        </div>
      </CardContent>
    </Card>
  );
}
