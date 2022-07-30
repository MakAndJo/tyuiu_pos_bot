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
  for i_org, org in enumerate(orgs):
    for i_form, eduform in enumerate(eduforms):
      for i_dir, direction in enumerate(directions):
        for i_type, edutype in enumerate(edutypes):
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
  await send_discipline_select(msg, user_id)
  return True

async def send_discipline_select(message: Message, user_id: int, is_resend: bool = False):
  user = await init.bot.current_states.get_data(user_id, user_id)
  payload = user["payloads"][user["payload_step"]]
  if (not is_resend and len(payload["disciplines"]) == 0): await init.bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text="Загрузка дисциплин...")
  disc_data = get_tyuiu_disciplines(payload["org"], payload["eduform"], payload["direction"], payload["edutype"])
  markup = build_disciplines_markup(payload["disciplines"], disc_data)
  text = (
    f'*Выбор дисциплины* - шаг {user["payload_step"] + 1} из {len(user["payloads"])}\n'
    f"*Форма обучения:*\xa0{edu_forms[payload['eduform']].lower()}\n"
    f"*Направление:*\xa0{edu_directions[payload['direction']].lower()}\n"
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
  #print("process_disciplines", current_payload, tyuiu_disciplines)
  if call.data != "discipline-next":
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
    await send_discipline_select(call.message, call.from_user.id, True)
  else:
    should_continue = user["payload_step"] < len(user["payloads"]) - 1
    user_selected = len(user_disciplines) > 0
    msg = call.message
    if user_selected:
      text = (
        f"**Выбрана дисциплина:**\n"
        f"Форма обучения:\xa0*{edu_forms[current_payload['eduform']].lower()}*\n"
        f"Направление:\xa0*{edu_directions[current_payload['direction']].lower()}*\n"
        f"Уровень образования:\xa0*{edu_types[current_payload['edutype']].lower()}*\n"
        f"Организация:\xa0*{tyuiu_orgs[current_payload['org']]}*\n"
        f"Дисциплины:\n" + '\n'.join(map(lambda e: str(f"- *{e}*"), user_disciplines))
      )
      await init.bot.edit_message_text(chat_id=msg.chat.id, message_id=msg.message_id, text=text, parse_mode='Markdown')
      if should_continue: msg = await init.bot.send_message(call.message.chat.id, text="Загрузка следующих дисциплин...")
    if not should_continue and not user_selected: # if end of slections and no disciplines selected
      await init.bot.delete_message(chat_id=msg.chat.id, message_id=msg.message_id)
    if should_continue:
      if not user_selected:
        user["payloads"].remove(user["payloads"][user["payload_step"]])
        await init.bot.answer_callback_query(call.id, text="Пропуск выбора дисциплины")
      else:
        user["payload_step"] += 1
      await init.bot.answer_callback_query(call.id, text="Выбор следующей дисциплины")
      await init.bot.current_states.set_data(call.message.chat.id, call.from_user.id, "payloads", user["payloads"])
      await send_discipline_select(msg, call.from_user.id, False)
    else:
      user["payload_step"] = 0
      await init.bot.answer_callback_query(call.id, text="Выбор дисциплины завершен")
      await init.bot.current_states.set_data(call.message.chat.id, call.from_user.id, "payloads", user["payloads"])
      await init.bot.send_message(call.message.chat.id, "Отлично! Я запомнил твой выбор!")
      pld = json.dumps(user["payloads"], indent=2, ensure_ascii=False)
      print(pld)

      await cmd_check.send_check_wrapper_raw(call.from_user.id)

      # await init.bot.send_message(call.message.chat.id, 'Сколько у тебя суммарно баллов?')
      # await init.bot.register_next_step_handler(call.message, process_mark_step)
      return
