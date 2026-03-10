# Use official Python runtime as base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set Python to unbuffered mode for better logging
ENV PYTHONUNBUFFERED=1

# Copy the entire project
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r backend/requirements.txt

# Change to backend directory
WORKDIR /app/backend

# Expose port (Render will override with PORT env var)
EXPOSE 8000

# Run the application
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
