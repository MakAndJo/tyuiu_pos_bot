
import json
from telebot.types import Message, ReplyKeyboardMarkup, ReplyKeyboardRemove
from bot_core.states import UserState
from bot_core.cmd import cmd_eduforms, cmd_directions, cmd_edutype, cmd_orgs, cmd_disciplines
import init

def init_state_store(data):
  if not "eduforms" in data:
    data["eduforms"] = []
  if not "directions" in data:
    data["directions"] = []
  if not "edutypes" in data:
    data["edutypes"] = []
  if not "orgs" in data:
    data["orgs"] = []
  if not "payloads" in data:
    data["payloads"] = []
  if not "payload_step" in data:
    data["payload_step"] = 0
  if not "mark" in data:
    data["mark"] = 0
  if not "with_originals" in data:
    data["with_originals"] = False
  return True

async def start(message: Message):
  await init.bot.set_state(message.from_user.id, UserState.start)
  markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True, selective=True)
  markup.add("Погнали!")
  await init.bot.send_message(message.chat.id, f'Привет {message.from_user.first_name}!\xa0' +
    'Я бот для получения данных о позиции в ТИУ!\n' +
    'Начнём?\n', reply_markup=markup)
  async with init.bot.retrieve_data(message.from_user.id) as data:
    init_state_store(data)
    return await init.bot.set_state(message.from_user.id, UserState.approve)

async def approve(message: Message):
  async with init.bot.retrieve_data(message.from_user.id) as data:
    if not "name" in data:
      data['name'] = message.from_user.first_name
      data['id'] = message.from_user.id
      await init.bot.send_message(message.chat.id, "Окей. Начнём с заполнения твоих предпочтений!", reply_markup=ReplyKeyboardRemove())
    if "name" in data:
      #await init.bot.send_message(message.chat.id, "Окей. Давай продолжим...", reply_markup=ReplyKeyboardRemove())
      print("User exists")
      if len(data["eduforms"]) == 0:
        print("User has no eduforms")
        return await cmd_eduforms.send_eduforms_raw(message.from_user.id)
      if len(data["directions"]) == 0:
        print("User has no directions")
        return await cmd_directions.send_directions_raw(message.from_user.id)
      if len(data["edutypes"]) == 0:
        print("User has no edutypes")
        return await cmd_edutype.send_edutypes_raw(message.from_user.id)
      if len(data["orgs"]) == 0:
        print("User has no orgs")
        return await cmd_orgs.send_orgs_raw(message.from_user.id)
      if len(data["payloads"]) == 0 or len([e for e in data["payloads"] if len(e["disciplines"])]) != len(data["payloads"]):
        print("User has no payloads or partial filled")
        return await cmd_disciplines.send_disciplines_raw(message.from_user.id)
      return False
    return False

async def send_state(message: Message):
  async with init.bot.retrieve_data(message.from_user.id) as data:
    await init.bot.send_message(message.chat.id, f'State:\n{json.dumps(data, indent=2, ensure_ascii=False)}')

async def send_me(message: Message):
  me = {
    "id": message.from_user.id,
    "first_name": message.from_user.first_name,
    "last_name": message.from_user.last_name,
    "state": await init.bot.get_state(message.from_user.id),
  }
  ob = '\n'.join(map(lambda e: str(f"<b>{e[0]}</b>: {e[1]}"), me.items()))
  await init.bot.send_message(message.chat.id, f"Me:\n{ob}", parse_mode="html")
