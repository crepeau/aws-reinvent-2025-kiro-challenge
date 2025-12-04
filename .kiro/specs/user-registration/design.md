# Design Document: User Registration System

## Overview

The user registration system is a backend service that manages users, events, and registrations with capacity constraints and waitlist functionality. The system provides APIs for creating users and events, registering/unregistering users for events, and querying registration status. The core challenge is maintaining data consistency when handling concurrent registrations for limited capacity events while automatically promoting users from waitlists when spots become available.

## Architecture

The system follows a layered architecture with clear separation of concerns:

### Layers

1. **API Layer**: Exposes REST endpoints for all operations
2. **Service Layer**: Contains business logic for registration rules, capacity enforcement, and waitlist management
3. **Repository Layer**: Handles data persistence and retrieval
4. **Domain Model Layer**: Defines core entities and their relationships

### Key Design Decisions

- **In-memory storage**: For simplicity, the initial implementation uses in-memory data structures. This can be replaced with a database later without changing the service layer.
- **Synchronous processing**: Registration operations are processed synchronously to ensure immediate consistency
- **Atomic operations**: Critical operations (like waitlist promotion) use locking mechanisms to prevent race conditions
- **Event-driven waitlist promotion**: When a user unregisters, the system immediately checks and promotes the next waitlisted user

## Components and Interfaces

### Domain Models

#### User
```python
class User:
    user_id: str
    name: str
```

#### Event
```python
class Event:
    event_id: str
    name: str
    capacity: int
    has_waitlist: bool
    registrations: List[str]  # List of user_ids
    waitlist: List[str]  # Ordered list of user_ids
```

#### Registration
```python
class Registration:
    user_id: str
    event_id: str
    status: RegistrationStatus  # REGISTERED or WAITLISTED
```

### Service Interfaces

#### UserService
- `create_user(user_id: str, name: str) -> User`
- `get_user(user_id: str) -> Optional[User]`

#### EventService
- `create_event(event_id: str, name: str, capacity: int, has_waitlist: bool) -> Event`
- `get_event(event_id: str) -> Optional[Event]`

#### RegistrationService
- `register_user(user_id: str, event_id: str) -> RegistrationResult`
- `unregister_user(user_id: str, event_id: str) -> bool`
- `get_user_registrations(user_id: str) -> List[Event]`
- `get_waitlist_position(user_id: str, event_id: str) -> Optional[int]`
- `promote_from_waitlist(event_id: str) -> Optional[str]`

### API Endpoints

- `POST /users` - Create a new user
- `GET /users/{user_id}` - Get user details
- `POST /events` - Create a new event
- `GET /events/{event_id}` - Get event details
- `POST /events/{event_id}/register` - Register a user for an event
- `DELETE /events/{event_id}/register/{user_id}` - Unregister a user
- `GET /users/{user_id}/events` - List user's registered events
- `GET /events/{event_id}/waitlist/{user_id}` - Get waitlist position

## Data Models

### Storage Structure

```python
# In-memory storage
users: Dict[str, User] = {}
events: Dict[str, Event] = {}
registrations: Dict[str, List[str]] = {}  # user_id -> [event_ids]
```

### Relationships

- A User can have multiple Registrations (one-to-many)
- An Event can have multiple Registrations (one-to-many)
- Each Event maintains its own waitlist as an ordered list
- Registrations are bidirectionally indexed for efficient queries


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: User creation preserves attributes
*For any* valid userId and name, creating a user should result in a User object with exactly those attributes.
**Validates: Requirements 1.1**

### Property 2: Capacity is never exceeded
*For any* event with a defined capacity, the number of registered users should never exceed that capacity, regardless of the sequence of registration and unregistration operations.
**Validates: Requirements 2.1, 7.1**

### Property 3: Waitlist enables overflow registration
*For any* event with waitlist enabled and at full capacity, attempting to register an additional user should add that user to the waitlist rather than rejecting the registration.
**Validates: Requirements 2.2, 3.3**

### Property 4: Events without waitlists reject overflow
*For any* event without waitlist enabled and at full capacity, attempting to register an additional user should reject the registration request.
**Validates: Requirements 2.3**

### Property 5: Successful registration creates association
*For any* user and event with available capacity, registering the user should create a registration that appears in both the event's registration list and the user's registered events list.
**Validates: Requirements 3.1**

### Property 6: Registration is idempotent
*For any* user already registered for an event, attempting to register again should be rejected without creating duplicate registrations or modifying the existing registration.
**Validates: Requirements 3.4**

### Property 7: Unregistration removes association
*For any* registered user and event, unregistering should remove the registration from both the event's registration list and the user's registered events list, and decrease the registered count by exactly one.
**Validates: Requirements 4.1**

### Property 8: Waitlist promotion is automatic
*For any* event with a non-empty waitlist, when a registered user unregisters, the first user in the waitlist should be automatically promoted to registered status and removed from the waitlist.
**Validates: Requirements 4.2, 6.3, 7.4**

### Property 9: Waitlist order is preserved
*For any* waitlist with multiple users, removing a user from any position should maintain the relative order of all remaining users in the waitlist.
**Validates: Requirements 4.3, 7.2**

### Property 10: User registrations query is complete
*For any* user with registrations, querying their registered events should return exactly the set of events where they have active registrations, with no duplicates and no omissions.
**Validates: Requirements 5.1**

### Property 11: Waitlisted events are excluded from registrations
*For any* user who is on the waitlist for an event but not registered, that event should not appear in the user's registered events list.
**Validates: Requirements 5.2**

### Property 12: Waitlist position is accurate
*For any* user on an event's waitlist, querying their position should return their exact index in the waitlist queue (1-indexed), reflecting their place in line for promotion.
**Validates: Requirements 6.1**

## Error Handling

### Validation Errors
- **Duplicate User ID**: Return 409 Conflict when attempting to create a user with an existing userId
- **Missing Required Fields**: Return 400 Bad Request when required fields are missing or invalid
- **Invalid Capacity**: Return 400 Bad Request when capacity is negative or zero
- **Non-existent References**: Return 404 Not Found when referencing non-existent users or events

### Business Logic Errors
- **Event Full**: Return 409 Conflict when attempting to register for a full event without a waitlist
- **Already Registered**: Return 409 Conflict when attempting to register for an event the user is already registered for
- **Not Registered**: Return 404 Not Found when attempting to unregister from an event the user is not registered for

### Error Response Format
```json
{
  "error": "error_code",
  "message": "Human-readable error message",
  "details": {}
}
```

## Testing Strategy

The testing strategy employs both unit tests and property-based tests to ensure comprehensive coverage.

### Unit Testing

Unit tests will verify specific examples and edge cases:

- **User Creation**: Test creating users with valid data, duplicate IDs, and missing fields
- **Event Creation**: Test creating events with various capacity values and waitlist configurations
- **Registration Flow**: Test the complete flow of registering, checking status, and unregistering
- **Waitlist Promotion**: Test specific scenarios of waitlist promotion with known sequences
- **Error Cases**: Test all error conditions with specific invalid inputs

### Property-Based Testing

Property-based tests will verify universal properties across randomly generated inputs using **Hypothesis** (Python's property-based testing library).

**Configuration**:
- Each property test should run a minimum of 100 iterations
- Tests should use Hypothesis strategies to generate valid users, events, and registration sequences
- Each property test must include a comment tag referencing the correctness property from this design document

**Tagging Format**:
```python
# Feature: user-registration, Property 1: User creation preserves attributes
@given(user_id=text(), name=text())
def test_user_creation_preserves_attributes(user_id, name):
    ...
```

**Property Test Coverage**:
- Property 1: Generate random userIds and names, verify created users have correct attributes
- Property 2: Generate random registration sequences, verify capacity is never exceeded
- Property 3: Generate full events with waitlists, verify overflow goes to waitlist
- Property 4: Generate full events without waitlists, verify overflow is rejected
- Property 5: Generate random users and events, verify registrations create bidirectional associations
- Property 6: Generate random registrations, attempt duplicate registration, verify rejection
- Property 7: Generate random registrations, unregister, verify complete removal
- Property 8: Generate events with waitlists, verify automatic promotion on unregistration
- Property 9: Generate random waitlists, remove users, verify order preservation
- Property 10: Generate users with multiple registrations, verify query completeness
- Property 11: Generate users with waitlist entries, verify exclusion from registered events
- Property 12: Generate random waitlists, verify position accuracy

**Test Generators**:
- `valid_user_id()`: Generates non-empty strings for user IDs
- `valid_name()`: Generates non-empty strings for names
- `valid_capacity()`: Generates positive integers for event capacity
- `registration_sequence()`: Generates sequences of register/unregister operations
- `waitlist_scenario()`: Generates events with waitlists and multiple users

### Integration Testing

Integration tests will verify the complete system behavior:
- API endpoint integration with service layer
- End-to-end registration flows through the API
- Concurrent registration handling (if applicable)

## Implementation Notes

### Concurrency Considerations

While the initial implementation uses in-memory storage with synchronous processing, future enhancements should consider:
- Thread-safe data structures for concurrent access
- Optimistic locking for registration operations
- Transaction boundaries for atomic waitlist promotion

### Scalability Considerations

For production deployment:
- Replace in-memory storage with a persistent database (PostgreSQL, DynamoDB)
- Implement caching for frequently accessed events
- Consider event sourcing for audit trail of registration changes
- Add pagination for large result sets

### Extensibility Points

The design allows for future enhancements:
- Event metadata (date, location, description)
- User profiles with additional attributes
- Notification system for waitlist promotions
- Priority waitlists based on user attributes
- Batch registration operations
