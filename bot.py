import logging
from multiprocessing.connection import answer_challenge

from openai import models, azure_endpoint
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram._utils import markup
from telegram.ext import (ApplicationBuilder, CallbackQueryHandler,
                          ContextTypes, CommandHandler )
from config import TG_TOKEN, GPT_TOKEN
from gpt import ChatGptService
from util import (load_message, send_text, send_image, show_main_menu,
                  default_callback_handler, load_prompt, send_text_buttons)

# logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


#commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = load_message('main')
    await send_image(update, context, 'main')
    await send_text(update, context, text)
    await show_main_menu(update, context, {
        'start': 'Главное меню',
        'random': 'Узнать случайный интересный факт 🧠',
        'gpt': 'Задать вопрос чату GPT 🤖',
        'talk': 'Поговорить с известной личностью 👤',
        'quiz': 'Поучаствовать в квизе ❓'
    })


async def random_fact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['usr_choice'] = 'random'
    await send_image(update, context, context.user_data.get('usr_choice'))
    await send_text(update, context, load_message(context.user_data.get('usr_choice')))
    answer = await chat_gpt.send_question(load_prompt(context.user_data.get('usr_choice')),'')
    await send_text_buttons(update, context, answer, {
        'random_more': 'Хочу еще факт',
        'stop': 'Закончить'
    })


async def random_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await random_fact(update, context)

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await start(update, context)


async def gpt_talk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass


# user reply handler

app = ApplicationBuilder().token(TG_TOKEN).build()
chat_gpt = ChatGptService(GPT_TOKEN)


# Command Handlers
app.add_handler(CommandHandler('start', start))
app.add_handler(CommandHandler('random', random_fact))
#app.add_handler(CommandHandler('gpt', gpt_talk))


# Callback Handlers
app.add_handler(CallbackQueryHandler(random_buttons, pattern='random_more'))
app.add_handler(CallbackQueryHandler(stop, pattern='stop'))
app.add_handler(CallbackQueryHandler(default_callback_handler))

app.run_polling()
