from telebot.types import Message, CallbackQuery
from bot_core.states import UserState
from bot_core.keyboards import build_eduforms_markup
from bot_core.cmd import cmd_directions
from constants import edu_forms
import init



async def send_eduforms(message: Message):
  return await send_eduforms_raw(message.from_user.id, message.chat.id)

async def send_eduforms_raw(user_id: int, chat_id: int = None):
  if not chat_id: chat_id = user_id
  await init.bot.set_state(user_id, UserState.set_edu_form)
  user = await init.bot.current_states.get_data(chat_id, user_id)
  markup = build_eduforms_markup(user['eduforms'])
  return await init.bot.send_message(chat_id, "Выбери форму обучения:", reply_markup=markup)

async def process_eduforms(call: CallbackQuery):
  user = await init.bot.current_states.get_data(call.message.chat.id, call.from_user.id)
  if call.data != "eduform-next":
    eduform = call.data.split("=")[1]
    if eduform == "all":
      user["eduforms"].extend(edu_forms.keys())
    else:
      edu_index = int(eduform)
      if edu_index in user["eduforms"]:
        await init.bot.answer_callback_query(call.id, text=f"{edu_forms[edu_index]} убран из выбора!")
        user["eduforms"].remove(edu_index)
      else:
        await init.bot.answer_callback_query(call.id, text=f"{edu_forms[edu_index]} добавлен в выбор!")
        user["eduforms"].append(edu_index)
    markup = build_eduforms_markup(user["eduforms"])
    await init.bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
    print("eduforms:", user["eduforms"])
    return

  if len(user["eduforms"]) == 0:
    await init.bot.answer_callback_query(call.id, text="Формы обучения не выбранны!", show_alert=True)
    return

  await init.bot.answer_callback_query(call.id, text="Формы обучения выбранны!")

  await cmd_directions.send_directions_edit(call.message, call.from_user.id) # next step

  return
