# Events Management API

A production-ready serverless events management system built with FastAPI, AWS Lambda, API Gateway, and DynamoDB. Features comprehensive CORS support, input validation, error handling, and auto-generated documentation.

## Features

- **RESTful API**: Full CRUD operations for event management
- **Serverless Architecture**: AWS Lambda + API Gateway for scalability
- **NoSQL Database**: DynamoDB for fast, scalable data storage
- **Input Validation**: Pydantic models with custom validators
- **CORS Support**: Configurable cross-origin resource sharing
- **Error Handling**: Comprehensive error responses with proper HTTP status codes
- **Auto Documentation**: Interactive API docs with Swagger UI and ReDoc
- **Infrastructure as Code**: AWS CDK for reproducible deployments
- **Health Checks**: Database connectivity monitoring

## Project Structure

```
.
├── backend/              # FastAPI application
│   ├── main.py          # API implementation
│   ├── requirements.txt # Python dependencies
│   └── docs/            # Generated API documentation
├── infrastructure/       # AWS CDK infrastructure
│   ├── app.py           # CDK app entry point
│   ├── stacks/          # CDK stack definitions
│   └── requirements.txt # CDK dependencies
└── README.md            # This file
```

## Quick Start

### Prerequisites

- Python 3.12+
- AWS CLI configured with credentials
- Node.js 18+ (for AWS CDK)
- AWS CDK CLI: `npm install -g aws-cdk`

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd <project-directory>
   ```

2. **Set up the backend**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. **Run the API locally**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Access the API**
   - API: http://localhost:8000
   - Interactive docs: http://localhost:8000/docs
   - Alternative docs: http://localhost:8000/redoc

### Deploy to AWS

1. **Install CDK dependencies**
   ```bash
   cd infrastructure
   pip install -r requirements.txt
   ```

2. **Bootstrap CDK (first time only)**
   ```bash
   cdk bootstrap
   ```

3. **Deploy the stack**
   ```bash
   cdk deploy
   ```

4. **Note the API endpoint**
   The deployment will output your API Gateway URL.

## API Usage Examples

### Create an Event

```bash
curl -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Tech Conference 2025",
    "description": "Annual technology conference",
    "date": "2025-12-15T09:00:00",
    "location": "Convention Center",
    "capacity": 500,
    "organizer": "Tech Corp",
    "status": "draft"
  }'
```

### List All Events

```bash
curl http://localhost:8000/events
```

### Filter Events by Status

```bash
curl "http://localhost:8000/events?status=published&limit=50"
```

### Get a Specific Event

```bash
curl http://localhost:8000/events/{event_id}
```

### Update an Event

```bash
curl -X PUT http://localhost:8000/events/{event_id} \
  -H "Content-Type: application/json" \
  -d '{
    "status": "published",
    "capacity": 600
  }'
```

### Delete an Event

```bash
curl -X DELETE http://localhost:8000/events/{event_id}
```

### Health Check

```bash
curl http://localhost:8000/health
```

## Configuration

### Environment Variables

Create a `.env` file in the backend directory:

```env
AWS_REGION=us-east-1
DYNAMODB_TABLE_NAME=events-table
ALLOWED_ORIGINS=*
```

### Production CORS Configuration

For production, always specify exact origins:

```env
ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

## Event Schema

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| title | string | Yes | 1-200 characters |
| description | string | Yes | 1-2000 characters |
| date | string | Yes | ISO format (YYYY-MM-DD or ISO 8601) |
| location | string | Yes | 1-500 characters |
| capacity | integer | Yes | 1-100,000 |
| organizer | string | Yes | 1-200 characters |
| status | enum | No | draft, published, cancelled, completed, active |

## Development

### Running Tests

```bash
cd backend
pytest
```

### Generate API Documentation

```bash
cd backend
pdoc main.py -o docs/ --html
```

### View CDK Diff

```bash
cd infrastructure
cdk diff
```

### Synthesize CloudFormation

```bash
cd infrastructure
cdk synth
```

## Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Client    │─────▶│ API Gateway  │─────▶│   Lambda    │
└─────────────┘      └──────────────┘      └─────────────┘
                                                   │
                                                   ▼
                                            ┌─────────────┐
                                            │  DynamoDB   │
                                            └─────────────┘
```

- **API Gateway**: Handles HTTP requests and CORS
- **Lambda**: Runs FastAPI application
- **DynamoDB**: Stores event data with partition key `eventId`

## Security Best Practices

1. **CORS**: Set specific origins in production (never use `*`)
2. **Input Validation**: All inputs validated and sanitized automatically
3. **Error Messages**: Generic messages prevent information leakage
4. **IAM Permissions**: Lambda has minimal required DynamoDB permissions
5. **Field Length Limits**: Prevents buffer overflow and DoS attacks

## Troubleshooting

### DynamoDB Connection Issues

Check that:
- AWS credentials are configured correctly
- The DynamoDB table exists
- Lambda has proper IAM permissions

### CORS Errors

Ensure `ALLOWED_ORIGINS` includes your frontend domain.

### Lambda Timeout

Increase timeout in `infrastructure/stacks/main_stack.py` if needed.

## Documentation

- [Backend README](backend/README.md) - Detailed API documentation
- [Infrastructure README](infrastructure/README.md) - CDK deployment guide
- [API Documentation](backend/docs/) - Generated API reference

## License

MIT

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request
