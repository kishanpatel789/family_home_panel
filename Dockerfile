FROM python:3.12

WORKDIR /app

# Copy the project files into the container
COPY application/ ./application
COPY wsgi.py ./wsgi.py
COPY requirements.txt ./requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 5000 for Flask
EXPOSE 5000

# Run the Flask app
CMD ["python", "wsgi.py"]
