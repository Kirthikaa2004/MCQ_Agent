import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy import select
from src.repositories.schemas.user_schema import User  # Adjust import
from src.utils.custom_app_exception import CustomAppException # Adjust import
from src.repositories.user_repository import UserRepository

@pytest.fixture
def mock_db_manager():
    """Mocks the DB manager and the session it yields."""
    db_manager = MagicMock()
    mock_session = AsyncMock()
    
    # Mock the 'async with self.db.get_session() as db_session:' 
    db_manager.get_session.return_value.__aenter__.return_value = mock_session
    return db_manager, mock_session

@pytest.mark.asyncio
async def test_check_user_repo_success(mock_db_manager):
    db_manager, mock_session = mock_db_manager
    mock_err_repo = AsyncMock()
    
    # 1. Setup: Mock SQLAlchemy result chain
    fake_user = User(user_id="user_123", is_active=True, username="test_dev")
    mock_result = MagicMock()
    
    mock_session.execute.return_value = mock_result
    mock_result.scalars.return_value.first.return_value = fake_user

    # 2. Instantiate Repo (Assuming it takes db manager in __init__)
    repo = UserRepository(db=db_manager) 
    
    # 3. Act
    result = await repo.check_user(user_id="user_123", err_repo=mock_err_repo)

    # 4. Assert
    assert result.user_id == "user_123"
    assert result.is_active is True
    mock_session.execute.assert_called_once()

@pytest.mark.asyncio
async def test_check_user_repo_db_error(mock_db_manager):
    db_manager, mock_session = mock_db_manager
    mock_err_repo = AsyncMock()
    
    # 1. Setup: Force the execute call to crash
    mock_session.execute.side_effect = Exception("Connection Timeout")

    repo = UserRepository(db=db_manager)

    # 2. Act & Assert
    with pytest.raises(CustomAppException) as exc:
        await repo.check_user(user_id="user_123", err_repo=mock_err_repo)

    assert exc.value.status_code == 500
    assert exc.value.err_code == "DB_QUERY_ERROR"
    
    # 3. Verify error repository was notified
    mock_err_repo.add_error.assert_called_once_with(
        file_name="coding_repository",
        function_name="check_user",
        message="Failed to check user: Connection Timeout"
    )
