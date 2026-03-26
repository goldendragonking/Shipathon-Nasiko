FROM python:3.11-slim

WORKDIR /app

# Copy only the source code to the container root
COPY src/ /app
# Also copy knowledge_base.json if it resides in src (it does)

RUN pip install --no-cache-dir \
    "a2a-sdk[http-server]>=0.3.0" \
    google-genai>=1.0.0 \
    pydantic>=2.11.4 \
    click>=8.1.8 \
    uvicorn \
    python-dotenv

ENV PYTHONUNBUFFERED=1

# Expose the port (optional but good practice)
EXPOSE 5000

# Start the agent using the flat structure expected by the template's Dockerfile
CMD ["python", "__main__.py", "--host", "0.0.0.0", "--port", "5000"]