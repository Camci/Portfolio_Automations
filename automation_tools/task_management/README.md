# Task Management System

A comprehensive task management system with an admin dashboard for tracking, assigning, and managing team tasks.

## Features

### Admin Dashboard

- **User Management**:
  - Integration with AWS Cognito for secure user authentication
  - Role-based access control for administrators and team members
  - User lookup and selection from centralized user pool

- **Task Management**:
  - Create, assign, and track tasks with deadlines
  - Break down tasks into subtasks with individual due dates
  - Real-time status updates and completion tracking
  - Task filtering and sorting capabilities

- **Interface**:
  - Clean, intuitive web interface built with PySimpleGUI
  - Responsive design that works on various screen sizes
  - Task list with clear visual indicators of status and priority

### API Integration

- RESTful API integration for task data storage and retrieval
- Automatic caching to improve performance and reduce API calls
- Error handling with graceful degradation when network issues occur

## Setup

1. Configure your AWS Cognito credentials in the settings:
   - User Pool ID
   - Region

2. Set up the API endpoint:
   - Base URL
   - Authentication tokens

3. Run the dashboard:
```bash
python admin_dashboard.py
```

## Requirements

```
boto3>=1.20.0
requests>=2.25.0
PySimpleGUI>=4.45.0
```

## Security Features

- Secure authentication through AWS Cognito
- No hard-coded credentials in the codebase
- Session-based access with automatic timeout
- Input validation to prevent injection attacks

## Extensibility

The system is designed to be easily extended with:
- Additional user interface components
- New task types and categories
- Custom reporting and analytics
- Integration with other project management tools

## Notes

- The admin dashboard requires an active internet connection to communicate with the API and AWS Cognito
- First-time startup may be slower due to initial data loading
- Cached data is stored in a local JSON file for improved performance 