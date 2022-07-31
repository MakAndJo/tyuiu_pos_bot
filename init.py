from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_filters import StateFilter
from telebot.asyncio_storage import StatePickleStorage
from constants import TOKEN

bot: AsyncTeleBot

def init_bot():
  state_storage: StatePickleStorage = StatePickleStorage(file_path="./.state.pkl")
  global bot
  bot = AsyncTeleBot(TOKEN, state_storage=state_storage)
  bot.add_custom_filter(StateFilter(bot))
