# Generic API Server

A template for building stable APIs with ZeroMQ background workers and thread executors. This project demonstrates a scalable architecture using FastAPI, ZeroMQ for message queuing, and async processing.

## Features

- FastAPI-based REST API server
- ZeroMQ message queue for background processing
- Thread executor for concurrent operations
- Modular strategy pattern for worker tasks
- Async context managers for resource management
- Graceful shutdown handling

## Prerequisites

- Python 3.8+
- Virtual environment tool (venv)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/milkymap/generic-api-server.git
cd generic-api-server
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

4. Create `.env` file in project root (example):
```plaintext
APP_TITLE="Generic API Server"
APP_DESCRIPTION="FastAPI server with ZeroMQ workers"
APP_VERSION="1.0.0"
APP_HOST="0.0.0.0"
APP_PORT=8000
APP_WORKERS=1
```

## Project Structure

```
├── src/
│   ├── api/                 # API related modules
│   │   ├── app.py          # FastAPI application
│   │   ├── manager.py      # Resource manager
│   │   └── routers/        # API endpoints
│   ├── backend/            # Worker implementation
│   │   ├── message_queue.py
│   │   └── strategy.py
│   ├── settings/           # Configuration
│   └── main.py            # Entry point
├── requirements.txt
└── README.md
```

## Usage

1. Launch the server:
```bash
python -m src.main launch-server
```

2. Implement custom worker strategies:
```python
from src.backend import Strategy

class CustomStrategy(Strategy):
    def __init__(self, *args, **kwargs):
        super().__init__()
        # Initialize strategy

    def consume(self, data: bytes) -> Any:
        # Implement processing logic
        return result
```

3. Access the API:
- API documentation: http://localhost:8000/docs
- Health check: http://localhost:8000/liveness

## Architecture

- FastAPI handles HTTP requests
- ZeroMQ broker manages worker pool
- Each worker runs in separate process
- Thread executor manages async tasks
- Strategy pattern for extensible processing

## Configuration

Key settings in `src/settings/`:
- `app.py`: Server configuration
- `manager.py`: Resource management settings

## Development

1. Add new endpoints in `src/api/routers/`
2. Implement strategies in `src/backend/`
3. Configure settings in `src/settings/`

## License

MIT License