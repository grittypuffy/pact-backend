import logging

from azure.identity import DefaultAzureCredential
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential

from ..config import AppConfig, get_config
from ..helpers.singleton import singleton

config: AppConfig = get_config()

@singleton
class PreProcessor:
    def __init__(self):
        self.azure_ai_project = {
            "subscription_id": config.env.azure_subscription_id,
            "resource_group_name": config.env.azure_rg_name,
            "project_name": config.env.azure_ai_project_name,
        }
        self.endpoint = config.env.azure_ai_endpoint
        self.language_api_key = config.env.azure_language_api_key
        self.language_endpoint = config.env.azure_language_endpoint
        self.credential = DefaultAzureCredential()
        self.client = TextAnalyticsClient(endpoint=self.endpoint, credential=self.credential)

    def redact_sensitive_info(self, query: str):
        query=[query]
        credential = AzureKeyCredential(self.language_api_key)
        text_analytics_client = TextAnalyticsClient(endpoint=self.language_endpoint, credential=credential)
        try:
            response = text_analytics_client.recognize_entities(query)
            redacted_response = [doc for doc in response if not doc.is_error]
            if redacted_response:
                return redacted_response[0].redacted_text
        except Exception as e:
            logging.error(f"Error during redaction: {e}")
