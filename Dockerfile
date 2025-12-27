# Use Python 3.12 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy uv lock files and pyproject.toml
COPY pyproject.toml uv.lock ./

# Install uv
RUN pip install uv

# Install dependencies
RUN uv sync --frozen

# Copy application code
COPY . .

# Expose port
EXPOSE 8080

# Run the application
CMD ["uv", "run", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8080"]
