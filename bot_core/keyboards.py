from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from constants import tyuiu_orgs, edu_forms, edu_directions, edu_types

def chunks(xs, n):
  n = max(1, n)
  return (xs[i:i+n] for i in range(0, len(xs), n))

def build_orgs_markup(user_orgs: list):
  markup = InlineKeyboardMarkup()
  markup.row_width = 1
  for i, (index, org) in enumerate(tyuiu_orgs.items()):
    markup.add(InlineKeyboardButton(f"{'✅' if index in user_orgs else ''}\xa0{org}", callback_data=f"org={index}"))
  #markup.add(InlineKeyboardButton("Все", callback_data="org=all"))
  markup.add(InlineKeyboardButton(f"Продолжить\xa0{'➡️' if len(user_orgs) > 0 else ''}", callback_data="org-next"))
  return markup

def build_edutypes_markup(user_edutypes: list):
  markup = InlineKeyboardMarkup()
  row = []
  for i, (index, edutype) in enumerate(edu_types.items()):
    row.append(InlineKeyboardButton(f"{'✅' if index in user_edutypes else ''}\xa0{edutype}", callback_data=f"edutype={index}"))
  rows = list(chunks(row, 2))
  for row in rows:
    markup.add(*row)
  markup.add(InlineKeyboardButton(f"Продолжить\xa0{'➡️' if len(user_edutypes) > 0 else ''}", callback_data="edutype-next"))
  return markup

def build_eduforms_markup(user_eduforms: list):
  markup = InlineKeyboardMarkup()
  row = []
  for i, (index, eduform) in enumerate(edu_forms.items()):
    row.append(InlineKeyboardButton(f"{'✅' if index in user_eduforms else ''}\xa0{eduform}", callback_data=f"eduform={index}"))
  markup.add(*row)
  markup.add(InlineKeyboardButton(f"Продолжить\xa0{'➡️' if len(user_eduforms) > 0 else ''}", callback_data="eduform-next"))
  return markup

def build_directions_markup(user_direction: list):
  markup = InlineKeyboardMarkup()
  row = []
  for i, (index, direction) in enumerate(edu_directions.items()):
    row.append(InlineKeyboardButton(f"{'✅' if index in user_direction else ''}\xa0{direction}", callback_data=f"direction={index}"))
  markup.add(*row)
  markup.add(InlineKeyboardButton(f"Продолжить\xa0{'➡️' if len(user_direction) > 0 else ''}", callback_data="direction-next"))
  return markup

def build_disciplines_markup(user_disciplines: list, disciplines: list):
  markup = InlineKeyboardMarkup()
  markup.row_width = 1
  for index, discipline in enumerate(disciplines):
    markup.add(InlineKeyboardButton(f"{'✅' if discipline in user_disciplines else ''}\xa0{discipline}", callback_data=f"discipline={index}"))
  markup.add(InlineKeyboardButton(f"Продолжить\xa0{'➡️' if len(user_disciplines) > 0 else ''}", callback_data="discipline-next"))
  return markup

def build_origs_markup():
  markup = InlineKeyboardMarkup()
  markup.add(InlineKeyboardButton("С оригиналами", callback_data="orig=on"), InlineKeyboardButton("Общий конкурс", callback_data="orig=off"))
  return markup
