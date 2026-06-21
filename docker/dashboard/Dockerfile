FROM python:3.10-slim

# Flask is the only dependency for the dashboard
RUN pip install --no-cache-dir flask

WORKDIR /app
COPY dashboard/ .

# Port 5000: Flask web server
EXPOSE 5000

CMD ["python", "app.py"]
