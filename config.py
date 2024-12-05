from dotenv import load_dotenv
from gpt import ChatGptService
import os

load_dotenv()
TG_TOKEN=os.getenv("TG_BOT_API")
GPT_TOKEN=os.getenv("GPT_TOKEN")
chat_gpt = ChatGptService(GPT_TOKEN)



