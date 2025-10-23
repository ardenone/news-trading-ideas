# News Trading Ideas MVP

AI-powered news clustering and trading ideas generation platform.

## Overview

This platform uses advanced AI to:
- Cluster related news articles using semantic similarity
- Generate actionable trading ideas based on news analysis
- Provide real-time insights for financial decision-making

## Features

- **News Clustering**: Automatically groups related news articles using OpenAI embeddings
- **Trading Ideas**: Generates trading recommendations based on clustered news
- **Real-time Updates**: Fetches latest news from multiple sources
- **RESTful API**: Clean API for integration with other systems
- **Modern UI**: React-based frontend for easy interaction

## Quick Start

### Using Docker (Recommended)

```bash
# Clone repository
git clone https://github.com/ardenone/news-trading-ideas.git
cd news-trading-ideas

# Configure environment
cp .env.example .env
# Edit .env and add your API keys

# Build and run
docker-compose up -d

# Access application
open http://localhost:8000
```

### Local Development

See [DEVELOPMENT.md](docs/DEVELOPMENT.md) for detailed setup instructions.

## Architecture

- **Backend**: FastAPI (Python 3.11)
- **Frontend**: React + Vite
- **Database**: SQLite (PostgreSQL ready)
- **AI**: OpenAI GPT-4 + Embeddings
- **Deployment**: Docker + GitHub Actions

## Documentation

- [Docker Setup](docs/DOCKER.md) - Container setup and usage
- [Deployment Guide](docs/DEPLOYMENT.md) - Production deployment
- [Development Guide](docs/DEVELOPMENT.md) - Local development setup
- [API Documentation](http://localhost:8000/docs) - OpenAPI/Swagger docs

## API Endpoints

- `GET /` - Frontend application
- `GET /health` - Health check
- `POST /api/cluster` - Cluster news articles
- `POST /api/trading-ideas` - Generate trading ideas
- `GET /docs` - API documentation

## Environment Variables

Required variables:

```bash
OPENAI_API_KEY=your_openai_api_key
NEWS_API_KEY=your_news_api_key
```

See [.env.example](.env.example) for all available options.

## Testing

```bash
# Run backend tests
pytest

# Run with coverage
pytest --cov=backend --cov-report=html

# Run in Docker
docker-compose exec app pytest
```

## CI/CD

GitHub Actions workflow automatically:
- Builds Docker image on push to main
- Runs tests and security scans
- Pushes to GitHub Container Registry
- Deploys to production (if configured)

See [.github/workflows/docker-build-test.yml](.github/workflows/docker-build-test.yml)

## Deployment

### Quick Deploy Options

- **Docker Compose**: `docker-compose up -d`
- **Google Cloud Run**: See [DEPLOYMENT.md](docs/DEPLOYMENT.md#google-cloud-run)
- **AWS EC2**: See [DEPLOYMENT.md](docs/DEPLOYMENT.md#aws-ec2)
- **Azure Container Instances**: See [DEPLOYMENT.md](docs/DEPLOYMENT.md#azure-container-instances)
- **Kubernetes**: See [DEPLOYMENT.md](docs/DEPLOYMENT.md#kubernetes-production-scale)

## Tech Stack

- **FastAPI** - High-performance Python web framework
- **React** - Modern frontend library
- **OpenAI GPT-4** - Advanced language models
- **Sentence Transformers** - Semantic similarity
- **SQLite/PostgreSQL** - Database
- **Docker** - Containerization
- **GitHub Actions** - CI/CD

## Project Structure

```
news-trading-ideas/
├── backend/           # FastAPI backend
├── frontend/          # React frontend
├── docs/              # Documentation
├── .github/workflows/ # CI/CD pipelines
├── Dockerfile         # Multi-stage build
├── docker-compose.yml # Local development
└── README.md          # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Security

- Never commit API keys or secrets
- Use environment variables for configuration
- Keep dependencies updated
- Run security scans regularly

## Performance

- Single container deployment
- Multi-stage Docker build for optimized image size
- Efficient API caching
- Async processing where applicable

## Support

- **Issues**: [GitHub Issues](https://github.com/ardenone/news-trading-ideas/issues)
- **Documentation**: [/docs](/docs)
- **API Docs**: http://localhost:8000/docs

## License

MIT License - see LICENSE file for details

## Acknowledgments

- OpenAI for GPT-4 and embeddings
- FastAPI framework
- React community
- News API providers

---

Built with ❤️ for better trading decisions
