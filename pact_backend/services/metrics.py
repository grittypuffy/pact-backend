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
        hate = metrics_response["hate"]
        jailbreak = metrics_response["jailbreak"]
        self_harm = metrics_response["self_harm"]
        sexual = metrics_response["sexual"]
        violence = metrics_response["violence"]

        hate, hate_severity = hate["filtered"], hate["severity"]
        jailbreak, jailbreak_attempt = jailbreak["filtered"], jailbreak["detected"]
        self_harm, self_harm_severity = self_harm["filtered"], self_harm["severity"]
        sexual, sexual_severity = sexual["filtered"], sexual["severity"]
        violence, violence_severity = violence["filtered"], violence["severity"]

        hate_severity = self.azure_openai_metric_mapping.get(hate_severity.lower())

        self_harm_severity = self.azure_openai_metric_mapping.get(self_harm_severity.lower())
        sexual_severity = self.azure_openai_metric_mapping.get(sexual_severity.lower())
        violence_severity = self.azure_openai_metric_mapping.get(violence_severity.lower())
        grammar = 0
        spell_check = 0

        sensitive_info = self.evaluate_sensitive_info(query)
        maxi = -1
        if (
            sensitive_info
            and isinstance(sensitive_info, list)
        ):
            entities = sensitive_info[0].entities
            for ele in entities:
                maxi = max(maxi, ele.get("confidence_score", -1))

            maxi = int(math.ceil((maxi * 5)))
        else:
            maxi = -1
        sensitive_info = maxi


        return {
            "flagged": True,
            "grammar": grammar,
            "spell_check": spell_check,
            "sensitive_info": sensitive_info,
            "violence": violence_severity,
            "bias_gender": sexual_severity,
            "bias_self_harm": self_harm_severity,
            "hate_unfairness": hate_severity,
            "jailbreak": jailbreak_attempt,
        }
