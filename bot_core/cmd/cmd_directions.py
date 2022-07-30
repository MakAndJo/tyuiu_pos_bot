from telebot.types import Message, CallbackQuery
from bot_core.states import UserState
from bot_core.keyboards import build_directions_markup
from bot_core.cmd import cmd_edutype
from constants import edu_directions
import init

async def send_directions(message: Message):
  return await send_directions_raw(message.from_user.id, message.chat.id)

async def send_directions_raw(user_id: int, chat_id: int = None):
  if not chat_id: chat_id = user_id
  await init.bot.set_state(user_id, UserState.set_edu_direction)
  user = await init.bot.current_states.get_data(chat_id, user_id)
  markup = build_directions_markup(user['directions'])
  return await init.bot.send_message(chat_id, "Выбери направление обучения:", reply_markup=markup)

async def process_directions(call: CallbackQuery):
  user = await init.bot.current_states.get_data(call.message.chat.id, call.from_user.id)
  if call.data != "direction-next":
    direction = call.data.split("=")[1]
    if direction == "all":
      user["directions"].extend(edu_directions.keys())
    else:
      dir_index = int(direction)
      if dir_index in user["directions"]:
        await init.bot.answer_callback_query(call.id, text=f"{edu_directions[dir_index]} убран из выбора!")
        user["directions"].remove(dir_index)
      else:
        await init.bot.answer_callback_query(call.id, text=f"{edu_directions[dir_index]} добавлен в выбор!")
        user["directions"].append(dir_index)
    markup = build_directions_markup(user["directions"])
    await init.bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
    print("directions:", user["directions"])
    return

  if len(user["directions"]) == 0:
    await init.bot.answer_callback_query(call.id, text="Направления не выбранны!", show_alert=True)
    return

  await init.bot.answer_callback_query(call.id, text="Направления выбранны!")
  ob = '\n'.join(map(lambda e: str(f"- *{edu_directions[e]}*"), user["directions"]))
  await init.bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"Направление:\n{ob}", parse_mode='Markdown')

  await cmd_edutype.send_edutypes_raw(call.from_user.id)

  return
