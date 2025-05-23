from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
import asyncio

from models.prompt_templates import PromptTemplates

if TYPE_CHECKING:
    from entities.user import User


class BaseModel(ABC):
    """Базовый класс для LLM моделей."""

    def __init__(self, api_key: str):
        """Инициализация базовых параметров модели."""
        self.api_key = api_key
        self.max_tokens = 1000
        self.temperature = 0.5
        self.frequency_penalty = 0.3
        self.presence_penalty = 0.2

    @abstractmethod
    async def _get_response(self, 
                          user: 'User',
                          max_tokens: int = None, 
                          temperature: float = None, 
                          frequency_penalty: float = None, 
                          presence_penalty: float = None, 
                          messages: list = None) -> str:
        """Получить ответ от модели"""
        pass

    async def _get_multiple_responses(self, user: 'User', messages: list) -> list:
        """Параллельно получить ответы на список сообщений"""
        responses = await asyncio.gather(*[
            self._get_response(
                user=user,
                messages=[{"role": "user", "content": text}],
                max_tokens=150
            ) for text in messages
        ])

        for text, reply in zip(messages, responses):
            await user.add_message("user", text)
            await user.add_message("assistant", reply)

        return responses

    async def analyze_data(self, user: 'User') -> str:
        """Проанализировать данные поста."""
        input_text = PromptTemplates.audience_reaction(user.analysis_data)
        await user.add_message('user', input_text)
        response = await self._get_response(
            user=user,
            messages=[{"role": "user", "content": input_text}]
        )
        await user.add_message('assistant', response)
        return response

    async def advanced_analyze_data(self, user: 'User') -> str:
        """Проанализировать данные поста, используя параллельные запросы"""
        input_messages = PromptTemplates.advanced_audience_reaction(user.analysis_data)
        output_messages = await self._get_multiple_responses(user, input_messages)
        return '\n\n'.join(output_messages)

    async def get_discusse_response(self, user: 'User', message: str) -> str:
        """Получить ответ на сообщение пользователя в контексте обсуждения поста."""
        validation_prompt = PromptTemplates.discusse_validation(message)
        validation_messages = user.messages + [{'role': 'user', 'content': validation_prompt}]
        try:
            validation_reply = await self._get_response(
                user=user,
                messages=validation_messages,
                temperature=0.0,
                max_tokens=10
            )
            if validation_reply.strip().lower() == 'true':
                prompt = PromptTemplates.discusse_response(message)
                await user.add_message('user', prompt)
                response = await self._get_response(
                    user=user,
                    max_tokens=700
                )
                await user.add_message('assistant', response)
                return response
            else:
                return 'Ваше сообщение не связано с контекстом.'
        except Exception as e:
            return f'Ошибка: {str(e)}' 
