import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from main import app  # Adjust based on your actual entry point

@pytest.fixture
def mock_setup():
    """
    Provides clean mocks for the Service and Error Repo.
    Scope is 'function' by default so mocks reset every test.
    """
    mock_service = AsyncMock()
    mock_err_repo = AsyncMock()
    return mock_service, mock_err_repo

@pytest.fixture
def client():
    """
    Provides a FastAPI TestClient.
    Using 'with' ensures the app startup/shutdown events run if defined.
    """
    with TestClient(app) as c:
        yield c
