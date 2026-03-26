"""Mesmo que `python main.py`: sobe o app com porta automática (não use uvicorn --port 8001)."""
from main import run_dev

if __name__ == "__main__":
    run_dev()
