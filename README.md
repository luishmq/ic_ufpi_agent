# Generative AI Chatbot API for SSP

## Table of Contents
 - [Introduction](#introduction)
 - [Features](#features)
 - [Architecture Overview](#architecture-overview)
 - [Tech Stack](#tech-stack)
 - [Repository Structure](#repository-structure)
 - [Prerequisites](#prerequisites)
 - [Configuration](#configuration)
 - [Installation](#installation)
 - [Running the Service](#running-the-service)
 - [API Endpoints](#api-endpoints)
 - [Troubleshooting](#troubleshooting)

## Introduction
 The Generative AI Chatbot API is designed to assist the Public Security Department (SSP) by integrating with the 190 emergency service. It leverages state-of-the-art Large Language Models (LLMs) and multimodal processing to handle text, audio, images, and geolocation data. Users interact via SMS/WhatsApp through Twilio, and conversation histories are stored in Google BigQuery for auditing and analytics.

## Features
 - Multimodal Input Support:
   - Text messaging
   - Audio message transcription
   - Image analysis via Google Gemini Vision
   - Reverse geocoding of location (latitude/longitude)
 - Real-time Twilio Integration (SMS & WhatsApp)
 - Asynchronous Background Processing for audio
 - Generative AI Agents with support for:
   - Anthropic Claude
   - OpenAI GPT
   - DeepSeek
   - Google Vertex AI (Gemini Vision)
   - Ollama
 - Protocol Detection & Generation for completed sessions
 - Conversation persistence in Google BigQuery
 - Redis-based session management
 - Dockerized deployment for consistency

## Architecture Overview
 1. **API Layer**: Built with FastAPI, exposes HTTP/webhook endpoints.
 2. **Middleware**:
    - CORS support
    - Request timeout handling
    - BigQuery logging of requests/responses
 3. **Business Logic**: Encapsulated in `Agent190` for emergency handling.
 4. **Modular Features**:
    - Audio transcription pipeline
    - Image processing
    - Geocoding
    - Protocol generation
 5. **Data Storage**:
    - Redis for short-term session state
    - Google BigQuery for long-term conversation history
 6. **Messaging**: Twilio SDK for inbound/outbound communication.

## Tech Stack
 - Python 3.11
 - FastAPI & Uvicorn
 - LangChain suite for LLM orchestration
 - Google Cloud Platform:
   - BigQuery
   - Cloud Storage
   - Vision API
   - Geocoding API
 - Twilio (SMS/WhatsApp)
 - Redis for session management
 - Docker & Docker Compose

## Repository Structure
 ```
 .
 ├── app/                     # Main application source
 │   ├── api/                 # FastAPI routers and endpoints
 │   ├── crud/                # Business logic & AI feature implementations
 │   ├── schemas/             # Pydantic models
 │   ├── utils/               # Utility modules & prompts
 │   ├── Dockerfile           # Docker container build config
 │   ├── entrypoint.sh        # Startup script (if used)
 │   ├── main.py              # FastAPI application entrypoint
 │   └── requirements.txt     # Python dependencies
 ├── pyproject.toml           # Project metadata
 ├── uv.lock                  # Dependency lock file
 └── README.md                # This documentation file
 ```

## Prerequisites
 - Python 3.11 or higher
 - Docker (for containerized deployment)
 - Google Cloud SDK & service account JSON with permissions for BigQuery, Cloud Storage, and Vision APIs
 - Redis server (or managed Redis instance)
 - Twilio account with WhatsApp-enabled phone number
 - API keys for:
   - OpenAI
   - Anthropic
   - DeepSeek
   - XAI (LangChain-XAI)
   - Google Maps Geocoding

## Configuration
 Create a `.env` file in the project root with the following environment variables:
 ```bash
 # Google Cloud
 GOOGLE_APPLICATION_CREDENTIALS=/path/to/your-service-account.json
 PROJECT_ID=your-gcp-project-id
 LOCATION=your-gcp-region

 # LangSmith (optional)
 LANGSMITH_ENDPOINT=
 LANGSMITH_PROJECT=
 LANGSMITH_TRACING=true
 LANGSMITH_API_KEY=

 # Twilio
 ACCOUNT_SID=your_twilio_account_sid
 TWILIO_AUTH_TOKEN=your_twilio_auth_token
 TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

 # LLM API Keys
 OPENAI_API_KEY=your_openai_api_key
 ANTHROPIC_API_KEY=your_anthropic_api_key
 DEEPSEEK_API_KEY=your_deepseek_api_key
 XAI_API_KEY=your_xai_api_key

 # Storage & Geocoding
 BUCKET_NAME=audios_ssp
 GOOGLE_MAPS_API_KEY=your_google_maps_api_key

 # Redis (session management)
 REDIS_HOST=localhost
 REDIS_PORT=6379
 REDIS_PASSWORD=your_redis_password
 REDIS_SSL=true
 REDIS_KEY_PREFIX=session_history:
 REDIS_EXPIRY_SECONDS=86400

 # Additional Settings
 USERAUDIO=
 PASSWORD=
 BASE_URL=https://your.api.base.url
 LUPA_API_KEY=
 ```

## Installation
### Local Setup
 ```bash
 # Clone the repository
 git clone https://github.com/your_org/your_repo.git
 cd your_repo/app

 # Create a virtual environment
 python3 -m venv venv
 source venv/bin/activate

 # Install dependencies
 pip install --upgrade pip
 pip install -r requirements.txt
 ```

### Docker Deployment
 ```bash
 # From the project root
 docker build -f app/Dockerfile -t api-chatbot-ssp .

 # Run the container
 docker run -d \
   --env-file .env \
   -p 8080:8080 \
   api-chatbot-ssp
 ```

## Running the Service
### Via Uvicorn (Local)
 ```bash
 cd app
 uvicorn main:app --host 0.0.0.0 --port 8080 --reload
 ```

### Docker
 Service will start automatically via the Docker entrypoint.

## API Endpoints
 - **GET /**  
   Healthcheck endpoint. Returns status `{ "message": "OK" }`.

 - **GET /api/v1/openapi.json**  
   OpenAPI schema (JSON).

 - **Documentation**  
   Interactive Swagger UI: `http://localhost:8080/docs`

 - **POST /api/v1/agent_twilio_190/init_session**  
   Initialize a new conversation session. Returns a unique `session_id`.

 - **POST /api/v1/agent_twilio_190/predict_twilio_190**  
   Webhook for Twilio SMS/WhatsApp. Supports text, audio, images, and location.

## Troubleshooting
 - **Timeout Errors**: Adjust `REQUEST_TIMEOUT_ERROR` in `app/main.py` if processing exceeds default limit.
 - **Redis Connectivity**: Verify Redis credentials and network accessibility.
 - **GCP Permissions**: Ensure your service account has BigQuery and Storage access.
 - **Twilio Webhook**: Confirm your Twilio console webhook URL is correctly configured.

---
*This README was generated to provide a comprehensive guide for setting up, configuring, and running the Generative AI Chatbot API for SSP.*
