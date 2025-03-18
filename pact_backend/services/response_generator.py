from langchain_community.callbacks import get_openai_callback
from langchain_openai import AzureChatOpenAI
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

class BotHandler:
    """
    Handles communication with Azure OpenAI models using LangChain.
    """

    def __init__(self, temperature: float = 0, max_tokens: int = 500):
        """
        Initializes the BotHandler with model configurations.
        
        Args:
            temperature (float): Controls randomness (default = 0).
            max_tokens (int): Maximum tokens for the response (default = 200).
        """
        
        self.model = os.getenv("AZURE_OPENAI_MODEL")
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Fetch model-specific environment variables
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION")

        if not all([self.api_key, self.endpoint, self.deployment, self.api_version, self.model]):
            raise EnvironmentError("Missing environment variables for Azure OpenAI.")

        # Initialize Azure OpenAI LLM
        self.llm = AzureChatOpenAI(
            openai_api_key=self.api_key,
            azure_endpoint=self.endpoint,
            azure_deployment=self.deployment,  # Deployment Name
            model=self.model,  # Explicitly specify model
            api_version=self.api_version,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            timeout=30,
            max_retries=3,
        )

    def get_response(self, prompt: str, structure=None):
        """
        Sends a prompt to the Azure OpenAI model and returns the response.

        Args:
            prompt (str): The user query.
            structure (dict, optional): Formatting template for prompt.

        Returns:
            dict: Contains response from the model.
        """
        if structure is None:
            structure = {"prompt_template": "Answer the following question: {}"}

        formatted_prompt = structure.get("prompt_template", "{}").format(prompt)

        try:
            with get_openai_callback() as cb:
                output = self.llm.invoke(formatted_prompt)  # Returns AIMessage
                response = output.content  # Extract content
                
        except Exception as e:
            raise RuntimeError(f"Error during API call: {e}")

        return {
            "response": response
        }

# # Example usage
# if __name__ == "__main__":
#     bot = BotHandler()
#     result = bot.get_response("What is LangChain?")
#     print(result)
