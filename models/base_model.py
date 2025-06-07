import asyncio
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

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

    async def _get_multiple_responses(self, 
                                      user: 'User', 
                                      max_tokens: int = None, 
                                      temperature: float = None, 
                                      frequency_penalty: float = None, 
                                      presence_penalty: float = None, 
                                      messages: list = None) -> list:
        """Параллельно получить ответы на список сообщений"""
        responses = await asyncio.gather(*[
            self._get_response(
                user=user,
                messages=[{"role": "user", "content": text}],
                max_tokens=max_tokens,
                temperature=temperature,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty
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
        input_text = PromptTemplates.comment_response(user.analysis_data)
        comment = await self._get_response(
            user=user,
            messages=[{"role": "user", "content": input_text}],
            max_tokens=100,
            temperature=0.5,
            frequency_penalty=0.4,
            presence_penalty=0.2,
        )
        input_messages, topics, beginnings = PromptTemplates.advanced_audience_reaction(user.analysis_data)
        output_messages = await self._get_multiple_responses(
            user=user, 
            messages=input_messages,
            max_tokens=700,
            temperature=0.1,
            frequency_penalty=0.0,
            presence_penalty=0.0,
        )
        input_summaries = [
            PromptTemplates.summary_response(message, topic, beginning) 
            for message, topic, beginning in zip(output_messages, topics, beginnings)
        ]
        output_summaries = await self._get_multiple_responses(
            user=user, 
            messages=input_summaries,
            max_tokens=150,
            temperature=0.4,
            frequency_penalty=0.4,
            presence_penalty=0.2,
        )
        return comment + '\n\n' + '\n\n'.join(output_summaries)

    async def get_dialog_response(self, user: 'User', message: str) -> str:
        """Получить ответ на сообщение пользователя в контексте обсуждения поста."""
        try:
            reasoning_prompt = PromptTemplates.dialog_validation_reasoning(message, user.messages)
            reasoning_response = await self._get_response(
                user=user,
                messages=[{'role': 'user', 'content': reasoning_prompt}],
                max_tokens=700,
                temperature=0.1,
                frequency_penalty=0.0,
                presence_penalty=0.0,
            )
            summary_prompt = PromptTemplates.dialog_validation_summary(reasoning_response)
            summary_response = await self._get_response(
                user=user,
                messages=[{'role': 'user', 'content': summary_prompt}],
                temperature=0.1,
                max_tokens=10
            )
            if summary_response.strip().lower() == 'true':
                prompt = PromptTemplates.dialog_response(message)
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
        