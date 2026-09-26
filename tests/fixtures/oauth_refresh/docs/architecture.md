# System Architecture

## Overview

This document describes the overall system architecture for the OAuth authentication service.

## Components

### Frontend
- React 18 with TypeScript
- Redux Toolkit for state management
- React Router for navigation

### Backend
- FastAPI (Python 3.12)
- PostgreSQL for persistence
- Redis for caching and token blacklist

### Infrastructure
- Docker containers orchestrated with Kubernetes
- NGINX ingress controller
- Prometheus + Grafana for monitoring

## Data Flow

```
User -> Frontend -> API Gateway -> Auth Service -> Database
                          -> Redis (cache/blacklist)
```

## Security

- All communication over TLS 1.3
- JWT tokens with HS256 signing
- Password hashing with Argon2
- Rate limiting on auth endpoints

## Deployment

- Blue-green deployments
- Health checks on /health endpoint
- Automated rollback on error rate spike