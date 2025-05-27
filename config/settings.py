import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    langchain_api_key: str = ""
    langchain_project: str = "exercise-tracker-chatbot"
    exercise_service_url: str = ""
    
    class Config:
        env_file = ".env"

settings = Settings() 