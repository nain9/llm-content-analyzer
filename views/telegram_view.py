from telebot import types
from telebot.async_telebot import AsyncTeleBot
from entities.states import RuntimeStates


class TelegramView:
    """Представление для взаимодействия с Telegram API."""

    def __init__(self, bot_token: str):
        """Инициализация представления с токеном бота."""
        self.bot = AsyncTeleBot(bot_token)
        self.controller = None
        self.keyboard_message_id = None
        self._setup_handlers()

    def set_controller(self, controller) -> None:
        """Установить контроллер для этого представления."""
        self.controller = controller

    def _setup_handlers(self) -> None:
        """Настроить все обработчики сообщений."""
        self.bot.message_handler(commands=['start'])(self._handle_start)
        self.bot.message_handler(commands=['clear'])(self._handle_clear)
        self.bot.message_handler(commands=['balance'])(self._handle_balance)
        self.bot.message_handler(commands=['changemodel'])(self._handle_change_model)
        self.bot.message_handler(commands=['currentmodel'])(self._handle_current_model)
        self.bot.message_handler(commands=['comment'])(self._handle_comment)
        self.bot.message_handler(commands=['analyze'])(self._handle_analyze)
        self.bot.message_handler(commands=['reanalyze'])(self._handle_reanalyze)
        self.bot.message_handler(commands=['switch'])(self._handle_switch)

        async def param_state_filter(message) -> bool:    
            return await self._is_valid_param_state(message.from_user.id)

        async def discusse_state_filter(message) -> bool:
            state = await self._get_state(message.from_user.id)
            return state == RuntimeStates.state_dialog

        self.bot.message_handler(func=param_state_filter)(self._handle_params_messages)
        self.bot.message_handler(func=discusse_state_filter)(self._handle_dialog_message)

        def model_callback_filter(call: types.CallbackQuery) -> bool:
            return (
                call.data in self.controller.config.MODELS or
                call.data.startswith('model_') or 
                call.data == 'back_to_model_type' or
                call.data.startswith('back_to_model_name_')
            )

        self.bot.callback_query_handler(func=model_callback_filter)(self._handle_model_callback)
        self.bot.callback_query_handler(func=lambda call: call.data == 'analyze')(self._handle_analyze_callback)
        self.bot.callback_query_handler(func=lambda call: True)(self._handle_general_callback)

    async def _get_state(self, user_id: int) -> RuntimeStates:
        """Получить текущее состояние пользователя."""
        return await self.controller.get_state_by_user_id(user_id)

    async def _is_valid_param_state(self, user_id: int) -> bool:
        """Проверить, является ли текущее состояние состоянием параметра."""
        state = await self._get_state(user_id)
        return state in [
            RuntimeStates.state_platform,
            RuntimeStates.state_blog_type,
            RuntimeStates.state_purpose,
            RuntimeStates.state_audience,
            RuntimeStates.state_post_text
        ]

    async def start_polling(self) -> None:
        """Запустить бота."""
        await self.bot.polling(none_stop=True)

    async def send_message(self, chat_id: int, text: str, reply_markup: types.InlineKeyboardMarkup = None) -> types.Message:
        """Отправить сообщение пользователю."""
        return await self.bot.send_message(chat_id, text, reply_markup=reply_markup)

    async def edit_message_reply_markup(self, chat_id: int, message_id: int, reply_markup: types.InlineKeyboardMarkup = None) -> None:
        """Изменить разметку ответа сообщения."""
        await self.bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=reply_markup)

    async def edit_message_text(self, chat_id: int, message_id: int, text: str, reply_markup: types.InlineKeyboardMarkup = None) -> None:
        """Изменить текст сообщения."""
        await self.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=reply_markup)

    async def send_state_keyboard(self, chat_id: int, user_id: int, state: str) -> None:
        """Отправить клавиатуру для текущего шага."""
        config = self.controller.config.STATES_CONFIG[state]
        markup = types.InlineKeyboardMarkup()
        for option in config['keyboard']:
            markup.add(types.InlineKeyboardButton(option, callback_data=option))
        sent = await self.send_message(chat_id, config['text'], reply_markup=markup)
        self.keyboard_message_id = sent.message_id

    async def _handle_start(self, message: types.Message) -> None:
        """Обработать команду /start."""
        await self.send_message(
            message.chat.id,
            'Привет! Начните анализ вашей текстовой публикации и я подскажу возможную реакцию аудитории.'
        )

    async def _handle_clear(self, message: types.Message) -> None:
        """Обработать команду /clear."""
        await self.controller.handle_clear(message)

    async def _handle_balance(self, message: types.Message) -> None:
        """Обработать команду /balance."""
        await self.controller.handle_balance(message)

    async def _handle_change_model(self, message: types.Message) -> None:
        """Обработать команду /changemodel."""
        markup = types.InlineKeyboardMarkup()
        for model_type in self.controller.config.MODELS:
            markup.add(types.InlineKeyboardButton(model_type, callback_data=model_type))
        await self.send_message(
            chat_id=message.chat.id,
            text='Выберите тип модели:',
            reply_markup=markup
        )

    async def _handle_current_model(self, message: types.Message) -> None:
        """Обработать команду /currentmodel."""
        await self.controller.handle_current_model(message)
        
    async def _handle_comment(self, message: types.Message) -> None:
        await self.controller.handle_comment(message)

    async def _handle_analyze(self, message: types.Message) -> None:
        """Обработать команду /analyze."""
        await self.controller.handle_analyze(message)

    async def _handle_reanalyze(self, message: types.Message) -> None:
        """Обработать команду /reanalyze."""
        await self.controller.handle_reanalyze(message)

    async def _handle_switch(self, message: types.Message) -> None:
        """Обработать команду /switch."""
        await self.controller.handle_switch(message)

    async def _handle_params_messages(self, message: types.Message) -> None:
        """Обработать сообщения с параметрами."""
        user_id = message.from_user.id
        chat_id = message.chat.id
        state = await self._get_state(user_id)
        
        if state in self.controller.config.STATES_CONFIG:    
            await self.edit_message_reply_markup(
                chat_id=chat_id,
                message_id=self.keyboard_message_id
            )        
            await self.controller.handle_state_input(user_id, chat_id, message.text.strip(), state) 
        elif state == RuntimeStates.state_post_text:
            await self.controller.handle_post_text(user_id, chat_id, message.text.strip())

    async def _handle_dialog_message(self, message: types.Message) -> None:
        """Обработать сообщения в контексте обсуждения."""
        await self.controller.handle_dialog_message(message)

    async def _handle_model_callback(self, call: types.CallbackQuery) -> None:
        """Обработать callback выбора модели."""
        try:
            await self.controller.change_model(call.from_user.id, call.data, call.message.message_id)
        except ValueError as e:
            await self.send_message(call.message.chat.id, str(e))

    async def _handle_analyze_callback(self, call: types.CallbackQuery) -> None:
        """Обработать callback кнопки анализа."""
        fake_message = types.Message(
            message_id=call.message.message_id,
            from_user=call.from_user,
            chat=call.message.chat,
            date=call.message.date,
            content_type='text',
            options={},
            json_string=''
        )
        fake_message.text = '/analyze'
        await self._handle_analyze(fake_message)

    async def _handle_general_callback(self, call: types.CallbackQuery) -> None:
        """Обработать общие callback-запросы."""
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        state = await self._get_state(user_id)

        if state in self.controller.config.STATES_CONFIG:
            await self.edit_message_text(
                chat_id=chat_id,
                message_id=call.message.message_id,
                text=f'Выбрано: {call.data}'
            )
            await self.controller.handle_state_input(user_id, chat_id, call.data, state)        