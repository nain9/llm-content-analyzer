import asyncio
from google import genai
from google.genai.types import Content, Part, GenerateContentConfig

from entities.user import User
from models.base_model import BaseModel


class GeminiModel(BaseModel):
    """Модель Google Gemini для генерации текста и анализа контента."""

    def __init__(self, api_key: str):
        super().__init__(api_key)

    async def _get_response(self, 
                          user: User,
                          max_tokens: int = None, 
                          temperature: float = None, 
                          frequency_penalty: float = None, 
                          presence_penalty: float = None, 
                          messages: list = None) -> str:
        """Получить ответ от модели Gemini."""
        try:
            client = genai.Client(
                api_key=self.api_key, 
                http_options={"base_url": "https://api.proxyapi.ru/google"}
            )

            contents = [
                Content(
                    role=message['role'],
                    parts=[Part(text=message['content'])]
                )
                for message in messages or user.messages
            ]

            config = GenerateContentConfig(
                temperature=temperature or self.temperature,
                frequency_penalty=frequency_penalty or self.frequency_penalty,
                presence_penalty=presence_penalty or self.presence_penalty,
                max_output_tokens=max_tokens or self.max_tokens
            )

            response = await asyncio.to_thread(
                client.models.generate_content, 
                model=user.model_name,
                contents=contents,
                config=config
            )

            return response.text.replace('*', '')
        except Exception as e:
            return f'Ошибка: {str(e)}'
        