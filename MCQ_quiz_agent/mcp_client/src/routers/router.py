from fastapi import APIRouter,Depends
from src.services.tutor_service import TutorService,get_tutor_service
from src.models.user_model import RequestModel
from src.utils.custom_app_exception import CustomAppException
from src.repositories.error_repository import ErrorRepository,get_err_repo
from fastapi import Request
from fastapi.responses import JSONResponse
from src.utils.helper import logger

router = APIRouter(prefix="/api")

@router.post("/chat")
async def generate_quiz(request:RequestModel,err_repo:ErrorRepository = Depends(get_err_repo),service:TutorService = Depends(get_tutor_service)):
    try:
        logger.info('generate_quiz triggered....')
        response = await service.tutor_service(message=request.user_query,user_id = request.user_id,session_id=request.session_id,err_repo=err_repo)

        return JSONResponse(
            content = response.model_dump(),
            status_code=200
        )
    except CustomAppException:
        raise
    except Exception as e:
        
        await err_repo.add_error(
            file_name="router.py",
            function_name="generate_quiz",
            message=f"Router err at generate_quiz : {str(e)}"
        )
        raise CustomAppException(
            message=f"Router err at generate_quiz : {str(e)}",
            status_code=500,
            err_code="ROUTER_ERR"
        )
    
    
@router.get("/users/{user_id}")
async def get_user(user_id:str,err_repo:ErrorRepository = Depends(get_err_repo),service:TutorService = Depends(get_tutor_service)):
    try:
        logger.info('generate_quiz triggered....')
        response = await service.get_user(user_id = user_id,err_repo=err_repo)

        return JSONResponse(
            content = response.model_dump(),
            status_code=200
        )
    except CustomAppException:
        raise
    except Exception as e:
        
        await err_repo.add_error(
            file_name="router.py",
            function_name="get_user",
            message=f"Router err at get_user : {str(e)}"
        )
        raise CustomAppException(
            message=f"Router err at generate_quiz : {str(e)}",
            status_code=500,
            err_code="ROUTER_ERR"
        )
    
