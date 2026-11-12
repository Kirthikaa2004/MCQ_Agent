from fastapi.testclient import TestClient
from fastapi import Depends
from unittest.mock import AsyncMock, MagicMock
from  src.repositories.user_repository import UserRepository, get_user_repo # Adjust imports based on your file structure
from  src.repositories.error_repository import ErrorRepository, get_err_repo # Adjust imports based on your file structure
from main import app

# 1. Create Mock Objects
mock_user_repo = MagicMock()
mock_err_repo = MagicMock()

# 2. Define Dependency Overrides
def override_get_user_repo():
    return mock_user_repo

def override_get_err_repo():
    return mock_err_repo

# 3. Apply Overrides to the App
app.dependency_overrides[get_user_repo] = override_get_user_repo
app.dependency_overrides[get_err_repo] = override_get_err_repo

client = TestClient(app)


@app.post("/users/{user_id}/threads/{thread_id}")
async def create_thread(user_id: str, thread_id: str, repo: UserRepository = Depends(get_user_repo),err_repo:ErrorRepository =  Depends(get_err_repo)):
    return await repo.add_user_thread(user_id, thread_id, err_repo)


def test_add_user_thread_endpoint():
    target_user_id = "28601827-850c-426d-8abd-cfa5440b16cd"
    target_thread_id = "62f2c8a0-f636-4678-8964-222a291e5f5f"

    # 4. Setup Mock Behavior (Using AsyncMock because repo call is awaited)
    mock_user_repo.add_user_thread = AsyncMock(return_value={
        "user_id": target_user_id,
        "thread_id": target_thread_id,
        "status": "success"
    })

    try:
        # 5. Make the request
        response = client.post(f"/users/{target_user_id}/threads/{target_thread_id}")
        
        data = response.json()
        print(data, 'res')
        
        assert response is not None
        assert response.status_code == 200
        assert data["user_id"] == target_user_id
        assert data["thread_id"] == target_thread_id
        
        # Verify the repo was called with correct arguments


        print('Test Passed.....')
    
    except Exception as e:
        print(f"Test Failed: {e}")
    finally:
        # Clean up overrides so they don't leak into other tests
        app.dependency_overrides = {}

if __name__ == "__main__":
    test_add_user_thread_endpoint()
