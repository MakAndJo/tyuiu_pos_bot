from telebot.types import Message, CallbackQuery
from bot_core.states import UserState
from bot_core.keyboards import build_orgs_markup
from bot_core.cmd import cmd_disciplines
from constants import tyuiu_orgs
import init

async def send_orgs(message: Message):
  return await send_orgs_raw(message.from_user.id, message.chat.id)

async def send_orgs_raw(user_id: int, chat_id: int = None):
  if not chat_id: chat_id = user_id
  await init.bot.set_state(user_id, UserState.set_edu_orgs)
  user = await init.bot.current_states.get_data(chat_id, user_id)
  markup = build_orgs_markup(user['orgs'])
  return await init.bot.send_message(chat_id, "Выбери институт:", reply_markup=markup)

async def process_orgs(call: CallbackQuery):
  user = await init.bot.current_states.get_data(call.message.chat.id, call.from_user.id)
  if call.data != "org-next":
    org = call.data.split("=")[1]
    if org == "all":
      user["orgs"].extend(tyuiu_orgs.keys())
    else:
      org_index = int(org)
      if org_index in user["orgs"]:
        await init.bot.answer_callback_query(call.id, text=f"{tyuiu_orgs[org_index]} убран из выбора!")
        user["orgs"].remove(org_index)
      else:
        await init.bot.answer_callback_query(call.id, text=f"{tyuiu_orgs[org_index]} добавлен в выбор!")
        user["orgs"].append(org_index)
    markup = build_orgs_markup(user["orgs"]) # rebuild markup
    await init.bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
    return

  if len(user["orgs"]) == 0:
    await init.bot.answer_callback_query(call.id, text="Организации не выбранны!", show_alert=True)
    return

  await init.bot.answer_callback_query(call.id, text="Организации выбраны!")
  ob = '\n'.join(map(lambda e: str(f"- *{tyuiu_orgs[e]}*"), user["orgs"]))
  await init.bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"Выбранные организации:\n{ob}", parse_mode='Markdown')

  await cmd_disciplines.send_disciplines_raw(call.from_user.id)

  return
