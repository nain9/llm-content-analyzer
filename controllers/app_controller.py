from typing import Dict, Any

import aiohttp
from telebot import types

from entities.states import RuntimeStates
from entities.user import User
from models.base_model import BaseModel
from models.gemini_model import GeminiModel
from models.openai_model import OpenAIModel
from services.firebase_service import FirebaseService
from views.telegram_view import TelegramView
from config import Config


class AppController:
    """Контроллер приложения для управления взаимодействием между представлением и моделями."""

    def __init__(self, view: TelegramView, config: Config):
        """Инициализация контроллера с представлением и конфигурацией."""
        self.view: TelegramView = view
        self.config: Config = config
        self.firebase_service: FirebaseService = FirebaseService(self.config.FIREBASE_API_KEY_PATH)
        self.models: Dict[str, BaseModel] = {
            'ChatGPT': OpenAIModel(self.config.PROXY_API_KEY),
            'DeepSeek': OpenAIModel(self.config.PROXY_API_KEY),
            'Gemini': GeminiModel(self.config.PROXY_API_KEY)
        }
        self.view.set_controller(self)

    async def start(self) -> None:
        """Запустить приложение."""
        await self.view.start_polling()

    async def get_state_by_user_id(self, user_id: int) -> RuntimeStates:
        """Получить состояние пользователя по его ID."""
        user = await self._get_user(user_id)
        return user.get_state()
    
    async def _set_state_by_user_id(self, user_id: int, state: RuntimeStates) -> None:
        """Установить состояние пользователя по его ID."""
        user = await self._get_user(user_id)
        await user.set_state(state)

    async def _get_user(self, user_id: int) -> User:
        """Получить или создать пользователя из базы данных."""
        return await self.firebase_service.get_user(user_id)

    def _get_model_for_user(self, user: User) -> BaseModel:
        """Получить экземпляр модели в зависимости от типа модели пользователя."""
        model = self.models.get(user.model_type)
        if model is None:
            raise ValueError(f'Unknown model type: {user.model_type}')
        return model

    def _get_base_url(self, model_type: str) -> str:
        """Получить базовый URL для API в зависимости от типа модели."""
        if model_type not in self.config.API_URLS:
            raise ValueError(f'Неизвестный тип модели: {model_type}')
        return self.config.API_URLS[model_type]

    def _get_model_type(self, model: str) -> str:
        """Получить тип модели по её названию."""
        model_type = next((type for type, models in self.config.MODELS.items() if model in models), None)
        if model_type is None:
            raise ValueError(f'Неизвестный тип модели: {model}')
        return model_type

    def _create_model_keyboard(self, model_type: str) -> types.InlineKeyboardMarkup:
        """Создать клавиатуру для выбора модели."""
        keyboard = types.InlineKeyboardMarkup()
        for model in self.config.MODELS[model_type]:
            keyboard.add(types.InlineKeyboardButton(text=model, callback_data=f'model_{model}'))
        keyboard.add(types.InlineKeyboardButton(text='« Назад', callback_data='back_to_model_type'))
        return keyboard

    def _create_model_type_keyboard(self) -> types.InlineKeyboardMarkup:
        """Создать клавиатуру для выбора типа модели."""
        keyboard = types.InlineKeyboardMarkup()
        for model_type in self.config.MODELS:
            keyboard.add(types.InlineKeyboardButton(model_type, callback_data=model_type))
        return keyboard

    def _create_action_keyboard(self, model_type: str) -> types.InlineKeyboardMarkup:
        """Создать клавиатуру для выбора действия после смены модели."""
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text='Начать анализ поста', callback_data='analyze'))
        keyboard.add(types.InlineKeyboardButton(text='« Назад', callback_data=f'back_to_model_name_{model_type}'))
        return keyboard

    async def handle_analyze(self, message: types.Message) -> None:
        """Обработать команду начала анализа поста."""
        user_id = message.from_user.id
        await self.clear_context(user_id)
        await self._set_state_by_user_id(user_id, RuntimeStates.state_platform)
        await self.view.send_state_keyboard(message.chat.id, user_id, RuntimeStates.state_platform)

    async def handle_clear(self, message: types.Message) -> None:
        """Обработать команду очистки контекста."""
        await self.clear_context(message.from_user.id)
        await self.view.send_message(message.chat.id, 'Контекст очищен!')

    async def handle_balance(self, message: types.Message) -> None:
        """Обработать команду проверки баланса API."""
        if message.from_user.id != self.config.ADMIN_ID:
            await self.view.send_message(message.chat.id, 'Нет доступа к балансу!')
            return
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url=self.config.API_URLS['balance'],
                headers={'Authorization': f'Bearer {self.config.PROXY_API_KEY}'}
            ) as response:
                balance = (await response.json()).get('balance', 'Недоступно')
                await self.view.send_message(message.chat.id, f'Текущий баланс: {balance}')

    async def handle_current_model(self, message: types.Message) -> None:
        """Обработать команду отображения текущей модели."""
        user = await self._get_user(message.from_user.id)
        model_name = user.model_name
        model_type = self._get_model_type(model_name)
        await self.view.send_message(
            message.chat.id,
            f'Тип модели: {model_type}\n'
            f'Текущая модель: {model_name}'
        )

    async def handle_reanalyze(self, message: types.Message) -> None:
        """Обработать команду повторного анализа поста."""
        user = await self._get_user(message.from_user.id)
        await user.clear_messages()
        chat_id = message.chat.id

        if not user.analysis_data.post_text:
            await self.view.send_message(chat_id, 'Нет данных для анализа. Используйте /analyze для нового анализа.')
            return

        model = self._get_model_for_user(user)
        if user.advanced_analysis:
            response = await model.advanced_analyze_data(user)
            await self._send_analysis_results(user, chat_id, response)
        else:
            response = await model.analyze_data(user)
            await self._send_analysis_results(user, chat_id, response)

    async def handle_switch(self, message: types.Message) -> None:
        """Обработать команду переключения режима анализа."""
        user = await self._get_user(message.from_user.id)
        await user.set_advanced_analysis(not user.advanced_analysis)
        status = "включен" if user.advanced_analysis else "выключен"
        await self.view.send_message(
            message.chat.id,
            f'Расширенный режим анализа {status}!'
        )

    async def handle_state_input(self, user_id: int, chat_id: int, text: str, state: RuntimeStates) -> None:
        """Обработать ввод для текущего шага анализа."""
        user = await self._get_user(user_id)
        config = self.config.STATES_CONFIG[state]
        await user.set_analysis_field(config['field'], text)        
        await self._set_state_by_user_id(user_id, config['next'])

        if config['next'] == RuntimeStates.state_post_text:          
            await self.view.send_message(chat_id, 'Отлично! Теперь отправьте текст поста.')
            await self.view.send_state_keyboard(chat_id, user_id, config['next'])
        else:
            await self.view.send_state_keyboard(chat_id, user_id, config['next'])

    async def handle_post_text(self, user_id: int, chat_id: int, text: str) -> None:
        """Обработать текст поста."""
        user = await self._get_user(user_id)
        await user.set_analysis_field('post_text', text)
        await self._set_state_by_user_id(user_id, RuntimeStates.state_discusse)
        
        model = self._get_model_for_user(user)
        if user.advanced_analysis:
            response = await model.advanced_analyze_data(user)
            await self._send_analysis_results(user, chat_id, response)
        else:
            response = await model.analyze_data(user)
            await self._send_analysis_results(user, chat_id, response)

    async def handle_discusse_message(self, message: types.Message) -> None:
        """Обработать сообщение в контексте обсуждения поста."""
        user = await self._get_user(message.from_user.id)
        model = self._get_model_for_user(user)
        response = await model.get_discusse_response(user, message.text)
        await self.view.send_message(message.chat.id, response)

    async def change_model(self, user_id: int, user_choice: str, message_id: int = None):
        """Изменить модель для конкретного пользователя."""
        if user_choice in self.config.MODELS:
            # Показать выбор конкретной модели
            markup = self._create_model_keyboard(user_choice)
            await self.view.edit_message_text(
                chat_id=user_id,
                message_id=message_id,
                text='Выберите модель:',
                reply_markup=markup
            )
        elif user_choice.startswith('model_'):
            # Обработать выбор конкретной модели
            user = await self._get_user(user_id)
            model_name = user_choice.replace('model_', '')
            model_type = self._get_model_type(model_name)
            base_url = self._get_base_url(model_type)
            await user.update_model(model_type, model_name, base_url)

            markup = self._create_action_keyboard(model_type)
            await self.view.edit_message_text(
                chat_id=user_id,
                message_id=message_id,
                text=f'Модель изменена на {model_name}. Выберите действие:',
                reply_markup=markup
            )
        elif user_choice == 'back_to_model_type':
            # Вернуться к выбору типа модели
            markup = self._create_model_type_keyboard()
            await self.view.edit_message_text(
                chat_id=user_id,
                message_id=message_id,
                text='Выберите тип модели:',
                reply_markup=markup
            )
        elif user_choice.startswith('back_to_model_name_'):
            # Вернуться к выбору конкретной модели
            model_type = user_choice.replace('back_to_model_name_', "")
            markup = self._create_model_keyboard(model_type)
            await self.view.edit_message_text(
                chat_id=user_id,
                message_id=message_id,
                text='Выберите модель:',
                reply_markup=markup
            )

    async def clear_context(self, user_id: int) -> None:
        """Очистить контекст для конкретного пользователя."""
        user = await self._get_user(user_id)
        await user.clear()

    async def _send_analysis_results(self, user: User, chat_id: int, response: str) -> None:
        """Отправить результаты анализа пользователю."""
        await self.view.send_message(
            chat_id,
            f'Модель: {user.model_name}\n'
            f'Платформа: {user.analysis_data.platform}\n'
            f'Тип блога: {user.analysis_data.blog_type}\n'
            f'Цель: {user.analysis_data.purpose}\n'
            f'Аудитория: {user.analysis_data.audience}\n\n'
            f'{response}'
        )
        await self._set_state_by_user_id(user.user_id, RuntimeStates.state_discusse) 