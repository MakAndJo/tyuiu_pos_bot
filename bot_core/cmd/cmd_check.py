import json
from datetime import datetime
from telebot.types import Message, CallbackQuery
from bot_core.states import UserState
from bot_core.keyboards import build_check_markup, build_origs_markup
from constants import edu_forms, edu_directions, edu_types
from tyuiu import get_tyuiu_results
import init

cached_boxes = {}

async def send_check_wrapper(message: Message):
  return await send_check_wrapper_raw(message.from_user.id, message.chat.id)

async def send_check_wrapper_raw(user_id: int, chat_id: int = None):
  if not chat_id: chat_id = user_id
  user = await init.bot.current_states.get_data(chat_id, user_id)
  if not "payloads" in user or len(user["payloads"]) == 0 or len([e for e in user["payloads"] if len(e["disciplines"])]) != len(user["payloads"]):
    return await init.bot.send_message(chat_id, "Нет дисциплин или они заполнены частично!")
  if not "mark" in user or user["mark"] == 0:
    user["mark"] = 0
    print("User has no mark set")
    return await send_mark_input_raw(user_id)
  return await send_origs_input_raw(user_id)

async def send_check_raw(user_id: int, chat_id: int = None):
  if not chat_id: chat_id = user_id
  user = await init.bot.current_states.get_data(chat_id, user_id)
  await init.bot.set_state(user_id, UserState.check_pos)
  #await init.bot.send_message(chat_id, "Запрашиваем данные с сервера...")
  for pay_i, payload in enumerate(user["payloads"]):
    if len(payload["disciplines"]) == 0: continue
    for dis_i, discipline in enumerate(payload["disciplines"]):
      msg = await init.bot.send_message(chat_id, "Загрузка данных...")
      await send_check_edit(msg, {
        'edutype': payload["edutype"],
        'eduform': payload["eduform"],
        'direction': payload["direction"],
        'org': payload["org"],
        'discipline': discipline,
        'usermark': user['mark'],
        'with_originals': user["with_originals"],
      })

async def send_check_edit(message: Message, payload: dict):
  data = get_tyuiu_results({
    'edutype': payload["edutype"],
    'eduform': payload["eduform"],
    'direction': payload["direction"],
    'org': payload["org"],
    'prof': payload["discipline"],
  }, payload["usermark"], payload["with_originals"])
  required_keys = ["pos", "prof", "budget_count", "total"]
  date = datetime.now()
  if all(x in [k for k in data] for x in required_keys):
    text = (
      f"<b>Направление подготовки:</b> {data['prof']}\n"
      f"<b>Категория:</b> {edu_directions[data['direction']]}\n"
      f"<b>Форма:</b> {edu_forms[data['eduform']]}\n"
      f"<b>Уровень образования:</b> {edu_types[data['edutype']]}\n"
      f"<b>Бюджетных мест:</b> {data['budget_count']}\n"
      f"<b>Ваша позиция:</b> {data['pos']} ({data['total']} баллов)\n"
      f"<i>Обновлено:</i> {date.strftime('%Y-%m-%d %H:%M:%S')}\n"
    )
    cached_data = {
      'edutype': payload["edutype"],
      'eduform': payload["eduform"],
      'direction': payload["direction"],
      'org': payload["org"],
      'discipline': payload["discipline"],
      'usermark': payload["usermark"],
      'with_originals': payload["with_originals"],
    }
    cached_id = hash(json.dumps(cached_data))
    cached_boxes[cached_id] = cached_data
    return await init.bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=text, parse_mode='Html', reply_markup=build_check_markup(cached_id))
  return await init.bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text='Похоже, что-то пошло не так...')


async def process_check(call: CallbackQuery):
  action = call.data.split("=")[0].split("-")[1] # check-action=cached_id
  cached_id = int(call.data.split("=")[1])
  cached = cached_boxes[cached_id]
  print(f"Processing check: {action} {json.dumps(cached, indent=2, ensure_ascii=False)}")
  if action == "reload":
    await init.bot.answer_callback_query(call.id, "Загрузка данных...")
    return await send_check_edit(call.message, cached)
  return

async def send_mark_input(message: Message):
  return await send_mark_input_raw(message.from_user.id, message.chat.id)

async def send_mark_input_raw(user_id: int, chat_id: int = None):
  if not chat_id: chat_id = user_id
  await init.bot.set_state(user_id, UserState.set_user_mark)
  return await init.bot.send_message(chat_id, "Введите свои баллы:")

async def process_input_mark(message: Message):
  mark = message.text
  if not mark.isdigit():
    return await init.bot.reply_to(message, f'"{mark}" не похоже на цифру! Дак сколько у тебя баллов?')
  elif int(mark) < 100 or int(mark) > 400:
    return await init.bot.reply_to(message, f'"{mark}" не похоже на баллы ЕГЭ! Дак сколько у тебя баллов?')
  user = await init.bot.current_states.get_data(message.chat.id, message.from_user.id)
  user["mark"] = int(mark)
  return await send_check_wrapper_raw(message.from_user.id, message.chat.id)

async def send_origs_input(message: Message):
  return await send_origs_input_raw(message.from_user.id, message.chat.id)

async def send_origs_input_raw(user_id: int, chat_id: int = None):
  if not chat_id: chat_id = user_id
  await init.bot.set_state(user_id, UserState.set_use_origs)
  markup = build_origs_markup()
  return await init.bot.send_message(chat_id, 'Смотрим с оригиналами?', reply_markup=markup)

async def process_input_origs(call: CallbackQuery):
  message = call.message
  user = await init.bot.current_states.get_data(call.message.chat.id, call.from_user.id)
  orig = call.data.split("=")[1]
  if orig == "on":
    user["with_originals"] = True
  elif orig == "off":
    user["with_originals"] = False
  else: return
  ob = f'Хорошо! Будем смотреть {"с оригиналами" if user["with_originals"] else "общий конкурс"}!'
  await init.bot.answer_callback_query(call.id, text=ob)
  await init.bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=ob, reply_markup=None)

  await send_check_raw(call.from_user.id)

  return False
