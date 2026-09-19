# Production Dockerfile for Google ADK Agent Service
FROM python:3.11-slim

WORKDIR /app

# Prevent Python from writing pyc files to disc & enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application codebase
COPY . .

# Expose HTTP port for Cloud Run
EXPOSE 8080

# Run the agent server using Uvicorn or ADK runner
CMD ["python3", "-m", "phase_1_foundations.customer_support_agent"]
