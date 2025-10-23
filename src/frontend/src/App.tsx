import React, { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Dashboard } from './components/Dashboard';
import { NewsExplorer } from './components/NewsExplorer';
import { TradingIdeas } from './components/TradingIdeas';
import { Settings } from './components/Settings';
import type { Event } from './types';
import { LayoutDashboard, Newspaper, TrendingUp, Settings as SettingsIcon } from 'lucide-react';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30000, // 30 seconds
      retry: 1,
    },
  },
});

type View = 'dashboard' | 'explorer' | 'ideas' | 'settings';

function App() {
  const [currentView, setCurrentView] = useState<View>('dashboard');
  const [selectedEvent, setSelectedEvent] = useState<Event | null>(null);

  const handleEventClick = (event: Event) => {
    setSelectedEvent(event);
    // Could navigate to a detail view or modal here
    console.log('Event clicked:', event);
  };

  const navigation = [
    { id: 'dashboard' as View, label: 'Dashboard', icon: LayoutDashboard },
    { id: 'explorer' as View, label: 'News Explorer', icon: Newspaper },
    { id: 'ideas' as View, label: 'Trading Ideas', icon: TrendingUp },
    { id: 'settings' as View, label: 'Settings', icon: SettingsIcon },
  ];

  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-background">
        {/* Header */}
        <header className="border-b bg-card sticky top-0 z-50">
          <div className="container mx-auto px-4 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <TrendingUp className="h-8 w-8 text-primary" />
                <div>
                  <h1 className="text-xl font-bold">News Trading Ideas</h1>
                  <p className="text-xs text-muted-foreground">AI-Powered Market Intelligence</p>
                </div>
              </div>
              <div className="flex items-center gap-1">
                <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse"></div>
                <span className="text-xs text-muted-foreground">Live</span>
              </div>
            </div>
          </div>
        </header>

        {/* Navigation */}
        <nav className="border-b bg-card">
          <div className="container mx-auto px-4">
            <div className="flex gap-1 overflow-x-auto">
              {navigation.map((item) => {
                const Icon = item.icon;
                const isActive = currentView === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => setCurrentView(item.id)}
                    className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                      isActive
                        ? 'border-primary text-primary'
                        : 'border-transparent text-muted-foreground hover:text-foreground hover:border-muted'
                    }`}
                  >
                    <Icon className="h-4 w-4" />
                    {item.label}
                  </button>
                );
              })}
            </div>
          </div>
        </nav>

        {/* Main Content */}
        <main className="container mx-auto px-4 py-8">
          {currentView === 'dashboard' && <Dashboard onEventClick={handleEventClick} />}
          {currentView === 'explorer' && <NewsExplorer onEventClick={handleEventClick} />}
          {currentView === 'ideas' && <TradingIdeas />}
          {currentView === 'settings' && <Settings />}
        </main>

        {/* Footer */}
        <footer className="border-t mt-12 bg-card">
          <div className="container mx-auto px-4 py-6">
            <div className="flex items-center justify-between text-sm text-muted-foreground">
              <p>News Trading Ideas MVP v1.0.0</p>
              <p>Powered by GPT-4 and FastAPI</p>
            </div>
          </div>
        </footer>
      </div>
    </QueryClientProvider>
  );
}

export default App;
