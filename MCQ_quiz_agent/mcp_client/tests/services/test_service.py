import pytest
from unittest.mock import AsyncMock, MagicMock
from src.services.tutor_service import TutorService # Adjust import
from src.utils.custom_app_exception import CustomAppException # Adjust import

@pytest.fixture
def service_setup():
    """Setup mocks for repo and service."""
    mock_user_repo = AsyncMock()
    mock_err_repo = AsyncMock()
    # Assuming the service takes repo as an init argument

    mock_orchestration_service = AsyncMock()
    service = TutorService(service = mock_orchestration_service,user_repo=mock_user_repo)
    return service, mock_user_repo, mock_err_repo

@pytest.mark.asyncio
async def test_get_user_success(service_setup):
    service, mock_repo, mock_err = service_setup
    
    # 1. Setup: Mock repository returning a valid user object
    mock_user = MagicMock()
    mock_user.username = "johndoe"
    mock_user.user_id = "uuid-123"
    mock_repo.check_user.return_value = mock_user

    # 2. Act
    response = await service.get_user(user_id="uuid-123", err_repo=mock_err)

    # 3. Assert
    assert response.status_code == 200
    assert response.data["user_name"] == "johndoe"
    assert response.data["user_id"] == "uuid-123"
    mock_repo.check_user.assert_called_once_with(user_id="uuid-123", err_repo=mock_err)

@pytest.mark.asyncio
async def test_get_user_not_found(service_setup):
    service, mock_repo, mock_err = service_setup
    
    # 1. Setup: Mock repository returning None
    mock_repo.check_user.return_value = None

    # 2. Act & Assert
    with pytest.raises(CustomAppException) as exc:
        await service.get_user(user_id="wrong-id", err_repo=mock_err)
    
    assert exc.value.status_code == 404
    assert exc.value.err_code == "USER_NOT_FOUND"

@pytest.mark.asyncio
async def test_get_user_internal_error(service_setup):
    service, mock_repo, mock_err = service_setup
    
    # 1. Setup: Mock repository raising an unexpected Exception
    mock_repo.check_user.side_effect = Exception("DB Connection Lost")

    # 2. Act & Assert
    with pytest.raises(CustomAppException) as exc:
        await service.get_user(user_id="uuid-123", err_repo=mock_err)
    
    assert exc.value.status_code == 500
    assert exc.value.err_code == "SERVICE_ERR"
    
    # Verify the error was logged to err_repo
    mock_err.add_error.assert_called_once()
