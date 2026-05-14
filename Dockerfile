FROM python:3.11-slim

# Install system dependencies required for OCR and image processing
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Install the spaCy model
RUN python -m spacy download en_core_web_sm

# Copy the rest of the application
COPY . .

# Expose the port the app runs on
EXPOSE 8080

# Command to run the Flask application using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--timeout", "120", "web_app:app"]
