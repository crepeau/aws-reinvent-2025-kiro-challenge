---
inclusion: fileMatch
fileMatchPattern: '**/*{api,route,endpoint,handler,controller}*'
---

# API Standards and Conventions

This steering file provides REST API conventions and standards for this project.

## HTTP Methods

- **GET**: Retrieve resources (idempotent, no side effects)
- **POST**: Create new resources or trigger actions
- **PUT**: Replace entire resource (idempotent)
- **PATCH**: Partial update of resource (idempotent)
- **DELETE**: Remove resource (idempotent)

## HTTP Status Codes

### Success (2xx)
- **200 OK**: Successful GET, PUT, PATCH, or DELETE
- **201 Created**: Successful POST that creates a resource
- **204 No Content**: Successful request with no response body (e.g., DELETE)

### Client Errors (4xx)
- **400 Bad Request**: Invalid request syntax or validation failure
- **401 Unauthorized**: Missing or invalid authentication
- **403 Forbidden**: Authenticated but lacks permission
- **404 Not Found**: Resource doesn't exist
- **409 Conflict**: Request conflicts with current state (e.g., duplicate)
- **422 Unprocessable Entity**: Validation errors on request body

### Server Errors (5xx)
- **500 Internal Server Error**: Unexpected server error
- **502 Bad Gateway**: Invalid response from upstream server
- **503 Service Unavailable**: Temporary unavailability

## JSON Response Format Standards

### Success Response
```json
{
  "data": {
    "id": "123",
    "attribute": "value"
  },
  "meta": {
    "timestamp": "2025-12-03T10:30:00Z"
  }
}
```

### Collection Response
```json
{
  "data": [
    {"id": "1", "name": "Item 1"},
    {"id": "2", "name": "Item 2"}
  ],
  "meta": {
    "total": 2,
    "page": 1,
    "per_page": 20
  }
}
```

### Error Response
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input provided",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format"
      }
    ]
  },
  "meta": {
    "timestamp": "2025-12-03T10:30:00Z",
    "request_id": "abc-123"
  }
}
```

## Naming Conventions

- Use plural nouns for collections: `/users`, `/products`
- Use kebab-case for multi-word resources: `/order-items`
- Use path parameters for resource IDs: `/users/{user_id}`
- Use query parameters for filtering: `/users?status=active&role=admin`

## Best Practices

- Always include appropriate Content-Type headers (`application/json`)
- Use consistent field naming (snake_case or camelCase project-wide)
- Include timestamps in ISO 8601 format
- Provide meaningful error messages with actionable details
- Version APIs when breaking changes occur: `/v1/users`
