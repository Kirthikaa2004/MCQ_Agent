from fastapi import Depends
from src.repositories.user_repository import UserRepository,get_user_repo
from src.repositories.error_repository import ErrorRepository,get_err_repo
from src.utils.custom_app_exception import CustomAppException
from src.services.orchestration_service import get_orchestrator_service,OrchestratorService
from fastapi import Depends
from src.utils.helper import logger
import re
from src.models.user_model import APIResponse,QuizToolResponse
import uuid
import json


class TutorService:
    def __init__(self,service,user_repo):
        self.orchestration_service = service 
        self.user_repo = user_repo
        

    async def tutor_service(self,message:str,user_id:str,session_id : str,err_repo:ErrorRepository):
        try:
            
          
            logger.info("tutor_service triggered successfully...")
            user = await self.user_repo.check_user(user_id=user_id,err_repo=err_repo)
            print(user.username)
            if not user:
                logger.info("user not found...")
                raise CustomAppException(
                    message=f"User Not Found ",
                    status_code=404,
                    err_code="USER_NOT_FOUND"
                )
            

            if message == "":
                logger.info("user message not found...")
                raise CustomAppException(
                    message=f"User Message not  Found ",
                    status_code=404,
                    err_code="QUERY_NOT_FOUND"
                )

            user_thread = await self.user_repo.check_thread(user_id=user_id,thread_id=session_id,err_repo=err_repo)
            print(user_thread,'user thread')
            if not user_thread:
                logger.info("creating new session id....")
                session_id = uuid.uuid4()
                await self.user_repo.add_user_thread(user_id = user_id,thread_id = session_id,err_repo=err_repo)
            
            agent_response = await self.orchestration_service.run_agent(user_prompt = message,thread_id = session_id,err_repo = err_repo)

            print(agent_response,'agent')
            # print(agent_response,'tutor response' ,type(agent_response),'type')
            

            # if not isinstance(agent_response,QuizToolResponse):
            #     print('in in')
            #     match = re.search(r'<thinking>(.*?)</thinking>', agent_response, flags=re.DOTALL)
            #     if match:
            #         agent_response = match.group(1).strip()
    
            
            return APIResponse(
                data = agent_response ,
                message="Response generated Successfully",
                status_code=200
            )
        
            
        except CustomAppException:
            raise
        except Exception as e:
            logger.info("err raised at tutor_service...")
            await err_repo.add_error(
                file_name="tutor_service",
                function_name="tutor_service",
                message=f"Service err at TutorService: {str(e)}"
            )

            raise CustomAppException(
                 message=f"Service err at TutorService: {str(e)}",
                 status_code=500,
                 err_code="SERVICE_ERR"
            )
        

    async def get_user(self,user_id:str,err_repo:ErrorRepository):
        try:
            user = await self.user_repo.check_user(user_id=user_id,err_repo=err_repo)

            if not user:
                logger.info("user not found...")
                raise CustomAppException(
                    message=f"User Not Found ",
                    status_code=404,
                    err_code="USER_NOT_FOUND"
                )
            
            user_details = {
                "user_name":user.username,
                "user_id":str(user.user_id)

            }
            return APIResponse(
                data=user_details,
                message = "User details fetched successfully",
                status_code=200

            )
        except CustomAppException:
            raise
        except Exception as e:
            logger.info("err raised at get_user...")
            await err_repo.add_error(
                file_name="tutor_service",
                function_name="add_thread",
                message=f"Service err at TutorService: {str(e)}"
            )

            raise CustomAppException(
                 message=f"Service err at TutorService: {str(e)}",
                 status_code=500,
                 err_code="SERVICE_ERR"
            )

def get_tutor_service(service:OrchestratorService = Depends(get_orchestrator_service),user_repo:UserRepository = Depends(get_user_repo)):
    return TutorService(service,user_repo)