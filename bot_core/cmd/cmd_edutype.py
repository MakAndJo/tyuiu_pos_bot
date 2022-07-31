from telebot.types import Message, CallbackQuery
from bot_core.states import UserState
from bot_core.keyboards import build_edutypes_markup
from bot_core.cmd import cmd_orgs
from constants import edu_types
import init

async def send_edutypes(message: Message):
  return await send_edutypes_raw(message.from_user.id, message.chat.id)

async def send_edutypes_raw(user_id: int, chat_id: int = None):
  if not chat_id: chat_id = user_id
  await init.bot.set_state(user_id, UserState.set_edu_type)
  user = await init.bot.current_states.get_data(chat_id, user_id)
  markup = build_edutypes_markup(user['edutypes'])
  return await init.bot.send_message(chat_id, "Выбери уровень образования:", reply_markup=markup)

async def send_edutypes_edit(message: Message, user_id: int):
  await init.bot.set_state(user_id, UserState.set_edu_type)
  user = await init.bot.current_states.get_data(user_id, user_id)
  markup = build_edutypes_markup(user['edutypes'])
  return await init.bot.edit_message_text("Выбери уровень образования:", message.chat.id, message.message_id, reply_markup=markup)

async def process_edutype(call: CallbackQuery):
  user = await init.bot.current_states.get_data(call.message.chat.id, call.from_user.id)
  if call.data != "edutype-next":
    edutype = call.data.split("=")[1]
    if edutype == "all":
      user["edutypes"].extend(edu_types.keys())
    else:
      edu_index = int(edutype)
      if edu_index in user["edutypes"]:
        await init.bot.answer_callback_query(call.id, text=f"{edu_types[edu_index]} убран из выбора!")
        user["edutypes"].remove(edu_index)
      else:
        await init.bot.answer_callback_query(call.id, text=f"{edu_types[edu_index]} добавлен в выбор!")
        user["edutypes"].append(edu_index)
    markup = build_edutypes_markup(user["edutypes"])
    await init.bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
    return

  if len(user["edutypes"]) == 0:
    await init.bot.answer_callback_query(call.id, text="Уровни образования не выбранны!", show_alert=True)
    return

  await init.bot.answer_callback_query(call.id, text="Уровни образования выбранны!")
  
  await cmd_orgs.send_orgs_edit(call.message, call.from_user.id)

  return
