# Nexora Backend

Backend foundation for **Nexora**, an AI Automation Agent platform.

## Tech Stack

- Python 3.14
- FastAPI
- Uvicorn
- Pydantic
- SQLAlchemy
- PostgreSQL
- python-dotenv

## Project Structure

```text
backend/
├── app/
│   ├── main.py
│   ├── api/
│   ├── models/
│   ├── schemas/
│   ├── database/
│   ├── agents/
│   ├── tools/
│   ├── llm/
│   └── services/
├── tests/
├── requirements.txt
└── .env.example
Setup

Create and activate the virtual environment:

python -m venv .venv
.venv\Scripts\activate

Install dependencies:

pip install -r requirements.txt
Run the Server
uvicorn app.main:app --reload

The API runs at:

http://127.0.0.1:8000
API Documentation

Swagger UI:

http://127.0.0.1:8000/docs

Health check:

http://127.0.0.1:8000/health
Current Status

Backend foundation is complete and the FastAPI server is running successfully.

Future modules will include:

AI Agent
LLM integration
Automation tools
Machine Learning
PostgreSQL database
Authentication
Task execution and verification