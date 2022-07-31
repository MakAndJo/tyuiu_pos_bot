#-*- coding: utf-8 -*-

# noinspection PyUnresolvedReferences
import init
from telebot.async_telebot import AsyncTeleBot

"""
Определяем тип для глобальной переменной (Если плохо определяется в IDE, то удалите и вставьте текст в этот файл заново. Баг Python)
"""


init.init_bot: init.init_bot
init.bot: AsyncTeleBot
