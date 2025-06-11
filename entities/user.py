from dataclasses import dataclass, field
from functools import wraps
from typing import Dict, List, TYPE_CHECKING

from entities.analysis_data import AnalysisData
from entities.states import RuntimeStates

if TYPE_CHECKING:
    from services.firebase_service import FirebaseService


def auto_save(func):
    """Декоратор для автоматического сохранения пользователя после изменения полей."""
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        result = await func(self, *args, **kwargs)
        await self.save()
        return result
    return wrapper


@dataclass
class User:
    """Класс для хранения данных пользователя и информации о сессии."""
    user_id: int
    model_type: str = 'ChatGPT'
    model_name: str = 'gpt-4.1-nano-2025-04-14'
    base_url: str = 'https://api.proxyapi.ru/openai/v1'
    messages: List[Dict[str, str]] = field(default_factory=list)
    comments: list = field(default_factory=list)
    analysis_data: AnalysisData = field(default_factory=AnalysisData)
    state: str = RuntimeStates.state_none.name
    _firebase_service: 'FirebaseService' = None

    def set_firebase_service(self, service: 'FirebaseService') -> None:
        """Установить сервис Firebase для автоматического сохранения."""
        self._firebase_service = service

    async def save(self) -> None:
        """Сохранить пользователя в Firebase."""
        if hasattr(self, '_firebase_service'):
            await self._firebase_service.save_user(self)

    @auto_save
    async def add_message(self, role: str, content: str) -> None:
        """Добавить сообщение в историю сообщений пользователя."""
        self.messages.append({'role': role, 'content': content})
    
    @auto_save
    async def add_comment(self, comment: str) -> None:
        """Добавить комментарий."""
        self.comments.append(comment)

    @auto_save
    async def clear(self) -> None:
        """Очистить историю сообщений пользователя."""
        self.messages = []
        self.comments = []
        self.analysis_data = AnalysisData()
        self.state = RuntimeStates.state_none.name

    @auto_save
    async def clear_messages(self) -> None:
        self.messages = []

    @auto_save
    async def update_model(self, model_type: str, model_name: str, base_url: str) -> None:
        """Обновить настройки модели."""
        self.model_type = model_type
        self.model_name = model_name
        self.base_url = base_url

    @auto_save
    async def set_analysis_field(self, field: str, value: str) -> None:
        """Установить значение конкретного поля в данных анализа."""
        setattr(self.analysis_data, field, value)

    @auto_save
    async def set_state(self, state: RuntimeStates) -> None:
        """Установить состояние пользователя."""
        self.state = state.name

    def get_state(self) -> RuntimeStates:
        """Получить текущее состояние пользователя."""
        return getattr(RuntimeStates, self.state.split(':')[-1])

    def to_dict(self) -> dict:
        """Преобразовать объект пользователя в словарь для сохранения."""
        return {
            'user_id': self.user_id,
            'model_type': self.model_type,
            'model_name': self.model_name,
            'base_url': self.base_url,
            'messages': self.messages,
            'comments': self.comments,
            'analysis_data': self.analysis_data.to_dict(),
            'state': self.state
        }

    @staticmethod
    def from_dict(data: dict) -> 'User':
        """Создать объект пользователя из словаря."""
        return User(
            user_id=data['user_id'],
            model_type=data.get('model_type', ""),
            model_name=data.get('model_name', ""),
            base_url=data.get('base_url', ""),
            messages=data.get('messages', []),
            comments=data.get('comments', []),
            analysis_data=AnalysisData.from_dict(data.get('analysis_data', {})),
            state=data.get('state', RuntimeStates.state_none.name)
        )

