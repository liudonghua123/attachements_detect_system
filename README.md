# Attachment Detection System

[![License](https://img.shields.io/github/license/liudonghua123/attachements_detect_system)](https://github.com/liudonghua123/attachements_detect_system/blob/main/LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green)](https://fastapi.tiangolo.com/)
[![Vue.js](https://img.shields.io/badge/Vue.js-3.0%2B-brightgreen)](https://vuejs.org/)

A powerful web application that scans, processes, and identifies sensitive information in attachments from remote databases. The system provides comprehensive tools for detecting ID cards, phone numbers, and other sensitive data with both pattern matching and AI-powered analysis capabilities.

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Frontend Overview](#frontend-overview)
- [OCR Configuration](#ocr-configuration)
- [AI Integration](#ai-integration)
- [Development Guidelines](#development-guidelines)
- [Testing](#testing)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)
- [Support](#support)
- [Changelog](#changelog)

## Features

- **Database Sync**: Synchronize site and attachment data from remote PostgreSQL database
- **Multi-format Processing**: Supports PDF, DOCX, XLSX, TXT, images, and archive files (ZIP/RAR)
- **OCR Capabilities**: Advanced text extraction from images using PaddleOCR or Tesseract
- **Sensitive Data Detection**: Pattern-based detection for ID card numbers and phone numbers
- **AI Analysis**: Optional OpenAI integration for advanced content analysis
- **Web Interface**: Vue.js-based frontend with intuitive dashboard and search capabilities
- **Progress Tracking**: Real-time progress display with WebSocket updates during bulk operations
- **Visual Analytics**: Chart.js integration for data visualization and statistics
- **Real-time Updates**: WebSocket-based progress notifications for long-running operations
- **Advanced Search**: Comprehensive search capabilities with multiple filters and criteria
- **Responsive Design**: Mobile-first responsive layout for various screen sizes

## Architecture

### Core Components

- `main.py`: FastAPI application with REST API endpoints
- `models.py`: SQLAlchemy database models for sites and attachments
- `config.py`: Application configuration using Pydantic Settings
- `sync.py`: Database synchronization logic for remote sites and attachments
- `download.py`: File downloading, caching, and processing functionality
- `utils.py`: Utility functions for text extraction, OCR, pattern matching, and AI analysis
- `static/index.html`: Vue.js frontend with Tailwind CSS styling

### Database Schema

- **Sites table**: Stores site information (owner, account, name, domain, state, aliases)
- **Attachments table**: Stores attachment metadata and analysis results (text content, OCR content, LLM content, sensitive data flags)

### Technology Stack

- **Backend**: Python, FastAPI, SQLAlchemy
- **Database**: SQLite (default), PostgreSQL, MySQL
- **Frontend**: Vue 3, Tailwind CSS, Chart.js
- **OCR**: PaddleOCR or Tesseract
- **AI**: OpenAI GPT-4 integration
- **WebSocket**: Real-time progress updates

## Requirements

### System Requirements
- Python 3.8 or higher
- 2GB+ RAM recommended
- 500MB+ disk space for initial setup
- Internet connection for downloading attachments and optional AI services

### Database Requirements
- PostgreSQL (optional, for remote database connection)
- SQLite (default local database) - no additional installation required
- MySQL (optional) - requires PyMySQL

### Optional Dependencies
- For PaddleOCR: paddlepaddle and paddleocr packages
- For Tesseract: pytesseract and tesseract-ocr
- For AI features: OpenAI API key

## Installation

### Quick Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/liudonghua123/attachements_detect_system
   cd attachements_detect_system
   ```

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

### OCR Setup

If using PaddleOCR:

```bash
pip install paddlepaddle paddleocr
```

If using Tesseract:
- Install Tesseract OCR engine (system-level installation required)
- On Windows: Download from [tesseract-ocr.github.io](https://tesseract-ocr.github.io/)
- On macOS: `brew install tesseract`
- On Ubuntu/Debian: `sudo apt-get install tesseract-ocr`

## Configuration

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
   OCR_ENGINE=paddle  # Options: paddle, tesseract

   # OpenAI API Configuration
   OPENAI_API_KEY=your_openai_api_key
   MODEL=gpt-4
   OPENAI_BASE_URL=https://api.openai.com/v1

   # Prompts for AI Analysis
   PROMPTS=Analyze the following content and identify any sensitive information such as personal identification numbers, phone numbers, addresses, or other private data. Respond with "SENSITIVE: [type of sensitive data found]" if sensitive data is detected, otherwise respond with "CLEAN: No sensitive data found."

   # Attachment Base URL
   ATTACHMENT_DEFAULT_BASE_URL=https://example.com
   ```

## Usage

### Starting the Application

1. Start the application:
   ```bash
   python main.py
   ```
   
   Or using uvicorn directly:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. Access the application at `http://localhost:8000`

3. For API documentation, visit `http://localhost:8000/docs`

### Basic Workflow

1. **Sync Data**: Use the sync functionality to retrieve site and attachment information from the remote database
2. **Search**: Use the search interface to find attachments based on various criteria
3. **Process/Detect**: Process individual attachments or run bulk detection on entire sites
4. **Review Results**: Check the dashboard for statistics and identified sensitive data
5. **Export**: Export results as needed for further processing

## API Documentation

### Authentication

Most endpoints are public. Some features may require API keys if configured.

### Core Endpoints

- `GET /api/sites` - Get all sites with metadata
- `GET /api/attachments` - Get attachments with filtering options
- `POST /api/sync` - Full synchronization of sites and attachments
- `POST /api/sync-sites` - Synchronize only sites
- `POST /api/sync-attachments` - Synchronize only attachments
- `POST /api/process-attachment/{id}` - Process a single attachment
- `POST /api/process-attachment-ai/{id}` - Process a single attachment with AI analysis
- `POST /api/process-site/{id}` - Process all attachments for a site
- `GET /api/stats` - Get system statistics
- `POST /api/detect-site/{id}` - Detect sensitive content in all attachments for a site
- `GET /ws/{ws_id}` - WebSocket endpoint for progress updates
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation (ReDoc)

### Filtering Parameters

The `/api/attachments` endpoint supports the following query parameters:

| Parameter | Type | Description |
|----------|------|-------------|
| `site_id` | integer | Filter by site ID |
| `site_owner` | string | Filter by site owner |
| `site_state` | integer | Filter by site state (0=active, 1=inactive, 2=suspended) |
| `text_content_search` | string | Search in extracted text content |
| `ocr_content_search` | string | Search in OCR content |
| `has_id_card` | boolean | Filter by ID card detection |
| `has_phone` | boolean | Filter by phone number detection |
| `file_ext` | string | Filter by file extension |
| `manual_verified_sensitive` | boolean | Filter by manual verification status |
| `skip` | integer | Pagination offset (default: 0) |
| `limit` | integer | Pagination limit (default: 100) |

### Example API Usage

```bash
# Get all attachments for a specific site
curl "http://localhost:8000/api/attachments?site_id=1&has_id_card=true"

# Process a single attachment
curl -X POST "http://localhost:8000/api/process-attachment/123"

# Get system statistics
curl "http://localhost:8000/api/stats"

# Synchronize all data
curl -X POST "http://localhost:8000/api/sync"
```

## Frontend Overview

The frontend is built with modern web technologies for an optimal user experience:

### Dashboard Features
- System statistics with visual charts
- Site and attachment counts
- Sensitive data detection metrics
- Data visualization with Chart.js

### Search Interface
- Advanced filtering options
- Real-time search suggestions
- Pagination controls
- Export functionality

### Processing Features
- Bulk processing with progress tracking
- Individual attachment processing
- AI-powered analysis options
- WebSocket-based progress updates

### Responsive Design
- Mobile-first approach
- Tablet and desktop optimized
- Touch-friendly interfaces
- Cross-browser compatibility

## OCR Configuration

The system supports two OCR engines with different strengths:

### PaddleOCR (Recommended for Chinese text)
- More accurate for Chinese characters
- Better handling of complex layouts
- Higher accuracy for scanned documents

### Tesseract (Better for English text)
- More versatile and widely supported
- Better for English and Latin-based text
- Good performance with clear documents

To switch between OCR engines, change the `OCR_ENGINE` setting in your `.env` file to either `paddle` or `tesseract`.

## AI Integration

The system supports advanced AI-powered content analysis using OpenAI's GPT models:

### Setup
1. Set your `OPENAI_API_KEY` in the `.env` file
2. Configure the model type in the settings (default: `gpt-4`)
3. Adjust the analysis prompts as needed

### Capabilities
- Context-aware sensitive data detection
- Identification of complex patterns
- Natural language understanding
- Advanced privacy risk assessment

### Endpoints
- `/api/process-attachment-ai/{id}` - Process with AI analysis
- AI analysis enhances traditional pattern matching

## Development Guidelines

### Code Style
- Follow PEP 8 standards for Python code
- Use type hints for function parameters and return values
- Write docstrings for complex functions and classes
- Maintain consistent naming conventions

### Database Models
- Use SQLAlchemy ORM for database operations
- Define models in `models.py`
- Include appropriate indexes for performance optimization
- Follow naming conventions for consistency

### API Design
- Use Pydantic models for request/response validation
- Follow RESTful API principles
- Implement proper error handling with HTTP exception codes
- Document API endpoints with examples

### Testing
- Write unit tests for utility functions
- Test API endpoints with appropriate test cases
- Validate OCR and text extraction capabilities
- Test error handling scenarios

### Security
- Validate and sanitize all inputs
- Use parameterized queries to prevent SQL injection
- Implement proper authentication when required
- Follow security best practices

## Testing

### Unit Tests
Run unit tests with pytest:

```bash
pytest tests/
```

### API Tests
Test API endpoints using the built-in test client:

```bash
pytest tests/test_api.py
```

### End-to-End Tests
If available, run end-to-end tests:

```bash
pytest tests/e2e/
```

## Deployment

### Production Setup

For production deployment, consider:

1. **Use a WSGI server**:
   ```bash
   # Using Gunicorn
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
   
   # Using Uvicorn with multiple workers
   uvicorn main:app --workers 4 --host 0.0.0.0 --port 8000
   ```

2. **Configure a reverse proxy** (Nginx recommended)

3. **Set up proper logging**

4. **Use a production database** (PostgreSQL recommended)

### Environment Configuration

For production environments:

```env
# Production settings
DEBUG=false
LOG_LEVEL=info
WORKERS=4
MAX_WORKERS=4
TIMEOUT=300

# Database settings for production
LOCAL_DB_TYPE=postgresql
LOCAL_DB_HOST=your_db_host
LOCAL_DB_PORT=5432
LOCAL_DB_NAME=your_db_name
LOCAL_DB_USER=your_db_user
LOCAL_DB_PASSWORD=your_db_password

# Security settings
ALLOWED_HOSTS=yourdomain.com,subdomain.yourdomain.com
CORS_ALLOW_ORIGINS=https://yourdomain.com
```

## Troubleshooting

### Common Issues

1. **OCR Not Working**
   - Check if OCR engine is installed: `pip list | grep ocr`
   - Verify Tesseract is installed at system level
   - Check OCR_ENGINE setting in .env file

2. **Database Connection Issues**
   - Verify database credentials in .env
   - Check database service is running
   - Ensure proper permissions for database access

3. **AI API Errors**
   - Confirm OpenAI API key is valid
   - Check internet connectivity
   - Verify rate limits are not exceeded

4. **File Processing Failures**
   - Check attachment cache directory permissions
   - Verify file download URLs are accessible
   - Ensure sufficient disk space

### Debugging

Enable debug mode by setting `DEBUG=true` in your .env file. This will provide more detailed error messages but should never be used in production.

### Logging

The application logs to standard output. For production, configure logging to write to files:

```python
import logging
logging.basicConfig(level=logging.INFO, filename='app.log')
```

## Contributing

We welcome contributions! Here's how you can help:

### Reporting Issues
- Use the GitHub issue tracker
- Provide detailed steps to reproduce
- Include environment information
- Suggest possible solutions when possible

### Pull Requests
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Ensure tests pass (`pytest`)
5. Add documentation for new features
6. Submit a pull request

### Development Process
- Follow the existing code style
- Write tests for new functionality
- Update documentation as needed
- Ensure backward compatibility

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

### Getting Help
- Check the [GitHub Issues](https://github.com/liudonghua123/attachements_detect_system/issues) for similar problems
- Open a new issue for bugs or feature requests
- Include system information when reporting issues

### Contact
- Repository: [https://github.com/liudonghua123/attachements_detect_system](https://github.com/liudonghua123/attachements_detect_system)
- Issues: [GitHub Issues](https://github.com/liudonghua123/attachements_detect_system/issues)

## Changelog

### v0.1.0
- Initial release
- Basic attachment processing
- Sensitive data detection
- Web interface with Vue.js

---

For more information, visit the [GitHub repository](https://github.com/liudonghua123/attachements_detect_system) or open an issue for questions and suggestions.