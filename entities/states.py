from telebot.handler_backends import State, StatesGroup

class RuntimeStates(StatesGroup):
    """Состояния выполнения для управления процессом анализа поста."""
    state_none = State()
    state_platform = State()
    state_audience = State()
    state_purpose = State()
    state_post_text = State()
    state_blog_type = State()
    state_discusse = State()