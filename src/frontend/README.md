# News Trading Ideas - Frontend

Modern React frontend for the News Trading Ideas MVP platform.

## Features

- **Dashboard**: Real-time overview of news events and trading ideas
- **News Explorer**: Browse and search clustered news events
- **Trading Ideas**: View AI-generated trading strategies
- **Settings**: Manage RSS feeds and configuration
- **Real-time Updates**: Automatic polling for live data
- **Responsive Design**: Mobile-first, works on all devices

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Styling
- **TanStack Query** - API state management
- **Axios** - HTTP client
- **Lucide React** - Icons

## Getting Started

### Prerequisites

- Node.js 18+ and npm/yarn
- Backend API running on port 8000 (or configured via VITE_API_URL)

### Installation

```bash
# Install dependencies
npm install

# Copy environment template
cp .env.example .env

# Start development server
npm run dev
```

The app will be available at `http://localhost:3000`

### Environment Variables

Create a `.env` file:

```env
VITE_API_URL=http://localhost:8000
VITE_POLLING_INTERVAL=30000
VITE_DEBUG=false
```

## Development

```bash
# Start dev server with hot reload
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run tests
npm run test

# Run tests with UI
npm run test:ui

# Generate coverage report
npm run test:coverage

# Lint code
npm run lint

# Format code
npm run format
```

## Project Structure

```
src/
├── api/              # API client and endpoints
├── components/       # React components
│   ├── ui/          # Reusable UI components
│   ├── Dashboard.tsx
│   ├── NewsExplorer.tsx
│   ├── TradingIdeas.tsx
│   └── Settings.tsx
├── hooks/           # Custom React hooks
├── lib/             # Utility functions
├── types/           # TypeScript types
├── App.tsx          # Main app component
└── main.tsx         # Entry point
```

## Components

### Dashboard
- Overview statistics
- Recent news events
- Recent trading ideas
- Real-time updates

### News Explorer
- Searchable event list
- Filters (time range, sort, ideas only)
- Event cards with metadata
- Click to view details

### Trading Ideas
- AI-generated strategies
- Confidence scores
- Instrument tags
- Filtering by confidence

### Settings
- RSS feed management
- Add/remove feeds
- Feed status monitoring
- Manual refresh

## API Integration

The app connects to the FastAPI backend via the API client:

```typescript
// Example usage
import { apiClient } from '@/api/client';

const data = await apiClient.getDashboard();
const events = await apiClient.getEvents({ sortBy: 'rank' });
```

## Testing

Tests use Vitest and React Testing Library:

```bash
# Run all tests
npm run test

# Watch mode
npm run test:watch

# Coverage
npm run test:coverage
```

## Building for Production

```bash
# Build optimized bundle
npm run build

# Output goes to dist/
# Deploy dist/ to any static hosting
```

## Performance

- Code splitting by route
- Lazy loading components
- Optimized API caching with TanStack Query
- Real-time updates via polling (30s interval)
- Minimal bundle size (~150KB gzipped)

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

## Contributing

1. Follow TypeScript best practices
2. Write tests for new features
3. Use conventional commits
4. Keep components small and focused

## License

MIT
