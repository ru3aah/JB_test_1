"""
gpt.py
------

This module implements functionality related to GPT models.
It can be used to interact with GPT APIs, process text inputs, and generate
meaningful outputs using AI-driven natural language processing.

Modules and functionality:
- Communication with GPT API endpoints
- Sending prompts and receiving responses
- Text preprocessing and result formatting
- Error handling for API interactions

    print(response)
"""

import httpx as httpx
from openai import OpenAI


class ChatGptService:
    client: OpenAI = None
    message_list: list = None


    def __init__(self, token):
        token = "sk-proj-" + token[:3:-1] if token.startswith('gpt:') else token
        self.client = OpenAI(
            api_key=token,
            http_client=httpx.Client(proxy="http://18.199.183.77:49232"))
        self.message_list = []

    async def send_message_list(self) -> str:
        completion = self.client.chat.completions.create(
            model="gpt-3.5-turbo",  # gpt-4o,  gpt-4-turbo, gpt-3.5-turbo,
            # GPT-4o mini
            messages=self.message_list,
            max_tokens=3000,
            temperature=0.9
        )
        message = completion.choices[0].message
        self.message_list.append(message)
        return message.content

    def set_prompt(self, prompt_text: str) -> None:
        self.message_list.clear()
        self.message_list.append({"role": "system", "content": prompt_text})

    async def add_message(self, message_text: str) -> str:
        self.message_list.append({"role": "user", "content": message_text})
        return await self.send_message_list()

    async def send_question(self, prompt_text: str, message_text: str) -> str:
        self.message_list.clear()
        self.message_list.append({"role": "system", "content": prompt_text})
        self.message_list.append({"role": "user", "content": message_text})
        return await self.send_message_list()
