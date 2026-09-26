# Context Package: Debug OAuth refresh endpoint returning 401 for valid refresh tokens
**Task ID:** demo-auth-001
**Compiled:** 2026-09-26T11:25:05.302025
**Estimated Tokens:** 726

## TASK
**Task:** Debug OAuth refresh endpoint returning 401 for valid refresh tokens

**Task ID:** demo-auth-001
**Details:** Debug OAuth refresh endpoint returning 401 for valid refresh tokens


## PROVENANCE
- file:tests/test_auth.py (observed by file_ingestion, confidence 100%)
- user:developer (observed by developer, confidence 100%)
- file:auth/endpoints.py (observed by file_ingestion, confidence 100%)
- file:auth/token.py (observed by file_ingestion, confidence 100%)
- file:tasks/endpoints.py (observed by file_ingestion, confidence 100%)
- file:tasks/schemas.py (observed by file_ingestion, confidence 100%)
- file:tasks/service.py (observed by file_ingestion, confidence 100%)
- file:tests/conftest.py (observed by file_ingestion, confidence 100%)
- file:tests/test_api_bugs.py (observed by file_ingestion, confidence 100%)
- file:tests/test_bugs.py (observed by file_ingestion, confidence 100%)


## RELEVANT FILES
- `tests/test_auth.py` — """Tests for authentication - BUG AUTH-001."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock

from auth.token i
- `auth/endpoints.py` — """Authentication endpoints."""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2Password
- `auth/token.py` — """JWT token handling for authentication - contains BUG AUTH-001."""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import jwt, JWTError
- `tasks/endpoints.py` — """Task endpoints - contains BUG API-003."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc im
- `tasks/schemas.py` — """Pydantic schemas for tasks - contains BUG API-003."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, field_validator
from tasks.models import TaskP
- `tasks/service.py` — """Task service layer - contains BUG DB-002 and BUG INT-005."""

from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, 
- `tests/conftest.py` — """Test configuration and fixtures."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import
- `tests/test_api_bugs.py` — """Tests for BUG API-003: Invalid priority causes 500 instead of 422."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


class TestBugAPI003:
    """Tests
- `tests/test_bugs.py` — """Tests for BUG INT-005: Pagination bug and CACHE-004: Stale permissions."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patc

