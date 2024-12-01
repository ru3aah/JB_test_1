
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
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


async def random_fact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usr_choice = 'random'
    await send_image(update, context, usr_choice)
    await send_text(update, context, load_message(usr_choice))
    chat_gpt.set_prompt(load_prompt(usr_choice))
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("Хочу ещё факт",
                              callback_data="random_fact")],
        [InlineKeyboardButton("Закончить", callback_data="start")]
    ])

    await context.bot.send_message(update.effective_chat.id, await
    chat_gpt.send_message_list(), reply_markup=markup)

    #await update.message.reply_text(await chat_gpt.send_message_list(),
                                    #reply_markup=markup)


async def gpt_talk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usr_choice = 'gpt'
    chat_gpt.set_prompt(load_prompt(usr_choice))
    await send_image(update, context, usr_choice)
    await send_text(update, context, load_message(usr_choice))

    await update.message.reply_text(
        await chat_gpt.send_question(load_prompt(usr_choice),
                                     update.message.text))


app = ApplicationBuilder().token(TG_TOKEN).build()
chat_gpt = ChatGptService(GPT_TOKEN)


#Command handlers
app.add_handler(CommandHandler('start', start))
app.add_handler(CommandHandler('random', random_fact))
app.add_handler(CommandHandler('gpt', gpt_talk))

# Callback Handlers
app.add_handler(CallbackQueryHandler(start,'start'))
app.add_handler(CallbackQueryHandler(random_fact, 'random_fact'))
app.add_handler(CallbackQueryHandler(default_callback_handler))

app.run_polling()
