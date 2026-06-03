# DOXA MVP

This is the MVP repository for DOXA. Python dependencies and environments are managed using [Poetry](https://python-poetry.org/).

## Setup & Installation

### Prerequisites

Ensure you have Python 3.12+ and Poetry installed.

### Install Dependencies

To set up the virtual environment and install all dependencies (including `langgraph`):
```bash
poetry install
```

This will automatically create a virtual environment in a local `.venv/` directory.

## Usage

### Running Commands

To run any script or command within the virtual environment:
```bash
poetry run python your_script.py
```

### Activating the Virtual Environment Shell

To spawn a shell within the virtual environment:
```bash
poetry shell
```

### Managing Dependencies

To add a new package:
```bash
poetry add <package-name>
```

To add a dev dependency:
```bash
poetry add --group dev <package-name>
```

To remove a package:
```bash
poetry remove <package-name>
```

## Backend

The backend is a FastAPI server powered by [LangGraph](https://langchain-ai.github.io/langgraph/) and lives in `backend/`.

### Environment Variables

Copy the example env file and fill in your OpenAI API key:
```bash
cp .env.example .env
```

Edit `.env` and set your key:
```
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o          # optional, defaults to gpt-4o
```

### Running the Backend

```bash
poetry run uvicorn backend.main:app --reload
```

The API will be available at `http://localhost:8000`.
- Health check: `GET /health`
- Chat: `POST /api/chat` with body `{ "message": "...", "session_id": "..." }`

### API Docs

FastAPI auto-generates interactive docs at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Frontend

The UI lives in `frontend/` (React, TypeScript, Vite). It is separate from the Python backend and has no API integration yet.

### Setup

```bash
cd frontend
npm install
npm run dev
```

Open the URL shown in the terminal (typically `http://localhost:5173`).