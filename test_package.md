# Context Package: Debug refresh token 401
**Task ID:** test-001
**Compiled:** 2026-09-26T18:55:16.890990
**Estimated Tokens:** 405

## TASK
**Task:** Debug refresh token 401

**Task ID:** test-001
**Details:** Debug refresh token 401


## PROVENANCE
- user:developer (observed by developer, confidence 100%)
- file:tests\test_auth.py (observed by file_ingestion, confidence 100%)
- file:auth\endpoints.py (observed by file_ingestion, confidence 100%)
- file:auth\token.py (observed by file_ingestion, confidence 100%)
- file:tests\conftest.py (observed by file_ingestion, confidence 100%)
- file:tests\test_bugs.py (observed by file_ingestion, confidence 100%)


## RELEVANT FILES
- `tests\test_auth.py` — """Tests for authentication - BUG AUTH-001."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock

from auth.token i
- `auth\endpoints.py` — """Authentication endpoints."""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2Password
- `auth\token.py` — """JWT token handling for authentication - contains BUG AUTH-001."""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import jwt, JWTError
- `tests\conftest.py` — """Test configuration and fixtures."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import
- `tests\test_bugs.py` — """Tests for BUG INT-005: Pagination bug and CACHE-004: Stale permissions."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patc

