import math
import concurrent.futures
import logging

from azure.ai.evaluation import (
    ViolenceEvaluator,
    SexualEvaluator,
    SelfHarmEvaluator,
    HateUnfairnessEvaluator,
    IndirectAttackEvaluator,
)
from azure.identity import DefaultAzureCredential
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential

from .response import BotHandler
from .preprocessor import PreProcessor
from ..config import AppConfig, get_config
from ..helpers.singleton import singleton

config: AppConfig = get_config()


@singleton
class Metrics:
    def __init__(self):
        """
        Initializes the Metrics class with Azure AI service credentials.
        """
        self.azure_ai_project = {
            "subscription_id": config.env.azure_subscription_id,
            "resource_group_name": config.env.azure_rg_name,
            "project_name": config.env.azure_ai_project_name,
        }
        self.endpoint = config.env.azure_ai_endpoint
        self.language_api_key = config.env.azure_language_api_key
        self.language_endpoint = config.env.azure_language_endpoint
        self.credential = DefaultAzureCredential()
        self.client = TextAnalyticsClient(
            endpoint=self.endpoint, credential=self.credential
        )
        self.bot = BotHandler()
        self.preprocessor = PreProcessor()
        self.azure_openai_metric_mapping = {"safe": 0, "low": 1, "medium": 3, "high": 5}

    def evaluate_grammar(self, query: str):
        prompt = f"Evaluate the grammatical correctness of the following sentence and return only the score from 0 to 5:\n\n{query}"
        result = self.bot.get_response(prompt)
        return result.get("response", "Error in evaluation")

    def evaluate_spell_check(self, query: str):
        prompt = f"Evaluate the spelling accuracy of the following sentence and return only the score from 0 to 5:\n\n{query}"
        result = self.bot.get_response(prompt)
        return result.get("response", "Error in evaluation")

    def evaluate_sensitive_info(self, query: str):
        query = [query]
        credential = AzureKeyCredential(self.language_api_key)
        text_analytics_client = TextAnalyticsClient(
            endpoint=self.language_endpoint, credential=credential
        )
        try:
            response = text_analytics_client.recognize_entities(query)
            return response
        except Exception as e:
            logging.error(f"Error during evaluation: {e}")
            return 0

    def evaluate_violence(self, query: str, response: str):
        violence_evaluator = ViolenceEvaluator(
            credential=self.credential, azure_ai_project=self.azure_ai_project
        )
        try:
            result = violence_evaluator(query=query, response=response)
            return result
        except Exception as e:
            logging.error(f"Error during evaluation: {e}")
            return None

    def evaluate_bias_gender(self, query: str, response: str):
        sexual_eval = SexualEvaluator(
            azure_ai_project=self.azure_ai_project, credential=self.credential
        )
        try:
            result = sexual_eval(query=query, response=response)
            return result
        except Exception as e:
            logging.error(f"Error during evaluation: {e}")
            return None

    def evaluate_self_harm(self, query: str, response: str):
        selfharm_eval = SelfHarmEvaluator(
            azure_ai_project=self.azure_ai_project, credential=self.credential
        )
        try:
            result = selfharm_eval(query=query, response=response)
            return result
        except Exception as e:
            logging.error(f"Error during evaluation: {e}")
            return None

    def evaluate_hate_unfairness(self, query: str, response: str):
        hate_unfairness_eval = HateUnfairnessEvaluator(
            azure_ai_project=self.azure_ai_project, credential=self.credential
        )
        try:
            result = hate_unfairness_eval(query=query, response=response)
            return result
        except Exception as e:
            logging.error(f"Error during evaluation: {e}")
            return None

    def evaluate_jailbreak(self, query: str, response: str):
        jailbreak_eval = IndirectAttackEvaluator(
            azure_ai_project=self.azure_ai_project, credential=self.credential
        )
        try:
            result = jailbreak_eval(query=query, response=response)
            return result
        except Exception as e:
            logging.error(f"Error during evaluation: {e}")
            return None

    def evaluate_all(self, query: str, response: str):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_function = {
                "grammar": executor.submit(self.evaluate_grammar, query),
                "spell_check": executor.submit(self.evaluate_spell_check, query),
                "sensitive_info": executor.submit(self.evaluate_sensitive_info, query),
                "violence": executor.submit(self.evaluate_violence, query, response),
                "bias_gender": executor.submit(
                    self.evaluate_bias_gender, query, response
                ),
                "bias_self_harm": executor.submit(
                    self.evaluate_self_harm, query, response
                ),
                "hate_unfairness": executor.submit(
                    self.evaluate_hate_unfairness, query, response
                ),
                "jailbreak": executor.submit(self.evaluate_jailbreak, query, response),
            }

            results = {
                key: future.result() for key, future in future_to_function.items()
            }
        return results

    def get_openai_metrics(self, metrics_response: object, query: str):
        print(metrics_response)
        # {'flagged': True, 'grammar': 0, 'spell_check': 0, 'sensitive_info': 5, 'violence': 3, 'bias_gender': 0, 'bias_self_harm': 0, 'hate_unfairness': 0, 'jailbreak': False}
        # check if metrics_response has key flagged
        if "flagged" in metrics_response:
            return {
                "flagged": True,
                "grammar": metrics_response["grammar"],
                "spell_check": metrics_response["spell_check"],
                "sensitive_info": metrics_response["sensitive_info"],
                "violence": metrics_response["violence"],
                "bias_gender": metrics_response["bias_gender"],
                "self_harm": metrics_response["self_harm"],
                "hate_unfairness": metrics_response["hate_unfairness"],
                "jailbreak": metrics_response["jailbreak"],
            }
        else:
            # {'response': 'The provided prompt was filtered due to the prompt triggering the content management policy. Please modify your prompts.', 'content_filter': True, 'hate': {'filtered': False, 'severity': 'safe'}, 'jailbreak': {'filtered': False, 'detected': False}, 'self_harm': {'filtered': False, 'severity': 'safe'}, 'sexual': {'filtered': False, 'severity': 'safe'}, 'violence': {'filtered': True, 'severity': 'medium'}, 'error': True}
            return {
                "flagged": True,
                "grammar": 0,
                "spell_check": 0,
                "sensitive_info": 0,
                "violence": self.azure_openai_metric_mapping[
                    metrics_response["violence"].get("severity", "safe")
                ],
                "hate_unfairness": self.azure_openai_metric_mapping[
                    metrics_response["hate"].get("severity", "safe")
                ],
                "jailbreak": metrics_response["jailbreak"]["detected"],
                "self_harm": self.azure_openai_metric_mapping[
                    metrics_response["self_harm"].get("severity", "safe")
                ],
                "bias_gender" : self.azure_openai_metric_mapping[
                    metrics_response["sexual"].get("severity", "safe")
                ],
            }
