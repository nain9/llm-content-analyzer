import aiohttp

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
            url = f'{user.base_url}/models/{user.model_name}:generateContent'
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}'
            }
            
            formatted_messages = [
                {
                    'role': 'user' if message['role'] == 'user' else 'model',
                    'parts': [{'text': message['content']}]
                }
                for message in messages or user.messages
            ]
            
            data = {
                'contents': formatted_messages,
                'generationConfig': {
                    'temperature': temperature or self.temperature,
                    'frequencyPenalty': frequency_penalty or self.frequency_penalty,
                    'presencePenalty': presence_penalty or self.presence_penalty,
                    'maxOutputTokens': max_tokens or self.max_tokens
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, headers=headers) as response:
                    response_data = await response.json()

                    if response.status != 200:
                        raise Exception(f'API Error: {response_data}')
                    
                    return response_data['candidates'][0]['content']['parts'][0]['text'].replace('*', '')

        except Exception as e:
            return f'Ошибка: {str(e)}'
        