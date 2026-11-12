import os
from dotenv import load_dotenv
from dataclasses import dataclass


load_dotenv()

@dataclass
class Settings:

    region: str | None
    aws_access_key_id: str |None
    aws_secret_access_key: str |None
    model_id:str |None
    db_name: str
    db_host: str
    db_port: str
    db_username: str
    db_password: str
    provider:str
    pep8_server_url:str
    duckduckgo_mcp_server_url:str




def get_settings() -> Settings:
    
    return Settings(

        region=os.getenv("REGION"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        model_id = os.getenv("MODEL_ID",""),
        db_name=os.getenv("DB_NAME", "bean_and_brew"),
        db_host=os.getenv("DB_HOST", "localhost"),
        db_port=os.getenv("DB_PORT", "5432"),
        db_username=os.getenv("DB_USERNAME", "postgres"),
        db_password=os.getenv("DB_PASSWORD", "password"),
        provider=os.getenv("PROVIDER","amazon"),
        duckduckgo_mcp_server_url=os.getenv("DUCKDUCKGO_MCP_SERVER_URL",""),
        pep8_server_url=os.getenv("PEP8_MCP_SERVER_URL","")


    )

config = get_settings()
