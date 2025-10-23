import { useEffect, useRef } from 'react';
import { useQueryClient } from '@tanstack/react-query';

interface UsePollingOptions {
  interval?: number;
  enabled?: boolean;
  queryKey: string[];
}

export function usePolling({ interval = 30000, enabled = true, queryKey }: UsePollingOptions) {
  const queryClient = useQueryClient();
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!enabled) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      return;
    }

    intervalRef.current = setInterval(() => {
      queryClient.invalidateQueries({ queryKey });
    }, interval);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [enabled, interval, queryClient, queryKey]);
}
