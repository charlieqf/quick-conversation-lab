# Voice Model Lab - Backend

Python + FastAPI backend for voice model testing platform.

## Setup

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --port 8000
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

## API Endpoints

- `GET /api/models` - List available models
- `GET /api/models/{id}` - Get model capabilities
- `WS /ws/{model_id}` - WebSocket for voice session
