# Automated GitHub PR Review Agent

An intelligent multi-agent system that analyzes GitHub Pull Requests and generates structured, actionable code review comments using Google Gemini and LangGraph orchestration.

## 🚀 Features

- **Multi-Agent Architecture**: Specialized agents for different review aspects
  - Logic Reviewer: Identifies bugs, edge cases, and algorithmic issues
  - Security Reviewer: Detects vulnerabilities and security risks
  - Performance Reviewer: Finds optimization opportunities
  - Readability Reviewer: Ensures code quality and maintainability

- **LangGraph Orchestration**: Parallel agent execution with intelligent workflow management
- **Dual Input Support**: Review GitHub PRs via URL or manual diff input
- **Industry-Standard API**: RESTful FastAPI endpoints with comprehensive documentation
- **Structured Output**: Categorized comments with severity levels and actionable suggestions

## 📋 Prerequisites

- Python 3.9+
- Google API Key (for Gemini)
- GitHub Token (optional, for fetching PRs)

## 🛠️ Installation

1. **Clone or navigate to the project directory**:
   ```bash
   cd pr-review-agent
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   ```bash
   # Copy example env file
   cp .env.example .env
   
   # Edit .env and add your API keys
   # Required: GOOGLE_API_KEY
   # Optional: GITHUB_TOKEN
   ```

## 🚦 Running the Application

### Development Mode

```bash
# Using Python
python app/main.py

# Or using Uvicorn directly
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Production Mode

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📡 API Endpoints

### Health Check

```bash
GET /health
```

### Review GitHub PR

```bash
POST /api/v1/review/github
Content-Type: application/json

{
  "pr_url": "https://github.com/owner/repo/pull/123"
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

### Get Severity Levels

```bash
GET /api/v1/review/severities
```

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
    json={"pr_url": "https://github.com/owner/repo/pull/123"}
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

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Application                   │
│                  (app/main.py - 0.0.0.0)                │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
   ┌────▼─────┐           ┌──────▼──────┐
   │  Health  │           │   Review    │
   │  Router  │           │   Router    │
   └──────────┘           └──────┬──────┘
                                 │
                         ┌───────▼────────┐
                         │ Review Service │
                         └───────┬────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │   LangGraph Workflow     │
                    │  (Parallel Execution)    │
                    └────────────┬─────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │            │           │           │            │
   ┌────▼───┐  ┌────▼────┐ ┌────▼────┐ ┌───▼─────┐ ┌────▼────┐
   │ GitHub │  │  Code   │ │ Logic   │ │Security │ │Perf/Read│
   │Fetcher │  │ Parser  │ │Reviewer │ │Reviewer │ │Reviewers│
   └────────┘  └─────────┘ └─────────┘ └─────────┘ └─────────┘
                                 │
                         ┌───────▼────────┐
                         │   Aggregator   │
                         │ (Deduplicate)  │
                         └────────────────┘
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_api.py -v
```

## 📂 Project Structure

```
pr-review-agent/
├── app/
│   ├── agents/              # Specialized review agents
│   │   ├── github_fetcher.py
│   │   ├── code_parser.py
│   │   ├── logic_reviewer.py
│   │   ├── security_reviewer.py
│   │   ├── performance_reviewer.py
│   │   └── readability_reviewer.py
│   ├── orchestration/       # LangGraph workflow
│   │   └── workflow.py
│   ├── routers/            # API endpoints
│   │   ├── health.py
│   │   └── review.py
│   ├── services/           # Business logic
│   │   ├── github_service.py
│   │   └── review_service.py
│   ├── models/             # Pydantic schemas
│   │   └── schemas.py
│   ├── config/             # Configuration
│   │   └── settings.py
│   └── main.py             # FastAPI app
├── tests/                  # Test suite
├── requirements.txt
├── .env.example
└── README.md
```

## 🔧 Configuration

Edit `.env` file:

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
```

## 🎯 Review Categories

- **Logic**: Bugs, edge cases, null pointers, incorrect algorithms
- **Security**: SQL injection, XSS, hardcoded secrets, auth issues
- **Performance**: N+1 queries, inefficient loops, memory leaks
- **Readability**: Naming, documentation, complexity, style

## 📊 Severity Levels

- **Critical**: Must fix immediately
- **Error**: Should fix before merging
- **Warning**: Should review
- **Info**: Suggestions for improvement

## 🚀 Deployment

### Docker (Optional)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables for Production

- Set `ENVIRONMENT=production`
- Configure CORS origins appropriately
- Use proper secret management for API keys
- Enable HTTPS/TLS

## 📄 License

MIT License

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📞 Support

For issues or questions, please open an issue on GitHub.

---

Built with ❤️ using FastAPI, LangGraph, and Google Gemini
