from langchain_aws import ChatBedrock
from settings import config
from src.utils.custom_app_exception import CustomAppException


async def get_llm(err_repo,max_tokens: int = None, temperature: float = None):
            try:
                logger.info("get_llm is triggered...")
                max_tokens = max_tokens or 3000
                temperature = temperature or 0

                llm = ChatBedrock(
                    model=config.model_id,
                    region_name=config.region,
                    provider=config.provider,
                    max_tokens=max_tokens,
                    temperature=temperature
                )

                return llm
            except CustomAppException:
                   raise
            except Exception as e:
                logger.info("Error in initialising LLM Client ...")
                await err_repo.add_error(
                       function_name="get_llm",
                       file_name="helper",
                       message=f"Failed to initialise LLM client: {str(e)}"
                )
                raise CustomAppException(
                    message=f"Failed to initialise LLM client: {str(e)}",
                    status_code=500,
                    err_code="LLM_INIT_ERROR",
                )
            
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


