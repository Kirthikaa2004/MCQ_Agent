from src.repositories.database import get_database,Database
from src.repositories.schemas.user_schema import UserThread,User
from src.utils.custom_app_exception import CustomAppException
from sqlalchemy import select
from src.repositories.error_repository import ErrorRepository,get_err_repo
from src.utils.helper import logger
from fastapi import Depends

class UserRepository:

    def __init__(self,db):
        self.db = db

    async def check_user(self,user_id:str,err_repo:ErrorRepository)-> User:
        try:

            logger.info("check_user function is triggered ...")
            async with self.db.get_session() as db_session:
            

                query = select(User).where(User.user_id == user_id).where(User.is_active == True)

                result = await db_session.execute(query)

                user = result.scalars().first()

                return user

        except CustomAppException:
            raise
        except Exception as e:
            await err_repo.add_error(
                file_name="coding_repository",
                function_name="check_user",
                message=f"Failed to check user: {str(e)}"
            )
            logger.info("Error in check_user ...")
            raise CustomAppException(
                message=f"Failed to check user: {str(e)}",
                status_code=500,
                err_code="DB_QUERY_ERROR",
            )
        
    async def add_user_thread(self,user_id:str,thread_id:str,err_repo:ErrorRepository)-> User:
        try:
            logger.info("add_user_thread function is triggered ...")
            async with self.db.get_session() as db_session:


                new_user_thread = UserThread(
                    user_id = user_id,
                    thread_id = thread_id
                )

                db_session.add(new_user_thread)
                await db_session.commit()

                await db_session.refresh(new_user_thread)


                return new_user_thread

        except CustomAppException:
            raise
        except Exception as e:
            await err_repo.add_error(
                file_name="coding_repository",
                function_name="add_user_thread",
                message=f"Failed to add user thread: {str(e)}"
            )
            logger.info("Error in add_user_thread ...")
            raise CustomAppException(
                message=f"Failed to add user thread: {str(e)}",
                status_code=500,
                err_code="DB_INSERT_ERROR",
            )

    
    async def check_thread(self,user_id:str,thread_id:str,err_repo:ErrorRepository):
        try:
            logger.info("check_thread function is triggered ...")
            async with self.db.get_session() as db_session:

                query = (
    select(UserThread)
    .where(
        UserThread.user_id == user_id,
        UserThread.thread_id == thread_id,
        UserThread.is_active == True
    )

)
                print(query,'query')
                results = await db_session.execute(query)
                
                user_thread = results.scalar_one_or_none()

                return user_thread
        except CustomAppException:
            raise
        except Exception as e:
            await err_repo.add_error(
                file_name="coding_repository",
                function_name="check_thread",
                message=f"Failed to check thread: {str(e)}"
            )
            logger.info("Error in check_thread ...")
            raise CustomAppException(
                message=f"Failed to check thread: {str(e)}",
                status_code=500,
                err_code="DB_QUERY_ERROR",
            )
        
        
def get_user_repo(db:Database = Depends(get_database)):
    return UserRepository(db)
