FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Install bash for debugging and interactive use
RUN apt-get update && apt-get install -y bash

COPY . .

# Default to STDIO, can be overridden by MCP_MODE env var
ENV MCP_MODE=stdio

# Entrypoint allows override for stdio or http
ENTRYPOINT ["python", "server.py"] 