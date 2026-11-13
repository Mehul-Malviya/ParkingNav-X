# Backend image. Works on Hugging Face Spaces (Docker SDK, port 7860) and any other Docker host.
FROM python:3.11-slim

# Spaces runs the container as uid 1000; give it a home and a writable app dir.
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user PATH=/home/user/.local/bin:$PATH \
    PARKINGNAV_DB_PATH=/tmp/digital_twin.db \
    PORT=7860

WORKDIR /home/user/app

COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=user . .
RUN mkdir -p experiments/results experiments/runs experiments/models

EXPOSE 7860

# The DB is rebuilt from migrations + configs/campus/vitap.yaml on startup, so no persistent disk is needed.
CMD ["sh", "-c", "uvicorn digital_twin.api.app:app --host 0.0.0.0 --port ${PORT}"]
