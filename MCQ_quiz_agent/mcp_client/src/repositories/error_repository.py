from src.repositories.database import get_database,Database
from src.repositories.schemas.user_schema import ErrLog
from src.utils.custom_app_exception import CustomAppException
from fastapi import Depends

class ErrorRepository:

    def __init__(self,db):
        self.db = db


    async def add_error(self,file_name:str,function_name:str,message:str)-> dict:
        try:

            async with self.db.get_session() as db_session:
                new_error = ErrLog(
                    filename=file_name,
                    function_name=function_name,
                    message=message
                )

                db_session.add(new_error)
                await db_session.commit()
                return new_error

        except CustomAppException:
            raise
        except Exception as e:
            raise CustomAppException(
                message=f"Failed to add error: {str(e)}",
                status_code=500,
                err_code="DB_INSERT_ERROR",
            )
    
def get_err_repo(db:Database = Depends(get_database)):
    return ErrorRepository(db)
