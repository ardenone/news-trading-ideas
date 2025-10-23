import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { EventCard } from '../../src/frontend/src/components/EventCard';
import type { Event } from '../../src/frontend/src/types';

describe('EventCard', () => {
  const mockEvent: Event = {
    id: 1,
    name: 'Federal Reserve Rate Decision',
    description: 'FOMC announces interest rate policy',
    article_count: 45,
    source_count: 12,
    earliest_at: '2025-10-22T10:00:00Z',
    latest_at: '2025-10-22T14:00:00Z',
    rank_score: 125.8,
    has_trading_idea: true,
    created_at: '2025-10-22T10:00:00Z',
    updated_at: '2025-10-22T14:00:00Z',
  };

  it('renders event information correctly', () => {
    const onViewDetails = vi.fn();
    render(<EventCard event={mockEvent} onViewDetails={onViewDetails} />);

    expect(screen.getByText('Federal Reserve Rate Decision')).toBeInTheDocument();
    expect(screen.getByText(/12 sources/)).toBeInTheDocument();
    expect(screen.getByText(/45 articles/)).toBeInTheDocument();
  });

  it('shows trading idea button when idea exists', () => {
    const onViewDetails = vi.fn();
    render(<EventCard event={mockEvent} onViewDetails={onViewDetails} />);

    expect(screen.getByText('View Idea')).toBeInTheDocument();
    expect(screen.getByText('Trading thesis generated')).toBeInTheDocument();
  });

  it('calls onViewDetails when clicked', () => {
    const onViewDetails = vi.fn();
    render(<EventCard event={mockEvent} onViewDetails={onViewDetails} />);

    fireEvent.click(screen.getByText('Federal Reserve Rate Decision'));
    expect(onViewDetails).toHaveBeenCalledWith(mockEvent);
  });

  it('shows priority icon based on source count', () => {
    const onViewDetails = vi.fn();
    const { container } = render(<EventCard event={mockEvent} onViewDetails={onViewDetails} />);

    // High priority event (12 sources) should show fire emoji
    expect(container.textContent).toContain('🔥');
  });

  it('shows "No thesis available" when no trading idea exists', () => {
    const eventWithoutIdea = { ...mockEvent, has_trading_idea: false };
    const onViewDetails = vi.fn();
    render(<EventCard event={eventWithoutIdea} onViewDetails={onViewDetails} />);

    expect(screen.getByText('No thesis available')).toBeInTheDocument();
  });
});
