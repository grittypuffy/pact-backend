from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from ..helpers import singleton

load_dotenv()


@singleton.singleton
class EnvVarConfig(BaseSettings):
    environment: str
    cookie_domain: str
    api_domain: str
    frontend_url: str
    mongodb_uri: str
    mongodb_db_name: str
    jwt_secret: str

    azure_subscription_id: str
    azure_client_id: str
    azure_tenant_id: str
    azure_client_secret: str

    azure_ai_project_name: str
    azure_rg_name: str
    azure_ai_endpoint: str
    azure_language_api_key: str
    azure_language_endpoint: str

    # Azure OpenAI configuration
    azure_openai_api_key: str
    azure_openai_endpoint: str
    azure_openai_deployment: str
    azure_openai_api_version: str
    azure_openai_model_name: str    

    # Azure speech to text
    azure_stt_key: str
    azure_stt_region: str
    
    # Temporary file uploads
    tmp_upload_dir: str

    # Azure blob storage
    uploads_container: str = "uploads"
    st_connection_string: str

    # Anonymous usage
    anonymous_user_id: str

    class EnvVarConfig:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_env_config():
    return EnvVarConfig()
