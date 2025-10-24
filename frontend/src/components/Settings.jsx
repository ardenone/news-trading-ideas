import React from 'react'
import { Settings as SettingsIcon } from 'lucide-react'

const Settings = () => {
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
        Settings
      </h2>

      <div className="card">
        <div className="flex items-center space-x-3 mb-6">
          <SettingsIcon className="h-6 w-6 text-gray-600 dark:text-gray-400" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Application Information
          </h3>
        </div>

        <div className="space-y-4">
          <div>
            <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">Version</h4>
            <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">1.0.0</p>
          </div>

          <div>
            <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">Description</h4>
            <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
              AI-powered news clustering and trading ideas generation platform
            </p>
          </div>

          <div>
            <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">Features</h4>
            <ul className="mt-2 space-y-1 text-sm text-gray-600 dark:text-gray-400">
              <li>• Automatic RSS news ingestion</li>
              <li>• AI-powered news clustering using OpenAI embeddings</li>
              <li>• Trading ideas generation with GPT-4</li>
              <li>• Real-time health monitoring</li>
              <li>• Dark mode support</li>
            </ul>
          </div>

          <div>
            <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">Technology Stack</h4>
            <div className="mt-2 flex flex-wrap gap-2">
              {['React', 'FastAPI', 'OpenAI', 'SQLite', 'Docker'].map((tech) => (
                <span
                  key={tech}
                  className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200"
                >
                  {tech}
                </span>
              ))}
            </div>
          </div>

          <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Built with Claude Flow orchestration • MVP v1.0
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Settings
