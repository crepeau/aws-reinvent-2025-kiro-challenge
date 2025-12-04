# Implementation Plan

- [ ] 1. Set up project structure and testing framework
  - Create directory structure for models, services, repositories, and API components
  - Install and configure Hypothesis for property-based testing
  - Set up pytest as the test runner
  - Create base test utilities and fixtures
  - _Requirements: All_

- [ ] 2. Implement domain models
  - [ ] 2.1 Create User model
    - Define User class with user_id and name attributes
    - Implement validation for required fields
    - _Requirements: 1.1, 1.3_
  
  - [ ]* 2.2 Write property test for User creation
    - **Property 1: User creation preserves attributes**
    - **Validates: Requirements 1.1**
  
  - [ ] 2.3 Create Event model
    - Define Event class with event_id, name, capacity, has_waitlist attributes
    - Initialize empty registrations and waitlist lists
    - Implement validation for capacity values
    - _Requirements: 2.1, 2.2, 2.3, 2.4_
  
  - [ ] 2.4 Create Registration model
    - Define Registration class with user_id, event_id, and status
    - Define RegistrationStatus enum (REGISTERED, WAITLISTED)
    - _Requirements: 3.1, 3.3_

- [ ] 3. Implement repository layer
  - [ ] 3.1 Create UserRepository
    - Implement in-memory storage for users (Dict[str, User])
    - Implement create_user method with duplicate checking
    - Implement get_user method
    - _Requirements: 1.1, 1.2_
  
  - [ ] 3.2 Create EventRepository
    - Implement in-memory storage for events (Dict[str, Event])
    - Implement create_event method
    - Implement get_event method
    - _Requirements: 2.1, 2.2, 2.3_
  
  - [ ] 3.3 Create RegistrationRepository
    - Implement in-memory storage for user-to-events mapping
    - Implement methods to add/remove registrations
    - Implement query methods for user registrations
    - _Requirements: 3.1, 4.1, 5.1_

- [ ] 4. Implement core registration service
  - [ ] 4.1 Create RegistrationService with basic registration logic
    - Implement register_user method with capacity checking
    - Handle registration for events with available capacity
    - Return appropriate success/error responses
    - _Requirements: 3.1_
  
  - [ ]* 4.2 Write property test for successful registration
    - **Property 5: Successful registration creates association**
    - **Validates: Requirements 3.1**
  
  - [ ]* 4.3 Write property test for capacity enforcement
    - **Property 2: Capacity is never exceeded**
    - **Validates: Requirements 2.1, 7.1**
  
  - [ ] 4.4 Add duplicate registration prevention
    - Check if user is already registered before creating registration
    - Return error for duplicate registration attempts
    - _Requirements: 3.4_
  
  - [ ]* 4.5 Write property test for registration idempotence
    - **Property 6: Registration is idempotent**
    - **Validates: Requirements 3.4**

- [ ] 5. Implement waitlist functionality
  - [ ] 5.1 Add waitlist logic to registration service
    - Check if event has waitlist enabled when at capacity
    - Add user to waitlist for full events with waitlist enabled
    - Reject registration for full events without waitlist
    - _Requirements: 2.2, 2.3, 3.2, 3.3_
  
  - [ ]* 5.2 Write property test for waitlist overflow
    - **Property 3: Waitlist enables overflow registration**
    - **Validates: Requirements 2.2, 3.3**
  
  - [ ]* 5.3 Write property test for non-waitlist rejection
    - **Property 4: Events without waitlists reject overflow**
    - **Validates: Requirements 2.3**
  
  - [ ] 5.4 Implement get_waitlist_position method
    - Query user's position in event waitlist
    - Return None if user is not on waitlist
    - Return 1-indexed position
    - _Requirements: 6.1, 6.2_
  
  - [ ]* 5.5 Write property test for waitlist position accuracy
    - **Property 12: Waitlist position is accurate**
    - **Validates: Requirements 6.1**

- [ ] 6. Implement unregistration and waitlist promotion
  - [ ] 6.1 Implement unregister_user method
    - Remove user from event registrations
    - Decrease registered count
    - Validate user is actually registered
    - _Requirements: 4.1, 4.4_
  
  - [ ]* 6.2 Write property test for unregistration
    - **Property 7: Unregistration removes association**
    - **Validates: Requirements 4.1**
  
  - [ ] 6.3 Add automatic waitlist promotion
    - Check for waitlisted users after unregistration
    - Promote first waitlisted user to registered status
    - Remove promoted user from waitlist
    - Ensure atomic operation
    - _Requirements: 4.2, 6.3, 7.4_
  
  - [ ]* 6.4 Write property test for waitlist promotion
    - **Property 8: Waitlist promotion is automatic**
    - **Validates: Requirements 4.2, 6.3, 7.4**
  
  - [ ] 6.5 Implement waitlist removal for unregistering waitlisted users
    - Remove user from waitlist if they unregister while waitlisted
    - Maintain order of remaining users
    - _Requirements: 4.3, 7.2_
  
  - [ ]* 6.6 Write property test for waitlist order preservation
    - **Property 9: Waitlist order is preserved**
    - **Validates: Requirements 4.3, 7.2**

- [ ] 7. Implement user registration queries
  - [ ] 7.1 Implement get_user_registrations method
    - Query all events where user has active registration
    - Exclude events where user is only waitlisted
    - Return empty list for users with no registrations
    - _Requirements: 5.1, 5.2, 5.3_
  
  - [ ]* 7.2 Write property test for registration query completeness
    - **Property 10: User registrations query is complete**
    - **Validates: Requirements 5.1**
  
  - [ ]* 7.3 Write property test for waitlist exclusion
    - **Property 11: Waitlisted events are excluded from registrations**
    - **Validates: Requirements 5.2**

- [ ] 8. Implement API layer
  - [ ] 8.1 Create FastAPI application structure
    - Set up FastAPI app with CORS and error handling
    - Define request/response models using Pydantic
    - Configure API routing
    - _Requirements: All_
  
  - [ ] 8.2 Implement user endpoints
    - POST /users - Create user endpoint
    - GET /users/{user_id} - Get user endpoint
    - Add input validation and error handling
    - _Requirements: 1.1, 1.2, 1.3_
  
  - [ ] 8.3 Implement event endpoints
    - POST /events - Create event endpoint
    - GET /events/{event_id} - Get event endpoint
    - Add input validation and error handling
    - _Requirements: 2.1, 2.2, 2.3, 2.4_
  
  - [ ] 8.4 Implement registration endpoints
    - POST /events/{event_id}/register - Register user endpoint
    - DELETE /events/{event_id}/register/{user_id} - Unregister endpoint
    - GET /users/{user_id}/events - List user registrations endpoint
    - GET /events/{event_id}/waitlist/{user_id} - Get waitlist position endpoint
    - Add comprehensive error handling for all business logic errors
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3, 4.4, 5.1, 5.2, 5.3, 5.4, 6.1, 6.2_

- [ ]* 9. Write integration tests
  - Test complete registration flows through API endpoints
  - Test error handling across all endpoints
  - Test waitlist promotion through API
  - _Requirements: All_

- [ ] 10. Add API documentation
  - Generate OpenAPI/Swagger documentation
  - Add endpoint descriptions and examples
  - Document error responses
  - _Requirements: All_

- [ ] 11. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
