import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

class SuperAgent:
    """
    Super Agent using Gemini 2.0 Flash Lite for action execution.
    """
    def __init__(self, model="gemini-2.0-flash-lite", api_key=None):
        self.model = model
        self.api_key = api_key or GOOGLE_API_KEY
        self.llm = ChatGoogleGenerativeAI(api_key=self.api_key, model=self.model)

    def act_on_action(user_action):
        """
        Given session memory and a user action (clicked action button),
        reply that the agent will do the action.
        """
        # prompt = f"""
        # You are a super agent for a retail assistant app. When the user clicks an action button, reply concisely that you will do the action, referencing the action and the context.
        # Session memory: {session_memory}
        # User action: {user_action}
        # Reply: "I will do the action: '{user_action}'."
        # """
        # response = self.llm.invoke(prompt)
        # Always return a simple confirmation as required
        return f"I will do the action: '{user_action}'."
