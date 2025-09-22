# CityLife Nexus

A smart navigation system that synchronizes traffic signals, predicts light states, and suggests pollution-aware routes.

## Features

- 🚦 **Green Corridor Synchronization** - Coordinate traffic signals for smooth travel
- 🌱 **Pollution-Aware Routing** - Routes that minimize air pollution exposure
- 📱 **Driver Alert System** - Voice alerts and signal predictions
- 🚨 **Emergency Broadcast** - Real-time incident alerts and rerouting
- 📊 **Impact Dashboard** - Track environmental and time savings
- 🎮 **Gamification** - Eco-scoring and achievements
- 🔋 **EV Support** - Battery-aware routing with charging stations
- 🌤️ **Weather Integration** - Weather-aware route adjustments
- 🚌 **Multi-modal** - Public transportation integration
- 📱 **PWA** - Offline-first mobile app

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.9+ (for local development)

### Using Docker (Recommended)

1. Clone the repository:
```bash
git clone <repository-url>
cd citylife-nexus
```

2. Start all services:
```bash
docker-compose up -d
```

3. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Local Development Setup

1. Backend Setup:
```bash
cd backend
pip install -r requirements.txt
```

2. Frontend Setup:
```bash
cd frontend
npm install
```

3. Start Development Servers:

Backend:
```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Frontend:
```bash
cd frontend
npm start
```

## Project Structure

```
citylife-nexus/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Core configuration and utilities
│   │   ├── models/         # Database models
│   │   ├── schemas/        # Pydantic schemas
│   │   └── services/       # Business logic services
│   ├── tests/              # Unit and integration tests
│   └── alembic/            # Database migrations
├── frontend/               # React frontend
│   ├── public/             # Static assets
│   └── src/                # Source code
│       ├── components/     # React components
│       ├── services/       # API service clients
│       └── utils/          # Utility functions
├── docker-compose.yml      # Docker configuration
└── README.md              # This file
```

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Development Guidelines

### Backend
- Follow REST API best practices
- Use Pydantic for data validation
- Implement proper error handling
- Write unit tests for new features

### Frontend
- Use React hooks for state management
- Follow component-based architecture
- Implement responsive design
- Use TypeScript for type safety

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License.