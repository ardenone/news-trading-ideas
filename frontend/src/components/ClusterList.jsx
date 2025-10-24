import React, { useState } from 'react'
import { formatDistanceToNow } from 'date-fns'
import { Layers, TrendingUp } from 'lucide-react'
import { generateClusters } from '../services/api'

const ClusterList = ({ clusters, isLoading, refetch }) => {
  const [generating, setGenerating] = useState(false)

  const handleGenerate = async () => {
    setGenerating(true)
    try {
      await generateClusters({ minArticles: 10, force: false })
      setTimeout(() => {
        refetch()
        setGenerating(false)
      }, 3000)
    } catch (error) {
      console.error('Error generating clusters:', error)
      setGenerating(false)
    }
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
          News Clusters
        </h2>
        <button
          onClick={handleGenerate}
          disabled={generating}
          className="btn btn-primary disabled:opacity-50"
        >
          {generating ? 'Generating...' : 'Generate Clusters'}
        </button>
      </div>

      {/* Clusters */}
      {clusters.length === 0 ? (
        <div className="text-center py-12">
          <Layers className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">No clusters</h3>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Generate clusters from news articles to get started.
          </p>
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {clusters.map((cluster) => (
            <div key={cluster.id} className="card">
              <div className="flex items-start justify-between">
                <div className="flex items-center">
                  <Layers className="h-5 w-5 text-blue-500 mr-2" />
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    {cluster.article_count} articles
                  </span>
                </div>
                <span className="badge badge-neutral">
                  {(cluster.confidence_score * 100).toFixed(0)}% conf.
                </span>
              </div>

              <h3 className="mt-4 text-lg font-semibold text-gray-900 dark:text-white">
                {cluster.theme}
              </h3>

              {cluster.summary && (
                <p className="mt-2 text-sm text-gray-600 dark:text-gray-300 line-clamp-3">
                  {cluster.summary}
                </p>
              )}

              <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                <div className="flex justify-between items-center text-xs text-gray-500 dark:text-gray-400">
                  <span>
                    {formatDistanceToNow(new Date(cluster.created_at), { addSuffix: true })}
                  </span>
                  {cluster.articles && cluster.articles.length > 0 && (
                    <a
                      href={`#cluster-${cluster.id}`}
                      className="text-blue-600 hover:text-blue-500 dark:text-blue-400 font-medium"
                    >
                      View articles →
                    </a>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default ClusterList
