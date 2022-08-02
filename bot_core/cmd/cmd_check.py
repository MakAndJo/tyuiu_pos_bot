from telebot.types import Message, CallbackQuery
from bot_core.states import UserState
from bot_core.keyboards import build_origs_markup
from constants import edu_forms, edu_directions, edu_types
from tyuiu import get_tyuiu_results
import init

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
  for _, payload in enumerate(user["payloads"]):
    print("Checking payload", payload)
    if len(payload["disciplines"]) == 0: continue
    for _, discipline in enumerate(payload["disciplines"]):
      msg = await init.bot.send_message(chat_id, "Загрузка данных...")
      data = get_tyuiu_results({
        'edutype': payload["edutype"],
        'eduform': payload["eduform"],
        'direction': payload["direction"],
        'org': payload["org"],
        'prof': discipline,
      }, user["mark"], user["with_originals"])
      required_keys = ["pos", "prof", "budget_count", "total"]
      if all(x in [k for k in data] for x in required_keys):
        text = (
          f"*Направление подготовки:* {data['prof']}\n"
          f"*Категория:* {edu_directions[data['direction']]}\n"
          f"*Форма:* {edu_forms[data['eduform']]}\n"
          f"*Уровень образования:* {edu_types[data['edutype']]}\n"
          f"*Бюджетных мест:* {data['budget_count']}\n"
          f"*Ваша позиция:* {data['pos']} ({data['total']} баллов)\n"
        )
        await init.bot.edit_message_text(chat_id=msg.chat.id, message_id=msg.message_id, text=text, parse_mode='Markdown')
      else: await init.bot.edit_message_text(chat_id=msg.chat.id, message_id=msg.message_id, text='Похоже, что-то пошло не так...')


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
