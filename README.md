# SafeAir Navigator

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
cd safeair-navigator
```

2. Start all services:
```bash
docker-compose up -d
```

3. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Local Development

#### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Run the backend:
```bash
uvicorn app.main:app --reload
```

#### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start development server:
```bash
npm start
```

## Project Structure

```
safeair-navigator/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Core configuration
│   │   ├── models/         # Database models
│   │   ├── services/       # Business logic
│   │   └── main.py         # FastAPI app
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── services/       # API services
│   │   └── App.tsx
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml      # Docker services
└── README.md
```

## API Documentation

Once the backend is running, visit http://localhost:8000/docs for interactive API documentation.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.