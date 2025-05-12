from views.telegram_view import TelegramView
from controllers.app_controller import AppController
from config import TELEGRAM_API_TOKEN, PROXY_API_KEY, ADMIN_ID, models, state_config, FIREBASE_API_KEY_PATH, API_URLS
import asyncio

async def main():
	view: TelegramView = TelegramView(TELEGRAM_API_TOKEN)

	config = {
		'ADMIN_ID': ADMIN_ID,
		'PROXY_API_KEY': PROXY_API_KEY,
		'FIREBASE_API_KEY_PATH': FIREBASE_API_KEY_PATH,
		'API_URLS': API_URLS,
		'models': models,
		'state_config': state_config
	}
	
	controller = AppController(view, config)
	await view.start_polling()

if __name__ == '__main__':
	asyncio.run(main())