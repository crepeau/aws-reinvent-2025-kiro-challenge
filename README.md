# AWS re:Invent 2025 Kiro Challenge

This project contains a FastAPI backend and CDK infrastructure.

## Project Structure

```
.
├── backend/          # FastAPI application
└── infrastructure/   # AWS CDK infrastructure
```

## Getting Started

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Infrastructure
```bash
cd infrastructure
pip install -r requirements.txt
cdk synth
```
