FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8005

# Run application
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8005", "--workers", "4"]
