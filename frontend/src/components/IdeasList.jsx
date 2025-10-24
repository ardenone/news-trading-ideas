import React, { useState } from 'react'
import { formatDistanceToNow } from 'date-fns'
import { TrendingUp, TrendingDown, Minus, Lightbulb } from 'lucide-react'
import { generateIdeas } from '../services/api'

const IdeasList = ({ ideas, isLoading, refetch }) => {
  const [generating, setGenerating] = useState(false)

  const handleGenerate = async () => {
    setGenerating(true)
    try {
      await generateIdeas({ clusterIds: null, force: false })
      setTimeout(() => {
        refetch()
        setGenerating(false)
      }, 5000)
    } catch (error) {
      console.error('Error generating ideas:', error)
      setGenerating(false)
    }
  }

  const getDirectionIcon = (direction) => {
    switch (direction) {
      case 'long': return <TrendingUp className="h-5 w-5 text-green-500" />
      case 'short': return <TrendingDown className="h-5 w-5 text-red-500" />
      case 'neutral': return <Minus className="h-5 w-5 text-gray-500" />
      default: return null
    }
  }

  const getDirectionBadge = (direction) => {
    const classes = {
      long: 'badge-long',
      short: 'badge-short',
      neutral: 'badge-neutral'
    }
    return classes[direction] || 'badge-neutral'
  }

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="spinner"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
          Trading Ideas
        </h2>
        <button
          onClick={handleGenerate}
          disabled={generating}
          className="btn btn-primary disabled:opacity-50"
        >
          {generating ? 'Generating...' : 'Generate Ideas'}
        </button>
      </div>

      {/* Ideas */}
      {ideas.length === 0 ? (
        <div className="text-center py-12">
          <Lightbulb className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">No trading ideas</h3>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Generate trading ideas from news clusters.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {ideas.map((idea) => (
            <div key={idea.id} className="card">
              <div className="flex items-start space-x-4">
                <div className="flex-shrink-0">
                  {getDirectionIcon(idea.direction)}
                </div>

                <div className="flex-1 min-w-0">
                  {/* Header */}
                  <div className="flex items-center justify-between mb-2">
                    <span className={`badge ${getDirectionBadge(idea.direction)}`}>
                      {idea.direction.toUpperCase()}
                    </span>
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      Confidence: {(idea.confidence * 100).toFixed(0)}%
                    </span>
                  </div>

                  {/* Idea */}
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                    {idea.idea}
                  </h3>

                  {/* Rationale */}
                  <p className="text-sm text-gray-600 dark:text-gray-300 mb-3">
                    {idea.rationale}
                  </p>

                  {/* Instruments */}
                  {idea.instruments && idea.instruments.length > 0 && (
                    <div className="flex flex-wrap gap-2 mb-3">
                      {idea.instruments.map((instrument, idx) => (
                        <span
                          key={idx}
                          className="inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200"
                        >
                          {instrument}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Footer */}
                  <div className="flex justify-between items-center text-xs text-gray-500 dark:text-gray-400 pt-3 border-t border-gray-200 dark:border-gray-700">
                    <span>
                      {idea.time_horizon && `${idea.time_horizon} term`}
                    </span>
                    <span>
                      {formatDistanceToNow(new Date(idea.created_at), { addSuffix: true })}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default IdeasList
