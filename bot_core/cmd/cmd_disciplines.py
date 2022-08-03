import json
from telebot.types import Message, CallbackQuery
from bot_core.states import UserState
from bot_core.keyboards import build_disciplines_markup
from bot_core.cmd import cmd_check
from constants import edu_forms, edu_directions, edu_types, tyuiu_orgs
from tyuiu import get_tyuiu_disciplines
import init

async def prebuild_payloads(eduforms: list, directions: list, edutypes: list, orgs: list):
  end = []
  for _, org in enumerate(orgs):
    for _, eduform in enumerate(eduforms):
      for _, direction in enumerate(directions):
        for _, edutype in enumerate(edutypes):
          end.append({"eduform": eduform, "direction": direction, "org": org, "edutype": edutype, "disciplines": []})
  return end

async def send_disciplines(message: Message):
  return await send_disciplines_raw(message.from_user.id)

async def send_disciplines_raw(user_id: int, chat_id: int = None):
  if not chat_id: chat_id = user_id
  await init.bot.set_state(user_id, UserState.set_edu_discplines)
  user = await init.bot.current_states.get_data(chat_id, user_id)
  if len(user["payloads"]) == 0:
    user["payloads"] = await prebuild_payloads(user["eduforms"], user["directions"], user["edutypes"], user["orgs"])
  msg = await init.bot.send_message(chat_id, "Загрузка данных...")
  return await send_discipline_select(msg, user_id)

async def send_disciplines_edit(message: Message, user_id: int):
  await init.bot.set_state(user_id, UserState.set_edu_discplines)
  user = await init.bot.current_states.get_data(user_id, user_id)
  if len(user["payloads"]) == 0:
    user["payloads"] = await prebuild_payloads(user["eduforms"], user["directions"], user["edutypes"], user["orgs"])
  await init.bot.edit_message_text("Загрузка данных...", message.chat.id, message.message_id)
  return await send_discipline_select(message, user_id)

async def send_discipline_select(message: Message, user_id: int):
  user = await init.bot.current_states.get_data(user_id, user_id)
  payload = user["payloads"][user["payload_step"]]
  disc_data = get_tyuiu_disciplines(payload["org"], payload["eduform"], payload["direction"], payload["edutype"])
  print("disc_data:", disc_data)
  markup = build_disciplines_markup(payload["disciplines"], disc_data)
  text = (
    f'*Выбор направления подготовки* - шаг {user["payload_step"] + 1} из {len(user["payloads"])}\n'
    f"*Форма обучения:*\xa0{edu_forms[payload['eduform']].lower()}\n"
    f"*Категория:*\xa0{edu_directions[payload['direction']].lower()}\n"
    f"*Уровень образования:*\xa0{edu_types[payload['edutype']].lower()}\n"
    f"*Организация:*\xa0{tyuiu_orgs[payload['org']]}\n"
  )
  return await init.bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=text, reply_markup=markup, parse_mode='Markdown')

async def process_disciplines(call: CallbackQuery):
  user = await init.bot.current_states.get_data(call.message.chat.id, call.from_user.id)
  print("process disc", json.dumps(user["payloads"], indent=2, ensure_ascii=False))
  current_payload = user["payloads"][user["payload_step"]]
  tyuiu_disciplines = get_tyuiu_disciplines(current_payload["org"], current_payload["eduform"], current_payload["direction"], current_payload["edutype"])
  user_disciplines = current_payload["disciplines"]
  if call.data != "discipline-next": # select
    discipline = call.data.split("=")[1]
    if discipline == "all":
      user_disciplines.extend(tyuiu_disciplines)
    else:
      discipline_index = int(discipline)
      discipline = tyuiu_disciplines[discipline_index]
      if discipline in user_disciplines:
        await init.bot.answer_callback_query(call.id, text=f"{discipline} убран из выбора!")
        user_disciplines.remove(discipline)
      else:
        await init.bot.answer_callback_query(call.id, text=f"{discipline} добавлен в выбор!")
        user_disciplines.append(discipline)
    await init.bot.current_states.set_data(call.message.chat.id, call.from_user.id, "payloads", user["payloads"])
    return await send_discipline_select(call.message, call.from_user.id)
  else: # next
    if len(user_disciplines) == 0: # skip discipline selection if no disciplines selected
      user["payloads"].remove(user["payloads"][user["payload_step"]])
      await init.bot.answer_callback_query(call.id, text="Пропуск выбора дисциплины")
    if user["payload_step"] < len(user["payloads"]) - 1: # if not last payload
      if len(user_disciplines) > 0: # if user selected some disciplines
        user["payload_step"] += 1
      await init.bot.current_states.set_data(call.message.chat.id, call.from_user.id, "payloads", user["payloads"])
      await init.bot.answer_callback_query(call.id, text="Загрузка следующей дисциплины...")
      await init.bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=build_disciplines_markup(user_disciplines, tyuiu_disciplines, True))
      return await send_discipline_select(call.message, call.from_user.id)
    else:
      user["payload_step"] = 0
      await init.bot.answer_callback_query(call.id, text="Выбор дисциплины завершен")
      await init.bot.current_states.set_data(call.message.chat.id, call.from_user.id, "payloads", user["payloads"])
      await init.bot.edit_message_text("Отлично! Я запомнил твой выбор!", call.message.chat.id, call.message.message_id)

      if user["in_refill_mode"]:
        user["in_refill_mode"] = False
      else:
        return await cmd_check.send_check_wrapper_raw(call.from_user.id)

      return False
