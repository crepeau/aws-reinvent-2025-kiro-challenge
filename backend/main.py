from fastapi import FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
import os
import uuid
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Events API",
    version="1.0.0",
    description="API for managing events with proper CORS and error handling"
)

# CORS Configuration
# Configure allowed origins based on environment
allowed_origins = os.getenv('ALLOWED_ORIGINS', '*').split(',')

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,  # Cache preflight requests for 1 hour
)


# Global exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with detailed messages"""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": " -> ".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    logger.warning(f"Validation error: {errors}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": errors
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors"""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected error occurred",
            "message": "Please try again later or contact support"
        }
    )

# DynamoDB setup with error handling
try:
    dynamodb = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION', 'us-east-1'))
    table_name = os.getenv('DYNAMODB_TABLE_NAME', 'events-table')
    table = dynamodb.Table(table_name)
    logger.info(f"Connected to DynamoDB table: {table_name}")
except Exception as e:
    logger.error(f"Failed to connect to DynamoDB: {str(e)}")
    table = None


class EventStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    ACTIVE = "active"


class EventBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Event title")
    description: str = Field(..., min_length=1, max_length=2000, description="Event description")
    date: str = Field(..., description="Event date in ISO format (YYYY-MM-DD or ISO 8601)")
    location: str = Field(..., min_length=1, max_length=500, description="Event location")
    capacity: int = Field(..., gt=0, le=100000, description="Maximum number of attendees")
    organizer: str = Field(..., min_length=1, max_length=200, description="Event organizer name")
    status: EventStatus = EventStatus.DRAFT
    
    @validator('title', 'description', 'location', 'organizer')
    def strip_whitespace(cls, v):
        """Strip leading/trailing whitespace"""
        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("Field cannot be empty or only whitespace")
        return v
    
    @validator('date')
    def validate_date(cls, v):
        """Validate date format and ensure it's not in the past"""
        try:
            # Try parsing as ISO format
            event_date = datetime.fromisoformat(v.replace('Z', '+00:00'))
            # Check if date is not too far in the past (allow some flexibility for testing)
            if event_date.date() < datetime.utcnow().date():
                logger.warning(f"Event date {v} is in the past")
            return v
        except ValueError:
            raise ValueError("Date must be in valid ISO format (e.g., 2024-12-31 or 2024-12-31T10:00:00)")


class EventCreate(EventBase):
    eventId: Optional[str] = Field(None, description="Optional custom event ID")


class EventUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    date: Optional[str] = None
    location: Optional[str] = Field(None, min_length=1, max_length=500)
    capacity: Optional[int] = Field(None, gt=0)
    organizer: Optional[str] = Field(None, min_length=1, max_length=200)
    status: Optional[EventStatus] = None


class Event(EventBase):
    eventId: str
    createdAt: str
    updatedAt: str


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Events API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "events": "/events",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    db_status = "connected" if table is not None else "disconnected"
    
    # Try a simple DynamoDB operation to verify connectivity
    if table is not None:
        try:
            table.table_status
            db_status = "healthy"
        except Exception as e:
            logger.error(f"DynamoDB health check failed: {str(e)}")
            db_status = "unhealthy"
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/events", response_model=Event, status_code=status.HTTP_201_CREATED)
async def create_event(event: EventCreate):
    """Create a new event"""
    if table is None:
        logger.error("DynamoDB table not available")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service is unavailable"
        )
    
    event_id = event.eventId if event.eventId else str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()
    
    item = {
        'eventId': event_id,
        'title': event.title,
        'description': event.description,
        'date': event.date,
        'location': event.location,
        'capacity': event.capacity,
        'organizer': event.organizer,
        'status': event.status.value,
        'createdAt': timestamp,
        'updatedAt': timestamp
    }
    
    try:
        table.put_item(Item=item)
        logger.info(f"Created event: {event_id}")
        return Event(**item)
    except ClientError as e:
        error_code = e.response['Error']['Code']
        logger.error(f"DynamoDB ClientError creating event: {error_code} - {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {error_code}"
        )
    except Exception as e:
        logger.error(f"Unexpected error creating event: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create event"
        )


@app.get("/events", response_model=List[Event])
async def list_events(
    status: Optional[EventStatus] = None,
    limit: int = 100
):
    """List all events with optional status filter"""
    if table is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service is unavailable"
        )
    
    # Validate limit parameter
    if not isinstance(limit, int) or limit < 1 or limit > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit must be between 1 and 1000"
        )
    
    try:
        if status:
            response = table.scan(
                FilterExpression=Key('status').eq(status.value),
                Limit=limit
            )
        else:
            response = table.scan(Limit=limit)
        
        items = response.get('Items', [])
        logger.info(f"Listed {len(items)} events")
        return [Event(**item) for item in items]
    except ClientError as e:
        error_code = e.response['Error']['Code']
        logger.error(f"DynamoDB ClientError listing events: {error_code} - {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {error_code}"
        )
    except Exception as e:
        logger.error(f"Unexpected error listing events: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list events"
        )


@app.get("/events/{event_id}", response_model=Event)
async def get_event(event_id: str):
    """Get a specific event by ID"""
    if table is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service is unavailable"
        )
    
    try:
        response = table.get_item(Key={'eventId': event_id})
        
        if 'Item' not in response:
            logger.warning(f"Event not found: {event_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event with ID {event_id} not found"
            )
        
        logger.info(f"Retrieved event: {event_id}")
        return Event(**response['Item'])
    except HTTPException:
        raise
    except ClientError as e:
        error_code = e.response['Error']['Code']
        logger.error(f"DynamoDB ClientError getting event: {error_code} - {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {error_code}"
        )
    except Exception as e:
        logger.error(f"Unexpected error getting event: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get event"
        )


@app.put("/events/{event_id}", response_model=Event)
async def update_event(event_id: str, event_update: EventUpdate):
    """Update an existing event"""
    if table is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service is unavailable"
        )
    
    # Build update expression
    update_data = event_update.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update. Provide at least one field to update"
        )
    
    # First check if event exists
    try:
        response = table.get_item(Key={'eventId': event_id})
        if 'Item' not in response:
            logger.warning(f"Event not found for update: {event_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event with ID {event_id} not found"
            )
    except HTTPException:
        raise
    except ClientError as e:
        error_code = e.response['Error']['Code']
        logger.error(f"DynamoDB ClientError checking event: {error_code} - {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {error_code}"
        )
    except Exception as e:
        logger.error(f"Unexpected error checking event: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check event"
        )
    
    update_data['updatedAt'] = datetime.utcnow().isoformat()
    
    update_expression = "SET " + ", ".join([f"#{k} = :{k}" for k in update_data.keys()])
    expression_attribute_names = {f"#{k}": k for k in update_data.keys()}
    expression_attribute_values = {f":{k}": v.value if isinstance(v, EventStatus) else v for k, v in update_data.items()}
    
    try:
        response = table.update_item(
            Key={'eventId': event_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues='ALL_NEW'
        )
        
        logger.info(f"Updated event: {event_id}")
        return Event(**response['Attributes'])
    except ClientError as e:
        error_code = e.response['Error']['Code']
        logger.error(f"DynamoDB ClientError updating event: {error_code} - {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {error_code}"
        )
    except Exception as e:
        logger.error(f"Unexpected error updating event: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update event"
        )


@app.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(event_id: str):
    """Delete an event"""
    if table is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service is unavailable"
        )
    
    try:
        response = table.get_item(Key={'eventId': event_id})
        if 'Item' not in response:
            logger.warning(f"Event not found for deletion: {event_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event with ID {event_id} not found"
            )
        
        table.delete_item(Key={'eventId': event_id})
        logger.info(f"Deleted event: {event_id}")
        return None
    except HTTPException:
        raise
    except ClientError as e:
        error_code = e.response['Error']['Code']
        logger.error(f"DynamoDB ClientError deleting event: {error_code} - {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {error_code}"
        )
    except Exception as e:
        logger.error(f"Unexpected error deleting event: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete event"
        )


# Lambda handler using Mangum
from mangum import Mangum
handler = Mangum(app, lifespan="off")
