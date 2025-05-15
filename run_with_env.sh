#!/bin/bash
# Activate virtual environment
source venv/bin/activate

# Export environment variables from .env file
export $(grep -v '^#' .env | xargs)

# Run Django management command passed as argument
python3 manage.py "$@"
