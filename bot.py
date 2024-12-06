import logging
from random import choice

from platformdirs import user_runtime_dir
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
    level=logging.DEBUG
)
logging.getLogger('httpx').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


#commands
#start menu
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['usr_choice'] = 'main'
    await send_image(update, context, context.user_data['usr_choice'])
    await send_text(update, context, load_message(context.user_data[
                                                      'usr_choice']))


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
    await send_image(update, context, context.user_data['usr_choice'])
    await send_text(update, context, load_message(context.user_data[
                                                      'usr_choice']))
    answer = await (chat_gpt.send_question
                    (load_prompt(context.user_data['usr_choice']),''))
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


#talk to the famous person
async def talk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['usr_choice'] = 'talk'
    text = load_message(context.user_data['usr_choice'])
    await send_image(update, context, context.user_data['usr_choice'])
    print(context.user_data['usr_choice'])
    await send_text_buttons(update, context, text,
                            context.user_data['usr_choice'])


#talk buttons
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



#quiz level 1 - choose the theme
async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['usr_choice'] = 'quiz'
    context.user_data['score'] = 0
    chat_gpt.set_prompt(load_prompt(context.user_data.get('usr_choice')))
    await send_image(update, context, context.user_data.get('usr_choice'))
    await send_text_buttons(update, context, 'Выбери тему',
                            context.user_data['usr_choice'])


app = ApplicationBuilder().token(TG_TOKEN).build()


# Command Handlers
app.add_handler(CommandHandler('start', start))
app.add_handler(CommandHandler('random', random_fact))
app.add_handler(CommandHandler('gpt', gpt_talk))
app.add_handler(CommandHandler('talk', talk))


# Callback Handlers
app.add_handler(CallbackQueryHandler(random_buttons, pattern='random_more'))
app.add_handler(CallbackQueryHandler(talk_buttons, pattern='^talk_.*'))
app.add_handler(CallbackQueryHandler(stop, pattern='stop'))

#Message Handlers
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,
                               message_handler))

# Conversation handler for quiz command

# Constants for the state of the conversation
CHOOSE_THEME, ASK_QUESTION, HANDLE_ANSWER, MENU_OPTIONS = range(4)


# Asynchronous functions to support the conversation

async def start_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начальное меню"""
    context.user_data['usr_choice'] = 'quiz'
    chat_gpt.set_prompt(await load_prompt(context.user_data['usr_choice']))
    context.user_data['score'] = 0
    await send_image(update, context, context.user_data['usr_choice'])
    await send_text_buttons(update, context, load_message(
        context.user_data['usr_choice']), context.user_data['usr_choice'])
    return CHOOSE_THEME


async def choose_theme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает выбор темы """
    context.user_data['chosen_theme'] = update.callback_query.data
    await send_text(update, context, context.user_data['chosen_theme'])
    return await ask_question(update, context)


async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """генерирует и задает вопрос"""
    question = await chat_gpt.add_message(context.user_data['chosen_theme'])
    await send_text(update, context, question)
    return HANDLE_ANSWER


async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Evaluate the user's answer and present options for the next step"""
    if not update.message or not update.message.text:
        await send_text(update, context, "Введите текстовый ответ.")
        return HANDLE_ANSWER
    user_answer = update.message.text
    evaluation_message = await chat_gpt.add_message(user_answer)

    if "Правильно!" in evaluation_message:
        context.user_data['score'] += 1

    await send_text(update, context, evaluation_message)
    await send_text_buttons(update, context,
                            f'Правильных ответов: '
                            f'{context.user_data["score"]}\n' 
                            'Что вы хотите делать дальше?',
                            'next_question_options')
    return MENU_OPTIONS


async def menu_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user choice to answer another question, change, or end quiz"""
    await update.callback_query.answer()
    selected_option = update.callback_query.data

    if selected_option == 'another_question':
        return await ask_question(update, context)
    elif selected_option == 'change_theme':
        return await start_quiz(update, context)
    else:  # End quiz
        await send_text(update, context, "Спасибо за участие в квизе!")
        return ConversationHandler.END


# Adding the quiz conversation handler to the application
app.add_handler(ConversationHandler(
    entry_points=[CommandHandler('quiz', start_quiz)],
    states={
        CHOOSE_THEME: [CallbackQueryHandler(choose_theme, pattern='^quiz_.*')],
        ASK_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND,
                                      ask_question)],
        HANDLE_ANSWER: [MessageHandler(filters.TEXT, handle_answer)],
        MENU_OPTIONS: [CallbackQueryHandler(menu_options,
                                            pattern='^next_question_options')]
    },
    fallbacks=[CommandHandler('stop', stop)]))


app.add_handler(CallbackQueryHandler(default_callback_handler))

app.run_polling()
