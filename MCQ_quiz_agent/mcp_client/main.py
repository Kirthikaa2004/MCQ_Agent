from fastapi import FastAPI
from fastapi.responses import JSONResponse
from src.migrations.create_tables import create_tables
from src.routers.router import router
from src.utils.custom_app_exception import CustomAppException
from contextlib import asynccontextmanager
from src.repositories.database import Database
from src.utils.helper import logger

@asynccontextmanager
async def lifespan(app:FastAPI):
    try:
        db = Database()
        await create_tables(db.engine)
        logger.info("----- Tables Created Successfully -----")
        yield

        logger.info("Shutting down: Closing Pool...")
    except Exception as e:
        logger.info(f"Error in lifespan: {str(e)}")

app = FastAPI(
    title="TuteAI - AI Homework Tutor Agent",
    description="Multi Agent Chatbot that uses agents as tools that helps as companion for students",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(router)


@app.exception_handler(CustomAppException)
async def custom_app_exception_handler(request, exc: CustomAppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "message": exc.message,
            "status_code": exc.status_code,
            "err_code": exc.err_code,
        },
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)

