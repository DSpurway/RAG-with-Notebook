# Dockerfile for IBM Docs Scraper Service
# Deploys to IBM Cloud Code Engine
# Uses pre-built Selenium image with Chrome already installed

FROM selenium/standalone-chrome:latest

# Switch to root to install Python and dependencies
USER root

# Install Python and pip
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements-windows.txt requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the scraper service
COPY windows_scraper_service.py app.py

# Expose port
EXPOSE 8080

# Set environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Run the service
CMD ["python3", "app.py"]