from bot_core.states import UserState
from bot_core import cmd
import init

def init_handlers():

  init.bot.register_message_handler(cmd.cmd_start.send_me, commands='me', state="*")
  init.bot.register_message_handler(cmd.cmd_start.send_state, commands='state', state="*")
  init.bot.register_message_handler(cmd.cmd_start.start_refill, commands='refill', state="*", chat_types=['private'])
  init.bot.register_message_handler(cmd.cmd_check.send_check_wrapper, commands='check_pos', state="*", chat_types=['private'])

  init.bot.register_message_handler(cmd.cmd_start.start, commands=['start'], chat_types=['private'])
  init.bot.register_message_handler(cmd.cmd_start.approve, state=UserState.approve, chat_types=['private'])

  init.bot.register_message_handler(cmd.cmd_eduforms.send_eduforms, state=UserState.set_edu_form, chat_types=['private'])
  init.bot.register_callback_query_handler(cmd.cmd_eduforms.process_eduforms, state=UserState.set_edu_form, func=lambda call: "eduform" in call.data)

  init.bot.register_message_handler(cmd.cmd_directions.send_directions, state=UserState.set_edu_direction, chat_types=['private'])
  init.bot.register_callback_query_handler(cmd.cmd_directions.process_directions, state=UserState.set_edu_direction, func=lambda call: "direction" in call.data)

  init.bot.register_message_handler(cmd.cmd_edutype.send_edutypes, state=UserState.set_edu_type, chat_types=['private'])
  init.bot.register_callback_query_handler(cmd.cmd_edutype.process_edutype, state=UserState.set_edu_type, func=lambda call: "edutype" in call.data)

  init.bot.register_message_handler(cmd.cmd_orgs.send_orgs, state=UserState.set_edu_orgs, chat_types=['private'])
  init.bot.register_callback_query_handler(cmd.cmd_orgs.process_orgs, state=UserState.set_edu_orgs, func=lambda call: "org" in call.data)

  init.bot.register_message_handler(cmd.cmd_disciplines.send_disciplines, state=UserState.set_edu_discplines, chat_types=['private'])
  init.bot.register_callback_query_handler(cmd.cmd_disciplines.process_disciplines, state=UserState.set_edu_discplines, func=lambda call: "discipline" in call.data)

  init.bot.register_message_handler(cmd.cmd_check.process_input_mark, state=UserState.set_user_mark, chat_types=['private'])
  init.bot.register_callback_query_handler(cmd.cmd_check.process_input_origs, state=UserState.set_use_origs, func=lambda call: "orig" in call.data)


  async def handle_text(message):
    await init.bot.set_state(message.from_user.id, UserState.start, message.chat.id)
    await init.bot.send_message(message.chat.id, message.text)
  init.bot.register_message_handler(handle_text)

  return True
