# AI Mastering Studio

A professional AI-powered audio mastering application built with FastAPI, React, and Gemini 2.5 Flash.

## Features

- 🎵 **Audio Upload & Analysis**: Automatic genre detection, tempo analysis, and frequency spectrum analysis
- 🤖 **AI-Powered Mastering**: Intelligent mastering suggestions using Gemini 2.5 Flash
- 🎛️ **Professional Controls**: EQ, compression, saturation, stereo processing, and limiting
- 💬 **Natural Language Interface**: Chat with AI to adjust mastering parameters
- 🔊 **A/B Comparison**: Compare original vs mastered versions
- 📊 **Real-time Visualization**: Waveform display and frequency analysis
- 🎨 **Modern UI**: Dark theme with glassmorphism effects

## Tech Stack

### Backend
- **FastAPI** - High-performance async API
- **PostgreSQL** - Database for track metadata
- **Redis** - Caching and task queue
- **Celery** - Background audio processing
- **librosa** - Audio analysis
- **Google GenAI** - Gemini 2.5 Flash integration

### Frontend
- **React 18** - Modern UI framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Utility-first styling
- **Zustand** - State management
- **Vite** - Fast build tool

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

### 1. Clone and Setup
```bash
git clone <repository-url>
cd ai-mastering-studio
```

### 2. Environment Configuration
Configure your Gemini API key in docker-compose.yml:
```
GEMINI_API_KEY=your_gemini_api_key
```

### 3. Start with Docker Compose
```bash
# Build and start all services
docker-compose up --build

# Or run in background
docker-compose up --build -d
```

### 4. Access the Application
- **Frontend**: http://localhost:80
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Services

The application consists of several services:

- **nginx** (Port 80) - Reverse proxy
- **frontend** (Port 3000) - React application
- **backend** (Port 8000) - FastAPI server
- **celery_worker** - Background audio processing
- **db** (Port 5432) - PostgreSQL database
- **redis** (Port 6379) - Redis cache

## Usage

### 1. Upload Audio Track
- Drag and drop or click to upload audio files
- Supported formats: WAV, MP3, FLAC, AIFF, M4A
- Maximum file size: 100MB

### 2. AI Analysis
- Automatic genre detection
- Tempo and key analysis
- Frequency spectrum analysis
- Loudness measurements

### 3. Mastering Controls
- **EQ**: 5-band parametric equalizer
- **Compression**: Threshold, ratio, attack, release
- **Saturation**: Tube, tape, or soft clipping
- **Stereo**: Width adjustment
- **Limiting**: Ceiling and release controls

### 4. AI Chat Interface
Ask the AI to adjust your mastering:
- "Add more bass"
- "Make it brighter"
- "Give it a vintage sound"
- "Increase the punch"
- "Make it wider"

### 5. Download Results
- Download original track
- Download mastered version
- A/B comparison player

## API Endpoints

### Tracks
- `POST /api/tracks/upload` - Upload audio file
- `GET /api/tracks/{id}` - Get track info
- `GET /api/tracks/{id}/analysis` - Get analysis results
- `POST /api/tracks/{id}/master` - Apply mastering
- `GET /api/tracks/{id}/download` - Download original
- `GET /api/tracks/{id}/download/mastered` - Download mastered

### Chat
- `POST /api/chat/mastering` - Send chat message
- `POST /api/chat/suggest` - Get AI suggestions
- `GET /api/chat/examples` - Get example commands

### Tasks
- `GET /api/tasks/{id}` - Get task status
- `DELETE /api/tasks/{id}` - Cancel task

## Development

### Local Development Setup

#### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Start services
uvicorn app.main:app --reload
celery -A app.celery_app worker --loglevel=info
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Environment Variables
```bash
# Backend
DATABASE_URL=postgresql://postgres:postgres123@localhost:5432/aimastering
REDIS_URL=redis://localhost:6379
GEMINI_API_KEY=your_gemini_api_key

# Frontend
VITE_API_URL=http://localhost:8000
```

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   React App     │────│   FastAPI        │────│   PostgreSQL    │
│   (Frontend)    │    │   (Backend)      │    │   (Database)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         │              ┌──────────────────┐              │
         │              │   Redis Cache    │              │
         │              └──────────────────┘              │
         │                        │                        │
         │              ┌──────────────────┐              │
         └──────────────│  Audio Processor │──────────────┘
                        │   (Celery Tasks) │
                        └──────────────────┘
                                 │
                        ┌──────────────────┐
                        │  Gemini 2.5 API  │
                        │  (AI Decisions)   │
                        └──────────────────┘
```

## Troubleshooting

### Common Issues

1. **Audio processing fails**
   - Check if ffmpeg is installed in the container
   - Verify audio file format is supported

2. **Database connection errors**
   - Ensure PostgreSQL is running
   - Check DATABASE_URL configuration

3. **Gemini API errors**
   - Verify API key is correct
   - Check API quota and limits

4. **Frontend build issues**
   - Clear node_modules and reinstall
   - Check Node.js version compatibility

### Logs
```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs celery_worker
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.
