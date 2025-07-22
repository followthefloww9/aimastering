# 🚀 Local Development Setup

## Quick Start (5 minutes)

### 1. Clone the Repository
```bash
git clone https://github.com/followthefloww9/aimastering.git
cd aimastering
```

### 2. Environment Setup
```bash
# Copy environment template
cp .env.template .env

# Edit .env with your values (optional - defaults work for local dev)
nano .env
```

### 3. Start All Services
```bash
# Start everything with Docker
docker-compose up -d

# Check all services are running
docker-compose ps
```

### 4. Access the Application
- **Main App**: http://localhost
- **API Docs**: http://localhost:8000/docs

## 🔧 Configuration

### Required for AI Features (Optional)
```bash
# Get a free Gemini API key from Google AI Studio
GEMINI_API_KEY=your_gemini_api_key_here
```

### Default Configuration (Works out of the box)
```bash
DATABASE_URL=postgresql://aimastering:password@db:5432/aimastering_db
REDIS_URL=redis://redis:6379/0
SECRET_KEY=dev-secret-key-change-in-production
```

## 🛠️ Development Commands

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Restart Services
```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart backend
```

### Database Access
```bash
# Connect to PostgreSQL
docker-compose exec db psql -U aimastering -d aimastering_db
```

### Frontend Development
```bash
# Install dependencies locally (optional)
cd frontend
npm install

# Run in development mode (optional)
npm run dev
```

### Backend Development
```bash
# Install dependencies locally (optional)
cd backend
pip install -r requirements.txt

# Run in development mode (optional)
uvicorn app.main:app --reload
```

## 🎵 Features Ready to Use

### ✅ Working Features
- **Upload audio files** (WAV, MP3, FLAC, AIFF, M4A)
- **Real-time analysis** (tempo, key, loudness, spectral features)
- **9 mastering tabs** with professional controls
- **AI chat integration** (if Gemini API key provided)
- **Real-time preview** with Web Audio API
- **Download mastered tracks**

### 🎛️ Mastering Controls
1. **EQ** - 10-band professional equalizer
2. **Compression** - Dynamic range compression
3. **Saturation** - Harmonic enhancement
4. **Stereo** - Stereo imaging and width
5. **Limiting** - Peak limiting
6. **Masking** - Frequency masking correction
7. **Dynamics** - Dynamic range optimization
8. **LUFS** - Loudness standards compliance
9. **Exciter** - Harmonic exciter

### 🤖 AI Chat Examples
- "Make it brighter"
- "Add more bass"
- "Make it louder"
- "Wider stereo image"
- "More punch and dynamics"

## 🐛 Troubleshooting

### Services Not Starting
```bash
# Clean restart
docker-compose down
docker-compose up -d
```

### Port Conflicts
```bash
# Check what's using ports
lsof -i :80
lsof -i :8000
lsof -i :5432
```

### Database Issues
```bash
# Reset database
docker-compose down -v
docker-compose up -d
```

## 📦 Production Deployment

### Environment Variables for Production
```bash
DEBUG=false
ENVIRONMENT=production
SECRET_KEY=your-secure-secret-key
DATABASE_URL=your-production-database-url
GEMINI_API_KEY=your-production-api-key
```

### Docker Production Build
```bash
# Build for production
docker-compose -f docker-compose.prod.yml up -d
```

## 🎯 Next Steps

1. **Get Gemini API Key** for AI features
2. **Customize mastering algorithms** in `backend/app/services/`
3. **Add new audio formats** in `backend/app/core/config.py`
4. **Enhance UI** in `frontend/src/components/`
5. **Add user authentication** 
6. **Deploy to cloud** (AWS, GCP, Azure)

## 📞 Support

- **GitHub Issues**: https://github.com/followthefloww9/aimastering/issues
- **Documentation**: See README.md for detailed info
- **API Docs**: http://localhost:8000/docs when running

Happy mastering! 🎵✨
