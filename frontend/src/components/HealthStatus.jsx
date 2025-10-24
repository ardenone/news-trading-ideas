import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { getHealth } from '../services/api'
import { Activity } from 'lucide-react'

const HealthStatus = () => {
  const { data: health, isLoading } = useQuery({
    queryKey: ['health'],
    queryFn: getHealth,
    refetchInterval: 30000 // 30 seconds
  })

  if (isLoading) {
    return (
      <div className="flex items-center space-x-2 text-gray-500">
        <Activity className="h-5 w-5 animate-pulse" />
        <span className="text-sm">Checking...</span>
      </div>
    )
  }

  const getStatusColor = () => {
    switch (health?.status) {
      case 'healthy': return 'text-green-600 dark:text-green-400'
      case 'degraded': return 'text-yellow-600 dark:text-yellow-400'
      case 'unhealthy': return 'text-red-600 dark:text-red-400'
      default: return 'text-gray-600'
    }
  }

  return (
    <div className={`flex items-center space-x-2 ${getStatusColor()}`}>
      <Activity className="h-5 w-5" />
      <span className="text-sm font-medium capitalize">{health?.status || 'unknown'}</span>
      {health && (
        <span className="text-xs text-gray-500 dark:text-gray-400">
          (DB: {health.database ? '✓' : '✗'} | AI: {health.openai ? '✓' : '✗'})
        </span>
      )}
    </div>
  )
}

export default HealthStatus
