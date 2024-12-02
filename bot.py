import logging
from dataclasses import dataclass
from gettext import textdomain

from telegram import Update
from telegram.ext import (ApplicationBuilder, CallbackQueryHandler,
                          ContextTypes, CommandHandler, MessageHandler, filters)
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
    context.user_data['usr_choice'] = 'main'
    await send_image(update, context, context.user_data.get('usr_choice'))
    await send_text(update, context, load_message(context.user_data.get
                                                  ('usr_choice'))
                    )
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
    await send_text(update, context, load_message(context.user_data.get(
        'usr_choice')))
    answer = await (chat_gpt.send_question
                    (load_prompt(context.user_data.get('usr_choice')),
                     '')
                    )
    await send_text_buttons(update, context, answer, {
        'random_more': 'Хочу еще факт',
        'stop': 'Закончить'
    })


async def random_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('usr_choice') != 'random':
        return
    await update.callback_query.answer()
    await random_fact(update, context)


async def gpt_talk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['usr_choice'] = 'gpt'
    chat_gpt.set_prompt(load_prompt(context.user_data.get('usr_choice')))
    text = load_message(context.user_data.get('usr_choice'))
    await send_image(update, context, context.user_data.get('usr_choice'))
    await send_text(update, context, text)


async def gpt_dialog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    request = update.message.text
    message = await send_text(update, context, 'Thinking...')
    answer = await chat_gpt.add_message(request)
    await message.delete()
    await send_text_buttons(update, context, answer, buttons={'stop':
                                                                  'Завершить'})

async def talk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['usr_choice'] = 'talk'
    text = load_message(context.user_data.get('usr_choice'))
    await send_image(update, context, context.user_data.get('usr_choice'))
    await send_text_buttons(update, context, text, buttons={
        'talk_cobain': 'Курт Кобейн',
        'talk_hawking': 'Стивен Хокинг',
        'talk_nietzche': 'Фридрих Ницше',
        'talk_queen': 'Елизавета II',
        'talk_tolkien': 'Джон Толкиен'
    })


async def talk_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('usr_choice') != 'talk':
        return
    await update.callback_query.answer()
    data = update.callback_query.data
    chat_gpt.set_prompt(load_prompt(data))
    await send_image(update, context, data)
    greet = await chat_gpt.add_message('Поздоровайся со мной')
    await send_text(update, context, greet)


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    match context.user_data.get('usr_choice'):
        case 'main':
            await start(update, context)
        case 'random':
            await start(update, context)
        case 'gpt':
            await gpt_dialog(update, context)
        case 'talk':
            await gpt_dialog(update, context)


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await start(update, context)


app = ApplicationBuilder().token(TG_TOKEN).build()
chat_gpt = ChatGptService(GPT_TOKEN)


# Command Handlers
app.add_handler(CommandHandler('start', start))
app.add_handler(CommandHandler('random', random_fact))
app.add_handler(CommandHandler('gpt', gpt_talk))
app.add_handler(CommandHandler('talk', talk))


# Callback Handlers
app.add_handler(CallbackQueryHandler(random_buttons, pattern='random_more'))
app.add_handler(CallbackQueryHandler(talk_buttons, pattern='talk_.*'))
app.add_handler(CallbackQueryHandler(stop, pattern='stop'))
app.add_handler(CallbackQueryHandler(default_callback_handler))

#Message Handlers
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,
                               message_handler))

app.run_polling()
