from views.telegram_view import TelegramView
from controllers.app_controller import AppController
from config import config
import asyncio

async def main():
	
	view = TelegramView(config.TELEGRAM_API_TOKEN)
	controller = AppController(view, config)
	await controller.start()

if __name__ == '__main__':
	asyncio.run(main())