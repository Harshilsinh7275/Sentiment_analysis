#!/bin/bash

# Install dependencies
pip install -r requirements.txt

# Run FastAPI using uvicorn
uvicorn backend.app:app --host 0.0.0.0 --port 8000
