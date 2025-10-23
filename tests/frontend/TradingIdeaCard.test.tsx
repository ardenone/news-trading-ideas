import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { TradingIdeaCard } from '../../src/frontend/src/components/TradingIdeaCard';
import type { TradingIdea } from '../../src/frontend/src/types';

describe('TradingIdeaCard', () => {
  const mockIdea: TradingIdea = {
    id: 1,
    event_id: 123,
    idea_text: 'Consider long USD positions against EUR and JPY',
    reasoning: 'Rate decision signals continued hawkish stance',
    instruments: ['EUR/USD', 'USD/JPY', 'US10Y'],
    confidence: 'high',
    timeframe: '1-3 days',
    created_at: '2025-10-22T14:30:00Z',
  };

  it('renders trading idea information correctly', () => {
    render(<TradingIdeaCard idea={mockIdea} showEvent={false} />);

    expect(screen.getByText('Consider long USD positions against EUR and JPY')).toBeInTheDocument();
    expect(screen.getByText('Rate decision signals continued hawkish stance')).toBeInTheDocument();
    expect(screen.getByText('1-3 days')).toBeInTheDocument();
  });

  it('displays confidence level with correct styling', () => {
    render(<TradingIdeaCard idea={mockIdea} showEvent={false} />);

    const confidenceBadge = screen.getByText('HIGH');
    expect(confidenceBadge).toBeInTheDocument();
    expect(confidenceBadge).toHaveClass('text-green-600');
  });

  it('renders instrument badges', () => {
    render(<TradingIdeaCard idea={mockIdea} showEvent={false} />);

    expect(screen.getByText('EUR/USD')).toBeInTheDocument();
    expect(screen.getByText('USD/JPY')).toBeInTheDocument();
    expect(screen.getByText('US10Y')).toBeInTheDocument();
  });

  it('shows event name when showEvent is true', () => {
    const ideaWithEvent = {
      ...mockIdea,
      event: {
        id: 123,
        name: 'Federal Reserve Rate Decision',
        description: 'Test',
        article_count: 45,
        source_count: 12,
        earliest_at: '2025-10-22T10:00:00Z',
        latest_at: '2025-10-22T14:00:00Z',
        rank_score: 125.8,
        has_trading_idea: true,
        created_at: '2025-10-22T10:00:00Z',
        updated_at: '2025-10-22T14:00:00Z',
      },
    };

    render(<TradingIdeaCard idea={ideaWithEvent} showEvent={true} />);
    expect(screen.getByText('Federal Reserve Rate Decision')).toBeInTheDocument();
  });
});
