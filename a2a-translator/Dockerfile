FROM python:3.10-slim

WORKDIR /app

# Copy the project files
COPY . .

# Install ONLY our required support agent dependencies
RUN pip install --no-cache-dir \
    "a2a-sdk[http-server]>=0.3.0" \
    openai>=1.57.0 \
    pydantic>=2.11.4 \
    click>=8.1.8 \
    uvicorn \
    python-dotenv
    
# The A2A protocol expects port 5000
EXPOSE 5000

# Start the agent
CMD ["python", "-m", "src", "--host", "0.0.0.0", "--port", "5000"]