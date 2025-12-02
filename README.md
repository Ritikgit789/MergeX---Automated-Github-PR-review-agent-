# MergeX - Automated GitHub PR Review Agent

> **AI-Powered Code Review Assistant** | Intelligent multi-agent system that analyzes GitHub Pull Requests and generates structured, actionable code review comments using Google Gemini and LangGraph orchestration.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-00a393.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.2+-61dafb.svg)](https://react.dev)
[![Python](https://img.shields.io/badge/Python-3.9+-3776ab.svg)](https://www.python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-Latest-ff4b4b.svg)](https://langchain-ai.github.io/langgraph/)

---

## 🌟 Overview

**MergeX** is a full-stack application that revolutionizes code review by leveraging AI-powered multi-agent architecture. It provides comprehensive PR analysis through specialized review agents, delivering actionable insights across logic, security, performance, and readability dimensions.

### ✨ Key Features

- 🤖 **Multi-Agent AI Architecture**: Specialized agents for different review aspects
  - **Logic Reviewer**: Identifies bugs, edge cases, and algorithmic issues
  - **Security Reviewer**: Detects vulnerabilities and security risks
  - **Performance Reviewer**: Finds optimization opportunities
  - **Readability Reviewer**: Ensures code quality and maintainability

- 🔒 **Private Repository Support**: Securely review private repositories using Personal Access Tokens (PAT).
  - **Secure Token Management**: Tokens are handled in-memory only, never stored or logged, and cleared immediately after use.
  - **Sidebar Settings**: Dedicated sidebar for managing session-based tokens.

- 💬 **Intelligent Interaction**:
  - **Smart Input Validation**: Distinguishes between greetings, irrelevant queries, and valid PR URLs.
  - **Friendly Assistant**: Responds to greetings and guides users on how to use the tool.

- 🔄 **LangGraph Orchestration**: Parallel agent execution with intelligent workflow management
- 🎯 **Dual Input Support**: Review GitHub PRs via URL or manual diff input
- 🎨 **Modern React Frontend**: Beautiful, responsive UI with glassmorphism design
  - **About Section**: Comprehensive help and information guide built-in.
  - **Animated UI**: Smooth transitions and engaging visual feedback.
- 🚀 **Production-Ready API**: RESTful FastAPI endpoints with comprehensive documentation
- 📊 **Structured Output**: Categorized comments with severity levels and actionable suggestions
- ☁️ **Cloud Deployment**: Configured for Render.com with `.render.yaml`

---

## 📂 Project Structure

```
MergeX/
├── app/                           # Backend FastAPI Application
│   ├── agents/                    # Specialized review agents
│   │   ├── __init__.py
│   │   ├── github_fetcher.py      # Fetches PR data from GitHub (Private/Public)
│   │   ├── code_parser.py         # Parses code diffs
│   │   ├── logic_reviewer.py      # Logic & bug detection
│   │   ├── security_reviewer.py   # Security vulnerability detection
│   │   ├── performance_reviewer.py # Performance optimization
│   │   └── readability_reviewer.py # Code quality & style
│   ├── orchestration/             # LangGraph workflow
│   │   ├── __init__.py
│   │   └── workflow.py            # Multi-agent orchestration
│   ├── routers/                   # API endpoints
│   │   ├── __init__.py
│   │   ├── health.py              # Health check endpoint
│   │   └── review.py              # Review endpoints
│   ├── services/                  # Business logic
│   │   ├── __init__.py
│   │   ├── github_service.py      # GitHub API integration
│   │   └── review_service.py      # Review orchestration
│   ├── utils/                     # Utility modules
│   │   ├── __init__.py
│   │   └── input_validator.py     # Input validation & greeting handling
│   │   └── language_detector.py   # Language detection
│   ├── models/                    # Data models
│   │   ├── __init__.py
│   │   └── schemas.py             # Pydantic schemas
│   ├── config/                    # Configuration
│   │   ├── __init__.py
│   │   └── settings.py            # App settings
│   └── __init__.py
│
├── frontend/                      # React Frontend Application
│   ├── src/
│   │   ├── components/            # React components
│   │   │   ├── Layout.jsx         # Main layout with gradient background
│   │   │   ├── PRInput.jsx        # PR URL/diff input component
│   │   │   ├── ReviewResult.jsx   # Review results display
│   │   │   ├── Sidebar.jsx        # Settings sidebar for Token management
│   │   │   └── About.jsx          # About & Help modal
│   │   ├── App.jsx                # Main App component
│   │   ├── App.css                # App-specific styles
│   │   ├── index.css              # Global styles & Tailwind
│   │   └── main.jsx               # React entry point
│   ├── public/                    # Static assets
│   ├── dist/                      # Production build output
│   ├── index.html                 # HTML template
│   ├── package.json               # Node dependencies
│   ├── vite.config.js             # Vite configuration
│   ├── tailwind.config.js         # Tailwind CSS config
│   ├── postcss.config.js          # PostCSS config
│   ├── eslint.config.js           # ESLint configuration
│   └── README.md                  # Frontend documentation
│
├── tests/                         # Test suite
│   ├── __init__.py
│   ├── test_agents.py             # Agent tests
│   └── test_api.py                # API endpoint tests
│
├── main.py                        # FastAPI application entry point
├── requirements.txt               # Python dependencies
├── .env                          # Environment variables (not in git)
├── .gitignore                    # Git ignore rules
├── .render.yaml                  # Render.com deployment config
└── README.md                     # This file
```

---

## 🛠️ Technology Stack

### Backend
- **FastAPI** - Modern, fast web framework for building APIs
- **LangGraph** - Multi-agent workflow orchestration
- **LangChain** - LLM application framework
- **Google Gemini** - AI model for code analysis
- **PyGithub** - GitHub API integration
- **Pydantic** - Data validation and settings management
- **Uvicorn** - ASGI server

### Frontend
- **React 18.2** - UI library
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **Framer Motion** - Animation library
- **Axios** - HTTP client
- **Lucide React** - Icon library

### Testing
- **Pytest** - Testing framework
- **pytest-asyncio** - Async test support
- **pytest-cov** - Coverage reporting
- **httpx** - HTTP client for testing

---

## 📋 Prerequisites

- **Python 3.9+**
- **Node.js 18+** and **npm**
- **Google API Key** (for Gemini)
- **GitHub Token** (optional, for fetching PRs)

---

## 🚀 Installation & Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd MergeX
```

### 2. Backend Setup

#### Create Virtual Environment

```bash
# Windows
python -m venv pragentenv
pragentenv\Scripts\activate

# Linux/Mac
python3 -m venv pragentenv
source pragentenv/bin/activate
```

#### Install Python Dependencies

```bash
pip install -r requirements.txt
```

#### Configure Environment Variables

Create a `.env` file in the root directory:

```env
# Required
GOOGLE_API_KEY=your_google_api_key_here

# Optional
GITHUB_TOKEN=your_github_token_here

# Model Settings
GEMINI_MODEL=gemini-1.5-flash
GEMINI_TEMPERATURE=0.3
GEMINI_MAX_TOKENS=2048

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
ENVIRONMENT=development
```

### 3. Frontend Setup

```bash
cd frontend
npm install
```

---

## 🏃 Running the Application

### Development Mode

#### Start Backend Server

```bash
# From root directory
python main.py

# Or using Uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The backend API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

#### Start Frontend Dev Server

```bash
# From frontend directory
cd frontend
npm run dev
```

The frontend will be available at: http://localhost:5173

### Production Mode

#### Build Frontend

```bash
cd frontend
npm run build
```

#### Run Backend in Production

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 📡 API Endpoints

### Health Check

```bash
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": "1.0.0"
}
```

### Review GitHub PR

```bash
POST /api/v1/review/github
Content-Type: application/json

{
  "pr_url": "https://github.com/owner/repo/pull/123",
  "github_token": "optional_token_for_private_repos"
}
```

### Review Manual Diff

```bash
POST /api/v1/review/diff
Content-Type: application/json

{
  "diff": "--- a/file.py\n+++ b/file.py\n...",
  "language": "python",
  "context": "Optional context about the changes"
}
```

### Get Review Categories

```bash
GET /api/v1/review/categories
```

**Response:**
```json
{
  "categories": ["logic", "security", "performance", "readability"]
}
```

### Get Severity Levels

```bash
GET /api/v1/review/severities
```

**Response:**
```json
{
  "severities": ["critical", "error", "warning", "info"]
}
```

---

## 📝 Example Usage

### Using cURL

```bash
# Review a manual diff
curl -X POST http://localhost:8000/api/v1/review/diff \
  -H "Content-Type: application/json" \
  -d '{
    "diff": "--- a/app.py\n+++ b/app.py\n@@ -1,3 +1,4 @@\n def process_data(data):\n-    return data\n+    result = data * 2\n+    return result",
    "language": "python"
  }'
```

### Using Python Requests

```python
import requests

# Review GitHub PR
response = requests.post(
    "http://localhost:8000/api/v1/review/github",
    json={
        "pr_url": "https://github.com/owner/repo/pull/123",
        "github_token": "your_token_if_private" 
    }
)

result = response.json()
print(f"Status: {result['status']}")
print(f"Summary: {result['summary']}")
print(f"Total Issues: {result['total_issues']}")

for comment in result['comments']:
    print(f"\n{comment['severity'].upper()}: {comment['category']}")
    print(f"File: {comment['file_path']}:{comment['line_number']}")
    print(f"Message: {comment['message']}")
    if comment['suggestion']:
        print(f"Suggestion: {comment['suggestion']}")
```

### Using the Frontend

1. Navigate to http://localhost:5173
2. **For Public Repos**:
   - Paste a GitHub PR URL directly.
   - Click "Review Code".
3. **For Private Repos**:
   - Click the **Settings** icon (Sidebar) in the top right.
   - Enter your GitHub Personal Access Token (PAT).
   - Close the sidebar and paste your PR URL.
   - Click "Review Code".
4. View categorized results with severity levels.

---

## 🔒 Security & Privacy

MergeX is designed with security in mind, especially when handling private repositories:

- **Ephemeral Token Usage**: GitHub tokens provided via the frontend are **never stored** in any database or file.
- **In-Memory Only**: Tokens are held in memory only for the duration of the API request and are immediately cleared from the backend state after fetching the PR data.
- **No Logging**: Tokens are masked in all server logs.
- **Client-Side Safety**: The frontend does not persist tokens in local storage or cookies; they must be re-entered if the page is reloaded (by design, for security).

---

## 🎨 Frontend Features

- **Glassmorphism Design**: Modern, premium UI with frosted glass effects
- **Animated Gradient Background**: Dynamic mesh gradient animation
- **Responsive Layout**: Works on all screen sizes
- **Real-time Feedback**: Loading states and error handling
- **Syntax Highlighting**: Code diffs with proper formatting
- **Categorized Results**: Organized by severity and category
- **Smooth Animations**: Framer Motion for fluid transitions
- **Interactive Sidebar**: Easy access to settings and token management
- **About Modal**: Built-in documentation and help guide

---

## 🔧 Configuration

### Backend Configuration (`app/config/settings.py`)

```python
class Settings(BaseSettings):
    app_name: str = "PR Review Agent"
    app_version: str = "1.0.0"
    environment: str = "development"
    
    google_api_key: str
    github_token: Optional[str] = None
    
    gemini_model: str = "gemini-1.5-flash"
    gemini_temperature: float = 0.3
    gemini_max_tokens: int = 2048
    
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"
```

### Frontend Configuration

- **Vite Config**: `frontend/vite.config.js`
- **Tailwind Config**: `frontend/tailwind.config.js`
- **ESLint Config**: `frontend/eslint.config.js`

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

---

## 📞 Support

For issues, questions, or feature requests:
- 🐛 **Bug Reports**: Open an issue on GitHub
- 💡 **Feature Requests**: Open an issue with the `enhancement` label
- 📧 **Contact**: [Your contact information]

---

## 🙏 Acknowledgments

- **FastAPI** - For the amazing web framework
- **LangChain & LangGraph** - For multi-agent orchestration
- **Google Gemini** - For powerful AI capabilities
- **React & Vite** - For modern frontend development
- **Tailwind CSS** - For beautiful, utility-first styling

---

<div align="center">

**Built with ❤️ using FastAPI, React, LangGraph, and Google Gemini**

⭐ Star this repo if you find it helpful!

</div>
