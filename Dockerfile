# Use Microsoft Playwright official Python image with all browser libraries pre-installed
FROM mcr.microsoft.com/playwright/python:v1.49.0-noble

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Install Python dependencies first (leverages Docker layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Ensure Chromium browser binary is installed and verified
RUN playwright install chromium

# Copy application source code
COPY . .

# Create directory for evidence and SQLite database if not present
RUN mkdir -p sample_data/evidence

# Expose port (Render & Railway inject dynamic $PORT at runtime)
EXPOSE 8000

# Run FastAPI server with Uvicorn bound to 0.0.0.0
CMD ["sh", "-c", "uvicorn app.mock_portal.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
