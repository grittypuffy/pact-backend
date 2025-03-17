from azure.ai.evaluation import (
    ViolenceEvaluator,SexualEvaluator,SelfHarmEvaluator,HateUnfairnessEvaluator
)
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

class Metrics:
    def __init__(self):
        """
        Initializes the Metrics class with Azure AI service credentials.
        """
        self.azure_ai_project = {
            "subscription_id": os.getenv("AZURE_SUBSCRIPTION_ID"),
            "resource_group_name": os.getenv("AZURE_RESOURCE_GROUP"),
            "project_name": os.getenv("AZURE_PROJECT_NAME"),
        }
        self.credential = DefaultAzureCredential()
    
    def evaluate_grammar(self, response):
     
        # try:
        #     grammar_evaluator = GrammarEvaluator(credential=self.credential, azure_ai_project=self.azure_ai_project)
        #     return grammar_evaluator(response=response)
        # except Exception as e:
        #     print(f"Grammar Evaluation Error: {e}")
        #     return None
        return 0
    
    def evaluate_spell_check(self, response):
       
        # try:
        #     spell_evaluator = SpellCheckEvaluator(credential=self.credential, azure_ai_project=self.azure_ai_project)
        #     return spell_evaluator(response=response)
        # except Exception as e:
        #     print(f"Spell Check Error: {e}")
        #     return None
        return 0
    
    def evaluate_sensitive_info(self, response):
       
        # try:
        #     sensitive_evaluator = SensitiveInfoEvaluator(credential=self.credential, azure_ai_project=self.azure_ai_project)
        #     return sensitive_evaluator(response=response)
        # except Exception as e:
        #     print(f"Sensitive Info Evaluation Error: {e}")
        #     return None
        return 0
    
    def evaluate_violence(self, query, response):
      
        # Initialize credentials and ViolenceEvaluator
        credential = DefaultAzureCredential()
        violence_evaluator = ViolenceEvaluator(credential=credential, azure_ai_project=self.azure_ai_project)

        # Perform evaluation
        try:
            result = violence_evaluator(query=query, response=response)
            return result
        except Exception as e:
            print(f"Error during evaluation: {e}")
            return None
    
    def evaluate_bias_gender(self,query, response):
        
        credential = DefaultAzureCredential()
        sexual_eval = SexualEvaluator(azure_ai_project=self.azure_ai_project, credential=credential)
        try:
            result = sexual_eval(query=query, response=response)
            return result
        except Exception as e:
            print(f"Error during evaluation: {e}")
            return None
        

    
    def evaluate_self_harm(self, query, response):
       
        credential = DefaultAzureCredential()
        selfharm_eval = SelfHarmEvaluator(azure_ai_project=self.azure_ai_project, credential=credential)
        try:
            result = selfharm_eval(query=query, response=response)
            return result
        except Exception as e:
            print(f"Error during evaluation: {e}")
            return None
    
    def evaluate_hate_unfairness(self, query, response):
        
        credential = DefaultAzureCredential()
        hate_unfairness_eval = HateUnfairnessEvaluator(azure_ai_project=self.azure_ai_project, credential=credential)
        try:
            result = hate_unfairness_eval(query=query, response=response)
            return result
        except Exception as e:
            print(f"Error during evaluation: {e}")
            return None
    
    def evaluate_jailbreak(self, query, response):
       
        # try:
        #     jailbreak_evaluator = JailbreakEvaluator(credential=self.credential, azure_ai_project=self.azure_ai_project)
        #     return jailbreak_evaluator(query=query, response=response)
        # except Exception as e:
        #     print(f"Jailbreak Evaluation Error: {e}")
        #     return None
        return 0
    
    def evaluate_all(self, query, response):
       
        return {
            "grammar": self.evaluate_grammar(query,response),
            "spell_check": self.evaluate_spell_check(query,response),
            "sensitive_info": self.evaluate_sensitive_info(query,response),
            "violence": self.evaluate_violence(query,response),
            "bias_gender": self.evaluate_bias_gender(query,response),
            "bias_self_harm": self.evaluate_self_harm(query,response),
            "hate_unfairness": self.evaluate_incomplete_input(query, response),
            "jailbreak": self.evaluate_jailbreak(query, response),
        }
