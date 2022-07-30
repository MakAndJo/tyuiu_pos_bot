import asyncio

from bot_core import handlers
import init


async def main():
  try:
    print("Bot is running")
    await init.bot.polling(skip_pending=True, timeout=0, interval=0, none_stop=True)
  except Exception as e:
    print(f"Exception caught: {e}")


if __name__ == "__main__":
  try:
    init.init_bot()
    handlers.init_handlers()
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()
  except KeyboardInterrupt:
    pass
