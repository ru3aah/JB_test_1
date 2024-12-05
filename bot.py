import logging

from telegram import Update
from telegram.ext import (ApplicationBuilder, CallbackQueryHandler,
                          ContextTypes, CommandHandler, MessageHandler, filters,
                          ConversationHandler)
from config import TG_TOKEN
from config import chat_gpt
from util import (load_message, send_text, send_image, show_main_menu,
                  default_callback_handler, load_prompt, send_text_buttons,
                  gpt_dialog)

# logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logging.getLogger('httpx').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


#commands
#start menu
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['usr_choice'] = 'main'
    await send_image(update, context, context.user_data.get('usr_choice'))
    await send_text(update, context, load_message(context.user_data.get
                                                  ('usr_choice')))


    await show_main_menu(update, context, {
        'start': 'Главное меню',
        'random': 'Узнать случайный интересный факт 🧠',
        'gpt': 'Задать вопрос чату GPT 🤖',
        'talk': 'Поговорить с известной личностью 👤',
        'quiz': 'Поучаствовать в квизе ❓'
    })

#random fact
async def random_fact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['usr_choice'] = 'random'
    await send_image(update, context, context.user_data.get('usr_choice'))
    await send_text(update, context, load_message(context.user_data.get(
        'usr_choice')))
    answer = await (chat_gpt.send_question
                    (load_prompt(context.user_data.get('usr_choice')),'')
                    )
    await send_text_buttons(update, context, answer, context.user_data[
        'usr_choice'])


async def random_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('usr_choice') != 'random':
        return
    await update.callback_query.answer()
    await random_fact(update, context)


#gpt talk
async def gpt_talk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['usr_choice'] = 'gpt'
    chat_gpt.set_prompt(load_prompt(context.user_data.get('usr_choice')))
    text = load_message(context.user_data.get('usr_choice'))
    await send_image(update, context, context.user_data.get('usr_choice'))
    await send_text(update, context, text)


# talk to the famous person
async def talk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['usr_choice'] = 'talk'
    text = load_message(context.user_data['usr_choice'])
    await send_image(update, context, context.user_data['usr_choice'])
    print(context.user_data['usr_choice'])
    await send_text_buttons(update, context, text,
                            context.user_data['usr_choice'])


#buttons
async def talk_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data['usr_choice'] != 'talk':
        return
    await update.callback_query.answer()
    data = update.callback_query.data
    chat_gpt.set_prompt(load_prompt(data))
    await send_image(update, context, data)
    greet = await chat_gpt.add_message('Поздоровайся со мной')
    await send_text(update, context, greet)


#message handler
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

CHOOSE_THEME, DIFF, ANSWER = range(3)

async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['usr_choice'] = 'quiz'
    context.user_data['score'] = 0
    chat_gpt.set_prompt(load_prompt(context.user_data.get('usr_choice')))
    await send_image(update, context, context.user_data.get('usr_choice'))
    await send_text_buttons(update, context, 'Выбери тему',
                            context.user_data['usr_choice'])
    return CHOOSE_THEME


async def quiz_theme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    question = await chat_gpt.add_message(update.callback_query.data)
    await send_text(update, context, question)
    return ANSWER

async def quiz_diff(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass


async def quiz_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    answer = await chat_gpt.add_message(text)
    if answer == 'Правильно!':
        context.user_data['score'] = context.user_data.get('score', 0) + 1
    await send_text_buttons(update, context, answer + '\n правильных ответов: ' +
                            str(context.user_data.get('score', 0)), buttons={
        'quiz_more': 'Next question',
        'quiz_change': 'Сменить тему',
        'stop': 'Завершить'

    })

    return ConversationHandler.END




app = ApplicationBuilder().token(TG_TOKEN).build()


# Command Handlers
app.add_handler(CommandHandler('start', start))
app.add_handler(CommandHandler('random', random_fact))
app.add_handler(CommandHandler('gpt', gpt_talk))
app.add_handler(CommandHandler('talk', talk))
app.add_handler(CommandHandler('quiz', quiz))


# Callback Handlers
app.add_handler(CallbackQueryHandler(random_buttons, pattern='random_more'))
app.add_handler(CallbackQueryHandler(talk_buttons, pattern='talk_.*'))
app.add_handler(CallbackQueryHandler(stop, pattern='stop'))

#Message Handlers
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,
                               message_handler))
#ConversationHandler
app.add_handler(ConversationHandler(
    entry_points=[CommandHandler('quiz', quiz)],
    states={
        CHOOSE_THEME: [CallbackQueryHandler(quiz_theme, pattern='^quiz_.*')],
        DIFF: [CallbackQueryHandler(quiz_diff, pattern='^diff_.*')],
        ANSWER: [MessageHandler(filters.TEXT & ~filters.COMMAND,
                                quiz_answer), CallbackQueryHandler(
            quiz_theme, pattern='quiz_more'),
                 CallbackQueryHandler(quiz, pattern='quiz_change'),
                 CallbackQueryHandler(stop, pattern='stop'),
                 CallbackQueryHandler(quiz_theme, pattern='quiz_more')]
    },
    fallbacks=[CommandHandler('stop', stop)
               ]

))

app.add_handler(CallbackQueryHandler(default_callback_handler))

app.run_polling()
