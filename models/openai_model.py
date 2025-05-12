from openai import AsyncOpenAI

from entities.user import User
from models.base_model import BaseModel


class OpenAIModel(BaseModel):
    """Модель OpenAI для генерации текста и анализа контента."""

    def __init__(self, api_key: str):   
        super().__init__(api_key)

    async def _get_response(self, 
                            user: User,
                            max_tokens: int = None, 
                            temperature: float = None, 
                            frequency_penalty: float = None, 
                            presence_penalty: float = None, 
                            messages: list = None) -> str:
        """Получить ответ от модели OpenAI."""
        try:
            client = AsyncOpenAI(api_key=self.api_key, base_url=user.base_url)
            response = await client.chat.completions.create(
                model=user.model_name,
                messages=messages or user.messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
                frequency_penalty=frequency_penalty or self.frequency_penalty,
                presence_penalty=presence_penalty or self.presence_penalty
            )
            return response.choices[0].message.content.replace('*', '')
        except Exception as e:
            return f'Ошибка: {str(e)}'
