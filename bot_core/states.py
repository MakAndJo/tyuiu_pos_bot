# new feature for states.
from telebot.asyncio_handler_backends import State, StatesGroup

class UserState(StatesGroup):
  start = State()
  approve = State()
  set_edu_form = State()
  set_edu_direction = State()
  set_edu_type = State()
  set_edu_orgs = State()
  set_edu_discplines = State()
  set_user_mark = State()
  set_use_origs = State()
  check_pos = State()