import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { formatDistanceToNow } from 'date-fns'
import { Newspaper, RefreshCw } from 'lucide-react'
import { getNews, refreshNews } from '../services/api'

const NewsList = () => {
  const [page, setPage] = useState(1)
  const [refreshing, setRefreshing] = useState(false)
  const pageSize = 50

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['news', page],
    queryFn: () => getNews({ page, pageSize })
  })

  const handleRefresh = async () => {
    setRefreshing(true)
    try {
      await refreshNews()
      setTimeout(() => {
        refetch()
        setRefreshing(false)
      }, 2000)
    } catch (error) {
      console.error('Error refreshing news:', error)
      setRefreshing(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="spinner"></div>
      </div>
    )
  }

  const articles = data?.articles || []
  const total = data?.total || 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            All News Articles
          </h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            {total} articles total
          </p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="btn btn-secondary disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
          {refreshing ? 'Refreshing...' : 'Refresh RSS'}
        </button>
      </div>

      {/* Articles */}
      {articles.length === 0 ? (
        <div className="text-center py-12">
          <Newspaper className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">No articles</h3>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Refresh RSS feeds to fetch news articles.
          </p>
        </div>
      ) : (
        <>
          <div className="space-y-4">
            {articles.map((article) => (
              <div key={article.id} className="card">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <a
                      href={article.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-lg font-semibold text-gray-900 dark:text-white hover:text-blue-600 dark:hover:text-blue-400"
                    >
                      {article.title}
                    </a>
                    {article.content && (
                      <p className="mt-2 text-sm text-gray-600 dark:text-gray-300 line-clamp-2">
                        {article.content}
                      </p>
                    )}
                    <div className="mt-3 flex items-center space-x-4 text-xs text-gray-500 dark:text-gray-400">
                      <span className="font-medium">{article.source}</span>
                      <span>•</span>
                      <span>
                        {formatDistanceToNow(new Date(article.fetched_at), { addSuffix: true })}
                      </span>
                      {article.cluster_id && (
                        <>
                          <span>•</span>
                          <span className="text-blue-600 dark:text-blue-400">
                            In cluster #{article.cluster_id}
                          </span>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Pagination */}
          {total > pageSize && (
            <div className="flex justify-center items-center space-x-4 mt-8">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="btn btn-secondary disabled:opacity-50"
              >
                Previous
              </button>
              <span className="text-sm text-gray-700 dark:text-gray-300">
                Page {page} of {Math.ceil(total / pageSize)}
              </span>
              <button
                onClick={() => setPage(p => p + 1)}
                disabled={page >= Math.ceil(total / pageSize)}
                className="btn btn-secondary disabled:opacity-50"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default NewsList
