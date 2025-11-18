# Attachment Detection System

## Project Overview

The Attachment Detection System is a FastAPI-based web application designed to scan, process, and identify sensitive information in attachments from remote databases. The system syncs site and attachment data from a remote PostgreSQL database, downloads and processes various file types, and uses both traditional pattern matching and AI-powered content analysis to detect sensitive information such as ID card numbers and phone numbers.

### Key Features
- **Database Sync**: Synchronizes site and attachment data from remote PostgreSQL database
- **Multi-format Processing**: Supports processing of PDF, DOCX, XLSX, TXT, and various image formats
- **OCR Capabilities**: Uses PaddleOCR or Tesseract for text extraction from images
- **Sensitive Data Detection**: Detects ID card numbers and phone numbers using pattern matching
- **AI Analysis**: Optional OpenAI integration for advanced content analysis
- **Web Interface**: Vue.js-based frontend with dashboard, search, and sync capabilities
- **Statistics & Charts**: Visual representation of data with Chart.js integration

## Architecture

### Core Components
- `main.py`: FastAPI application with REST API endpoints
- `models.py`: SQLAlchemy database models for sites and attachments
- `config.py`: Application configuration using Pydantic Settings
- `sync.py`: Database synchronization logic for remote sites and attachments
- `download.py`: File downloading and processing functionality
- `utils.py`: Utility functions for text extraction, OCR, and pattern matching
- `static/index.html`: Vue.js frontend with Tailwind CSS styling

### Database Schema
- **Sites table**: Stores site information (owner, account, name, domain, state, aliases)
- **Attachments table**: Stores attachment metadata and analysis results (text content, OCR content, LLM content, sensitive data flags)

## Building and Running

### Prerequisites
- Python 3.8+
- PostgreSQL (optional, for remote database connection)
- MySQL (optional, for local database)
- SQLite (default local database)

### Installation

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```
3. Activate the virtual environment:
   ```bash
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Configuration

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Update the `.env` file with your database connection settings and API keys:
   ```env
   # Remote Database Configuration
   REMOTE_DB_HOST=your_remote_host
   REMOTE_DB_PORT=5432
   REMOTE_DB_NAME=your_remote_db_name
   REMOTE_DB_USER=your_username
   REMOTE_DB_PASSWORD=your_password

   # Local Database Configuration
   LOCAL_DB_TYPE=sqlite
   LOCAL_DB_PATH=./local_attachments.db

   # Cache Configuration
   ATTACHMENT_CACHE_DIR=./attachments_cache

   # OCR Configuration
   OCR_ENGINE=paddle

   # OpenAI API Configuration
   OPENAI_API_KEY=your_openai_api_key
   MODEL=gpt-4
   ```

### Running the Application

1. Start the application:
   ```bash
   python main.py
   ```
   Or using uvicorn directly:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. Access the application at `http://localhost:8000`

### API Endpoints

The application provides the following main API endpoints:

- `GET /api/sites` - Get all sites
- `GET /api/attachments` - Get attachments with filtering options
- `POST /api/sync` - Full synchronization of sites and attachments
- `POST /api/sync-sites` - Synchronize only sites
- `POST /api/sync-attachments` - Synchronize only attachments
- `POST /api/process-attachment/{id}` - Process a single attachment
- `POST /api/process-site/{id}` - Process all attachments for a site
- `GET /api/stats` - Get system statistics
- `POST /api/detect-site/{id}` - Detect sensitive content in all attachments for a site

## Development Conventions

### Code Style
- Follow PEP 8 standards for Python code
- Use type hints for function parameters and return values
- Write docstrings for complex functions and classes

### Database Models
- Use SQLAlchemy ORM for database operations
- Define models in `models.py`
- Include appropriate indexes for performance optimization

### API Design
- Use Pydantic models for request/response validation
- Follow RESTful API principles
- Implement proper error handling with HTTP exception codes

### Testing
- Write unit tests for utility functions
- Test API endpoints with appropriate test cases
- Validate OCR and text extraction capabilities

## OCR Configuration

The system supports two OCR engines:
- **PaddleOCR** (default): More accurate for Chinese text
- **Tesseract**: More versatile, better for English text

To switch between OCR engines, change the `OCR_ENGINE` setting in your `.env` file to either `paddle` or `tesseract`.

## AI Integration

The system supports AI-powered content analysis using OpenAI's GPT models. To enable AI features:
1. Set your `OPENAI_API_KEY` in the `.env` file
2. Use the `/api/process-attachment-ai` endpoint to process attachments with AI analysis
3. AI analysis enhances the detection of sensitive information by understanding context in addition to pattern matching

## Frontend

The frontend is built with:
- Vue.js 3 for reactive UI components
- Tailwind CSS for styling
- Chart.js for data visualization
- Font Awesome for icons

The frontend provides:
- Dashboard with system statistics
- Search functionality for attachments
- Site and attachment management
- Data visualization charts