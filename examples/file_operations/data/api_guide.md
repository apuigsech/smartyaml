# API Documentation

## Overview

This API provides access to user management and data operations.

## Authentication

All API requests require authentication using a Bearer token:

```
Authorization: Bearer YOUR_TOKEN_HERE
```

## Base URL

- Production: `https://api.example.com/v1`
- Staging: `https://staging-api.example.com/v1`
- Development: `http://localhost:8080/v1`

## Endpoints

### Users

#### GET /users
Retrieve a list of users.

**Parameters:**
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 20)
- `search` (optional): Search term for filtering

**Response:**
```json
{
  "users": [
    {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 100
  }
}
```

#### POST /users
Create a new user.

**Request Body:**
```json
{
  "name": "Jane Doe",
  "email": "jane@example.com",
  "password": "securepassword123"
}
```

#### GET /users/{id}
Retrieve a specific user by ID.

#### PUT /users/{id}
Update a user's information.

#### DELETE /users/{id}
Delete a user.

## Error Handling

The API returns standard HTTP status codes:

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Internal Server Error

Error responses include a detailed message:

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "The request parameters are invalid",
    "details": {
      "field": "email",
      "issue": "Email format is invalid"
    }
  }
}
```

## Rate Limiting

API requests are limited to 1000 requests per hour per API key.

Rate limit headers are included in all responses:
- `X-RateLimit-Limit`: Maximum requests per hour
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Unix timestamp when the rate limit resets
