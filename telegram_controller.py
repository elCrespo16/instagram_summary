import os
import logging
import telebot
from utils import Singleton
from commands import CommandResponse


logger = logging.getLogger(__name__)
ConsoleOutputHandler = logging.StreamHandler()
logger.addHandler(ConsoleOutputHandler)
logger.setLevel(logging.INFO)


class TelegramController(metaclass=Singleton):
    def __init__(self, update_id=None):
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN', "")
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID', "")
        self.bot = telebot.TeleBot(bot_token)
        self.update_id = update_id

    def notify(self, message) -> None:
        if not message:
            return
        try:
            self.bot.send_message(self.chat_id, message)
            logger.info(message)
        except Exception as e:
            logger.info(f"Could not send Telegram message {e}")

    def get_new_messages(self) -> list[telebot.types.Update]:
        try:
            return self.bot.get_updates(offset=self.update_id)
        except Exception as e:
            logger.info(f"Could not get Telegram messages {e}")
            return []

    def reply(self, message: telebot.types.Message, response: CommandResponse):
        if not message:
            return
        try:
            self.bot.reply_to(message, response)
        except Exception as e:
            logger.info(
                f"Could not reply to Telegram message {message.text} command {response} {e}")
