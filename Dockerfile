FROM python:3.11

# Set the working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Flask and other dependencies if they're not in requirements.txt
RUN pip install --no-cache-dir flask

# Copy application code
COPY bot.py .
COPY *.json ./

# Copy and set proper permissions for sensitive files
COPY .env .env
COPY google-key.json google-key.json
RUN chmod 600 .env google-key.json

# Expose port for Flask
EXPOSE 8080

# Set the environment variable for Cloud Run
ENV PORT=8080

# Create directory for any data that needs to be persisted
RUN mkdir -p /app/data
VOLUME ["/app/data"]

# Run the bot
CMD ["python", "bot.py"]
