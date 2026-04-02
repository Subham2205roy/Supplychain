web: python -m alembic upgrade head && gunicorn -k uvicorn.workers.UvicornWorker backend.app:app --bind 0.0.0.0:$PORT
