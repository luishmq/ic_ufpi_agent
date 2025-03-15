# API ChatBot Gen AI - SSP

## Description

This is an intelligent chatbot API developed for the Public Security Department (SSP), integrated with the 190 emergency service via Twilio. The application uses Large Language Models (LLMs) to process various input modalities, including text, audio, images, and geographic coordinates, providing contextualized responses for emergency situations.

## Technologies Used

- **FastAPI**: Web framework for creating RESTful APIs in Python
- **LangChain**: Framework for developing applications with LLMs
- **AI Models**:
  - Anthropic Claude
  - OpenAI GPT
  - DeepSeek
  - Google Gemini Vision (image processing)
- **Twilio**: Integration for SMS/WhatsApp communication
- **Google Cloud Platform**:
  - BigQuery (conversation history storage)
  - Cloud Storage (audio storage)
  - Geocoding API (coordinates processing)
- **Docker**: Application containerization

## Project Structure

```
/app
├── api/                    # API Endpoints
│   └── v1/                 # API version 1
│       ├── api.py          # Main router
│       └── endpoints/      # Specific endpoints
│           └── agent_190_twilio.py  # Agent 190 endpoint for Twilio
├── crud/                   # Business logic
│   ├── adapters/           # Adapters for different LLMs
│   │   ├── adapter.py      # Base adapter class
│   │   └── factory.py      # Factory for adapter creation
│   ├── agents/             # AI agent implementations
│   │   └── agent190_modeling.py  # Agent 190 logic
│   ├── features/           # Specific functionalities
│   │   ├── audio_transcript.py  # Audio processing
│   │   ├── gemini_vision.py     # Image processing with Gemini
│   │   ├── history_bq.py        # BigQuery history storage
│   │   └── maps.py              # Reverse geocoding
│   ├── managers/           # Service managers
│   │   └── llm_manager.py  # LLM models manager
│   └── tools/              # Tools for agents
│       ├── get_person_data.py  # Tool for obtaining personal data
│       └── tools.py            # General tools
├── schemas/                # Data schemas
│   └── healthcheck.py      # Healthcheck model
├── utils/                  # Utilities
│   ├── prompts.py          # Prompts for models
│   └── result.py           # Response standardization class
├── Dockerfile              # Docker configuration
├── Makefile                # Build and deploy commands
├── entrypoint.sh           # Initialization script
├── main.py                 # Application entry point
└── requirements.txt        # Project dependencies
```

## Main Features

- **Multimodal Processing**:
  - Receiving and processing text messages
  - Transcription and analysis of audio messages
  - Image analysis with Gemini Vision
  - Interpretation of geographic coordinates and address retrieval

- **Twilio Integration**:
  - Bidirectional communication via SMS/WhatsApp
  - Media support (audio, image, location)

- **Robust Architecture**:
  - Strategy pattern for multiple LLM models
  - Factory pattern for adapter creation
  - Middleware for timeout and performance monitoring
  - Conversation history storage in BigQuery

## Installation and Configuration

### Prerequisites

- Python 3.11+
- Docker (optional)
- Credentials for:
  - Twilio
  - Google Cloud Platform
  - LLM Models (OpenAI, Anthropic, DeepSeek)

### Environment Variables Configuration

Create a `.env` file in the project root with the following variables:

```
ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
DEEPSEEK_API_KEY=your_deepseek_key
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/credentials.json
```

### Local Installation

```bash
# Clone the repository
git clone [REPOSITORY_URL]
cd app

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Installation with Docker

```bash
# Build the image
docker build -t api-chatbot-ssp .

# Run the container
docker run -p 8080:8080 -d api-chatbot-ssp
```

## Execution

### Locally

```bash
uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

### With Docker

```bash
docker run -p 8080:8080 --env-file .env api-chatbot-ssp
```

## API Usage

The API will be available at `http://localhost:8080/` with the following endpoints:

- **GET /** - Healthcheck
- **POST /api/v1/agent_twilio_190/predict_twilio_190** - Endpoint for Twilio integration that processes received messages

### API Documentation

Access the interactive API documentation at:

```
http://localhost:8080/docs
```

## Contributions

1. Fork the project
2. Create your feature branch (`git checkout -b feature/feature-name`)
3. Commit your changes (`git commit -m 'Add new feature'`)
4. Push to the branch (`git push origin feature/feature-name`)
5. Open a Pull Request