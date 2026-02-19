# Ahana DW Tool Frontend Documentation

## Table of Contents
1. [Introduction](#introduction)
2. [File Structure](#file-structure)
3. [Core Components](#core-components)
4. [Authentication & Authorization](#authentication--authorization)
5. [Routing & Navigation](#routing--navigation)
6. [UI Framework & Styling](#ui-framework--styling)
7. [Modules](#modules)
8. [State Management](#state-management)
9. [API Integration](#api-integration)
10. [Configuration](#configuration)
11. [Key Features](#key-features)

## Introduction

The Ahana DW Tool frontend is a Next.js-based application that provides a modern, responsive user interface for managing data warehouse operations. It features a comprehensive set of modules for user authentication, license management, data mapping, job scheduling, and dashboard analytics.

The application is built using React with Next.js framework, utilizing modern UI libraries like Material-UI, Framer Motion for animations, and Tailwind CSS for styling. It communicates with the backend API to perform operations on the data warehouse.

## File Structure

```
frontend/
├── src/                    # Source code
│   ├── app/                # Next.js app directory (pages and routing)
│   │   ├── admin/          # Admin module
│   │   ├── auth/           # Authentication pages
│   │   ├── dashboard/      # Dashboard module
│   │   ├── home/           # Home page
│   │   ├── jobs/           # Jobs management module
│   │   ├── job_status_and_logs/ # Job status and logs module
│   │   ├── manage_sql/     # SQL management module
│   │   ├── mapper_module/  # Mapper module
│   │   ├── profile/        # User profile module
│   │   ├── type_mapper/    # Parameters module
│   │   ├── api/            # API routes
│   │   ├── context/        # React context providers
│   │   ├── components/     # Shared components
│   │   ├── config.js       # Configuration file
│   │   ├── globals.css     # Global styles
│   │   └── layout.js       # Root layout component
│   ├── components/         # Global components
│   │   ├── LayoutWrapper.js # Main layout wrapper
│   │   ├── LicenseCheck.jsx # License validation component
│   │   ├── NavBar.js       # Navigation bar component
│   │   ├── Sidebar.js      # Sidebar navigation component
│   │   └── Notification.js # Notification component
│   ├── context/            # Global context providers
│   │   └── ThemeContext.js # Theme context provider
│   ├── hooks/              # Custom React hooks
│   │   ├── useClickOutside.js # Hook for detecting clicks outside elements
│   │   └── useJobLogs.js   # Hook for job logs functionality
│   ├── middleware.js       # Next.js middleware
│   └── styles/             # Global styles
├── public/                 # Static assets
├── package.json            # Dependencies and scripts
└── next.config.js          # Next.js configuration
```

## Core Components

### Layout Components

#### LayoutWrapper.js

The main layout wrapper that provides the structure for the application, including the sidebar, navbar, and content area.

Key features:
- Responsive layout with collapsible sidebar
- Theme integration (light/dark mode)
- License validation check
- Notification system

#### Sidebar.js

Navigation sidebar component that provides access to all modules of the application.

Key features:
- Collapsible design
- Animated navigation items
- Active state indication
- Responsive design

#### NavBar.js

Top navigation bar component that provides user information, theme toggle, and other global actions.

### Authentication Components

#### LicenseValidation.jsx

Component that checks the license status of the application and restricts access if the license is invalid.

#### ProtectedRoute.js

Higher-order component that protects routes from unauthorized access.

## Authentication & Authorization

### AuthContext.js

Provides authentication state and methods throughout the application.

Key features:
- User login/logout functionality
- Token management
- User profile management
- Password change functionality
- Session timeout handling
- License status checking

Authentication flow:
1. User logs in through the login page
2. Credentials are validated by the backend API
3. JWT token is stored in localStorage and cookies
4. User information is stored in context and localStorage
5. Protected routes check for valid authentication
6. Automatic logout on session timeout

## Routing & Navigation

The application uses Next.js App Router for navigation, with the following main routes:

- `/auth/*` - Authentication routes (login, forgot password, reset password)
- `/home` - Home page
- `/admin` - Admin module
- `/mapper_module` - Mapper module
- `/jobs` - Jobs management
- `/job_status_and_logs` - Job status and logs
- `/dashboard` - Analytics dashboard
- `/manage_sql` - SQL management
- `/type_mapper` - Parameters
- `/profile` - User profile

## UI Framework & Styling

The application uses a combination of:

- Tailwind CSS for utility-based styling
- Material-UI (MUI) components for complex UI elements
- Framer Motion for animations
- Custom CSS for specific styling needs
- Theme support with light and dark modes

## Modules

### Admin Module

Provides administrative functions for managing users, roles, and system settings.

Key components:
- User management (create, edit, delete users)
- Role management (create, edit, delete roles)
- License management
- System notifications

### Mapper Module

Allows users to create and manage data mapping configurations.

Key features:
- Reference table management
- Mapping configuration
- Template download/upload
- Logic validation
- Concurrent editing prevention with locking mechanism

### Jobs Module

Manages job creation, scheduling, and execution.

Key features:
- Job creation from mappings
- Job scheduling (immediate, regular, historical)
- Job dependency configuration
- Job execution monitoring

### Dashboard Module

Provides analytics and metrics for the application.

Key components:
- MetricsCards - Display key metrics
- JobsAverageRunDurationChart - Chart for job run duration
- JobsExecutionDurationChart - Chart for job execution duration
- JobsProcessedRowsChart - Chart for processed rows
- JobsSuccessFailChart - Chart for success/failure rates

### Job Status and Logs Module

Displays job execution logs and status information.

Key features:
- Log filtering and searching
- Error details viewing
- Job status monitoring
- Job stopping functionality

## State Management

The application uses React Context API for global state management:

- AuthContext - Authentication state
- ThemeContext - Theme preferences

Local component state is managed using React's useState and useEffect hooks.

## API Integration

API calls are made using Axios for HTTP requests. The base URL is configured in `config.js`.

Key API integration points:
- Authentication API for user login/logout
- License API for license validation
- Mapper API for mapping configuration
- Jobs API for job management
- Dashboard API for analytics data

## Configuration

Configuration is managed through environment variables and the `config.js` file:

- API_BASE_URL - Base URL for API requests
- ENABLE_RECAPTCHA - Toggle for reCAPTCHA functionality
- RECAPTCHA_SITE_KEY - Google reCAPTCHA site key

## Key Features

### Responsive Design

The application is designed to work on various screen sizes, with responsive components that adapt to different viewport dimensions.

### Theme Support

The application supports both light and dark themes, with a smooth transition between them.

### Animation

Framer Motion is used for smooth animations throughout the application, enhancing the user experience.

### Concurrent Editing Prevention

The mapper module implements a locking mechanism to prevent concurrent editing of the same reference by multiple users.

### Session Management

The application includes features for session timeout detection and automatic logout after a period of inactivity.

### License Validation

The application validates the license status and restricts access to features based on the license.

### Error Handling

Comprehensive error handling is implemented throughout the application, with user-friendly error messages and logging.
