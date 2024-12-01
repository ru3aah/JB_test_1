from telegram import Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, ContextTypes, \
    CommandHandler
from config import TG_TOKEN, GPT_TOKEN
from gpt import ChatGptService
from util import (load_message, send_text, send_image, show_main_menu,
                  default_callback_handler, load_prompt)


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


async  def random_fact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usr_choice = 'random'
    await send_image(update, context, usr_choice)
    await send_text(update, context, load_message(usr_choice))
    chat_gpt.set_prompt(load_prompt(usr_choice))
    await update.message.reply_text(await chat_gpt.send_message_list())

app = ApplicationBuilder().token(TG_TOKEN).build()
chat_gpt = ChatGptService(GPT_TOKEN)

#command handlers
app.add_handler(CommandHandler('start', start))
app.add_handler(CommandHandler('random', random_fact))





# Зарегистрировать обработчик коллбэка можно так:
# app.add_handler(CallbackQueryHandler(app_button, pattern='^app_.*'))
app.add_handler(CallbackQueryHandler(default_callback_handler))

app.run_polling()

