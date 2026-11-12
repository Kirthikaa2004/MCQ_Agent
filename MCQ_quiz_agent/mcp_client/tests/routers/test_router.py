import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import status
from main import app
from src.services.tutor_service import get_tutor_service
from src.repositories.error_repository import get_err_repo
from src.utils.custom_app_exception import CustomAppException

@pytest.fixture
def mock_setup():
    """Create mocks for service and error repo."""
    mock_service = AsyncMock()
    mock_err_repo = AsyncMock()
    return mock_service, mock_err_repo

def test_get_user_router_success(client, mock_setup):
    mock_service, mock_err = mock_setup
    
    # 1. Setup: Mock the service to return a successful response object
    # Assuming APIResponse has a .model_dump() method
    mock_response = MagicMock()
    mock_response.model_dump.return_value = {
        "data": {"user_name": "johndoe", "user_id": "uuid-123"},
        "message": "User details fetched successfully",
        "status_code": 200
    }
    mock_service.get_user.return_value = mock_response

    # 2. Inject: Override the dependencies
    app.dependency_overrides[get_tutor_service] = lambda: mock_service
    app.dependency_overrides[get_err_repo] = lambda: mock_err

    # 3. Act
    response = client.get("api/users/uuid-123")

    # 4. Assert
    assert response.status_code == 200
    assert response.json()["data"]["user_name"] == "johndoe"
    mock_service.get_user.assert_called_once()
    
    app.dependency_overrides.clear()

def test_get_user_router_exception(client, mock_setup):
    mock_service, mock_err = mock_setup
    
    # 1. Setup: Mock the service to raise a CustomAppException (e.g., 404)
    mock_service.get_user.side_effect = CustomAppException(
        message="User Not Found",
        status_code=404,
        err_code="USER_NOT_FOUND"
    )

    app.dependency_overrides[get_tutor_service] = lambda: mock_service
    app.dependency_overrides[get_err_repo] = lambda: mock_err

    # 2. Act
    response = client.get("/api/users/invalid_id")

    # 3. Assert

    print(response,'err_response')
    assert response.status_code == 404
    assert response.json()["err_code"] == "USER_NOT_FOUND"
    
    app.dependency_overrides.clear()

def test_get_user_router_server_error(client, mock_setup):
    mock_service, mock_err = mock_setup
    
    # 1. Setup: Mock a generic crash (Exception) to trigger the router's try-except
    mock_service.get_user.side_effect = Exception("Unexpected Crash")

    app.dependency_overrides[get_tutor_service] = lambda: mock_service
    app.dependency_overrides[get_err_repo] = lambda: mock_err

    # 2. Act
    response = client.get("api/users/uuid-123")

    # 3. Assert
    assert response.status_code == 500
    # Check if the error repo was called to log the router error
    mock_err.add_error.assert_called_once()
    assert "Router err" in response.json()["message"]
    
    app.dependency_overrides.clear()
