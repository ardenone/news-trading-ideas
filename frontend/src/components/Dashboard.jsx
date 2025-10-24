import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import NewsList from './NewsList'
import ClusterList from './ClusterList'
import IdeasList from './IdeasList'
import Settings from './Settings'
import { getClusters, getIdeas } from '../services/api'

const Dashboard = () => {
  const [activeTab, setActiveTab] = useState('clusters')

  const { data: clustersData, isLoading: clustersLoading, refetch: refetchClusters } = useQuery({
    queryKey: ['clusters'],
    queryFn: () => getClusters({ skip: 0, limit: 100 })
  })

  const { data: ideasData, isLoading: ideasLoading, refetch: refetchIdeas } = useQuery({
    queryKey: ['ideas'],
    queryFn: () => getIdeas({ skip: 0, limit: 100 })
  })

  const tabs = [
    { id: 'clusters', name: 'News Clusters', count: clustersData?.total || 0 },
    { id: 'ideas', name: 'Trading Ideas', count: ideasData?.total || 0 },
    { id: 'news', name: 'All News', count: null },
    { id: 'settings', name: 'Settings', count: null }
  ]

  return (
    <div className="space-y-6">
      {/* Tabs */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`
                ${activeTab === tab.id
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
                }
                whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors
              `}
            >
              {tab.name}
              {tab.count !== null && (
                <span className={`ml-2 py-0.5 px-2 rounded-full text-xs ${
                  activeTab === tab.id
                    ? 'bg-blue-100 text-blue-600 dark:bg-blue-900 dark:text-blue-300'
                    : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
                }`}>
                  {tab.count}
                </span>
              )}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab content */}
      <div className="fade-in">
        {activeTab === 'clusters' && (
          <ClusterList
            clusters={clustersData?.clusters || []}
            isLoading={clustersLoading}
            refetch={refetchClusters}
          />
        )}
        {activeTab === 'ideas' && (
          <IdeasList
            ideas={ideasData?.ideas || []}
            isLoading={ideasLoading}
            refetch={refetchIdeas}
          />
        )}
        {activeTab === 'news' && <NewsList />}
        {activeTab === 'settings' && <Settings />}
      </div>
    </div>
  )
}

export default Dashboard
