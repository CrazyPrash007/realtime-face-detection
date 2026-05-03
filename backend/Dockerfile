FROM python:3.11-slim

# Set non-interactive environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Create a non-root user (Audit fix — principle of least privilege)
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

WORKDIR /app

# Install OS-level dependencies needed by mediapipe
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgl1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies first (better layer caching)
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Switch to non-root user
USER appuser

EXPOSE 8000

# Use uvicorn with module path matching the package layout
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
