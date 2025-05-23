import os
from dataclasses import dataclass
from typing import Dict, List
from dotenv import load_dotenv
from entities.states import RuntimeStates

load_dotenv()

@dataclass
class Config:
    """Класс конфигурации для приложения."""
    
    TELEGRAM_API_TOKEN: str = os.getenv('TELEGRAM_API_TOKEN')
    PROXY_API_KEY: str = os.getenv('PROXY_API_KEY')
    FIREBASE_API_KEY_PATH: str = os.getenv('FIREBASE_API_KEY_PATH')
    ADMIN_ID: int = int(os.getenv('ADMIN_ID'))

    MODELS: Dict[str, List[str]] = None
    API_URLS: Dict[str, str] = None
    KEYBOARD_DATA: Dict[RuntimeStates, List[str]] = None
    STATES_CONFIG: Dict[RuntimeStates, Dict] = None

    def __post_init__(self):
        """Инициализировать комплексные поля после основной инициализации."""
        self.MODELS = {
            'ChatGPT': [
                'gpt-4.1-2025-04-14',
                'gpt-4.1-mini-2025-04-14',
                'gpt-4.1-nano-2025-04-14',
                'gpt-4o-mini-2024-07-18',
                'gpt-4o-2024-11-20',
                'gpt-3.5-turbo-0125'
            ],
            'DeepSeek': [
                'deepseek-chat',
                'deepseek-reasoner'
            ],
            'Gemini': [
                'gemini-2.0-flash',
                'gemini-2.0-flash-lite',
                'gemini-1.5-pro'
            ]
        }

        self.API_URLS = {
            'ChatGPT': 'https://api.proxyapi.ru/openai/v1',
            'DeepSeek': 'https://api.proxyapi.ru/deepseek',
            'Gemini': 'https://api.proxyapi.ru/google/v1beta',
            'balance': 'https://api.proxyapi.ru/proxyapi/balance'
        }

        self.KEYBOARD_DATA = {
            RuntimeStates.state_platform: ['Telegram', 'Twitter (X)', 'Reddit', 'Threads'],
            RuntimeStates.state_blog_type: ['СМИ', 'Личный блог', 'Научный блог'],
            RuntimeStates.state_purpose: ['Информирование', 'Образование', 'Развлечение', 'Реклама'],
            RuntimeStates.state_audience: ['Население', 'Молодёжь', 'Специалисты']
        }

        self.STATES_CONFIG = {
            RuntimeStates.state_platform: {
                'text': 'Выберите или напишите платформу для публикации.',
                'next': RuntimeStates.state_blog_type,
                'field': 'platform',
                'keyboard': self.KEYBOARD_DATA[RuntimeStates.state_platform],
            },
            RuntimeStates.state_blog_type: {
                'text': 'Выберите или напишите тип своего блога.',
                'next': RuntimeStates.state_purpose,
                'field': 'blog_type',
                'keyboard': self.KEYBOARD_DATA[RuntimeStates.state_blog_type],
            },
            RuntimeStates.state_purpose: {
                'text': 'Выберите или напишите цель публикации.',
                'next': RuntimeStates.state_audience,
                'field': 'purpose',
                'keyboard': self.KEYBOARD_DATA[RuntimeStates.state_purpose],
            },
            RuntimeStates.state_audience: {
                'text': 'Выберите или напишите тип аудитории.',
                'next': RuntimeStates.state_post_text,
                'field': 'audience',
                'keyboard': self.KEYBOARD_DATA[RuntimeStates.state_audience],
            },
        }

config = Config()

