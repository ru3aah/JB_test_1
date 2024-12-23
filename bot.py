"""
bot.py
-------

This module provides the main logic for implementing a bot application.
It includes function definitions and classes for handling bot interactions,
responses, and processing user inputs.

Modules and functionality:
- Command processing
- Event handling (e.g., chat messages or API calls)
- Response generation
- Integration with external APIs or services

Usage:
------
Import this module and initialize the bot via its corresponding setup functions
or classes. Ensure any required third-party packages are installed beforehand.

Dependencies:
-------------
- Python 3.12 or later
- ref to dependencies.txt

Author: Alexander Telenkov

"""

import logging

from telegram import Update
from telegram.ext import (ApplicationBuilder, CallbackQueryHandler,
                          ContextTypes, CommandHandler, MessageHandler, filters,
                          ConversationHandler)

from advice import (advice_conv_handler)
from config import TG_TOKEN
from config import chat_gpt
from util import (load_message, send_text, send_image, show_main_menu,
                  default_callback_handler, load_prompt, send_text_buttons,
                  gpt_dialog)

# logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - '
                           '%(message)s',
                    level=logging.DEBUG)
logging.getLogger('httpx').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


# Commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Asynchronous function to initiate a conversation with the user.

    This function sets the user's initial choice within the context, retrieves
    a corresponding message, and sends it as both an image and textual response.
    Finally, it displays the main menu with various interaction options.

    Parameters:
    - update: Update object containing information about the incoming update.
    - context: Context object containing user-specific data and bot interaction data.

    Returns:
    - ConversationHandler.END: Indicates that the conversation handler should terminate.
    """

    context.user_data['usr_choice'] = 'main'
    text = load_message(context.user_data['usr_choice'])
    await send_image(update, context, context.user_data['usr_choice'])
    await send_text(update, context, text)
    await show_main_menu(update, context,{
        'start': 'Главное меню',
        'random': 'Узнать случайный интересный факт 🧠',
        'gpt': 'Задать вопрос чату GPT 🤖',
        'talk': 'Поговорить с известной личностью 👤',
        'quiz': 'Поучаствовать в квизе ❓',
        'advice': 'Получить совет по выбору фильма, сериала или книги'
    })
    return ConversationHandler.END


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик выбора пользователя и запуск обработчика"""

    match str(context.user_data['usr_choice']):
        case 'main':
            await start(update, context)
        case 'random':
            await start(update, context)
        case 'gpt':
            await gpt_dialog(update, context)
        case 'talk':
            await gpt_dialog(update, context)


async def random_fact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Генерирует случайный факт и показывает его пользователю"""

    context.user_data['usr_choice'] = 'random'
    text = load_message(context.user_data['usr_choice'])
    await send_image(update, context, context.user_data['usr_choice'])
    await send_text(update, context, text)
    prompt = load_prompt(context.user_data['usr_choice'])
    answer = await (chat_gpt.send_question(prompt, ''))
    await send_text_buttons(update, context, answer,
                            context.user_data['usr_choice'])


async def random_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатия кнопок в меню random_fact"""

    if context.user_data.get('usr_choice') != 'random':
        return
    await update.callback_query.answer()
    await random_fact(update, context)


async def gpt_talk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Разговор с gpt начало"""

    context.user_data['usr_choice'] = 'gpt'
    text = load_message(context.user_data.get('usr_choice'))
    await send_image(update, context, context.user_data.get('usr_choice'))
    await send_text(update, context, text)
    prompt = load_prompt(context.user_data.get('usr_choice'))
    chat_gpt.set_prompt(prompt)


async def talk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Разговор с известным человеком начало"""

    context.user_data['usr_choice'] = 'talk'
    text = load_message(context.user_data['usr_choice'])
    await send_image(update, context, context.user_data['usr_choice'])
    await send_text_buttons(update, context, text,
                            context.user_data['usr_choice'])


async def talk_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ Разговор с известным человеком обработчик"""

    if context.user_data['usr_choice'] != 'talk':
        return
    await update.callback_query.answer()
    data = update.callback_query.data
    chat_gpt.set_prompt(load_prompt(data))
    await send_image(update, context, data)
    greet = await chat_gpt.add_message('Поздоровайся со мной')
    await send_text(update, context, greet)


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ stop function """
    await update.callback_query.answer()
    context.user_data.clear()
    context.user_data['usr_choice'] = 'main'
    await start(update, context)
    return ConversationHandler.END


app = ApplicationBuilder().token(TG_TOKEN).build()


app.add_handler(CommandHandler('start', start))
app.add_handler(CommandHandler('random', random_fact))
app.add_handler(CommandHandler('gpt', gpt_talk))
app.add_handler(CommandHandler('talk', talk))


app.add_handler(CallbackQueryHandler(random_buttons, pattern='random_more'))
app.add_handler(CallbackQueryHandler(talk_buttons, pattern='^talk_.*'))


CHOOSE_THEME, ASK_QUESTION, HANDLE_ANSWER, MENU_OPTIONS = range(4)


async def start_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ инициация квиза """
    context.user_data['usr_choice'] = 'quiz'
    context.user_data['prompt'] = load_prompt(context.user_data['usr_choice'])
    context.user_data['score'] = 0
    context.user_data['questions'] = 0
    context.user_data['chosen_theme'] = ''
    await send_image(update, context, context.user_data['usr_choice'])
    await ask_theme(update, context)

    return CHOOSE_THEME


async def ask_theme(update, context):
    """ Выводит начальное меню квиза с кнопками выбора тем """
    await send_text_buttons(update, context,
                            load_message(context.user_data['usr_choice']),
                            context.user_data['usr_choice'])

    return CHOOSE_THEME


async def choose_theme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает выбор темы """
    await update.callback_query.answer()
    context.user_data['chosen_theme'] = update.callback_query.data
    await ask_question(update, context)

    return HANDLE_ANSWER


async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Генерирует и задает вопрос"""
    question = await chat_gpt.send_question(context.user_data['prompt'],
                                            context.user_data['chosen_theme'])
    context.user_data['questions'] += 1
    await send_text(update, context, question)

    return HANDLE_ANSWER


async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Принимает и оценивает ответ, предлагает выбор дальше"""
    user_answer = update.message.text
    evaluation_message = await chat_gpt.add_message(user_answer)
    if "Правильно!" in evaluation_message:
        context.user_data['score'] += 1
    await send_text(update, context, evaluation_message)
    await send_text_buttons(update, context,
                            f'Правильных ответов: '
                            f'{context.user_data['score']} из '
                            f'{context.user_data['questions']}\n'
                            'Что вы хотите делать дальше?',
                            'quiz_answer_options')

    return MENU_OPTIONS


async def menu_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает выбор пользователя после ответа на вопрос квиза"""
    await update.callback_query.answer()
    selected_option = update.callback_query.data
    if selected_option == 'quiz_more':
        return await ask_question(update, context)
    elif selected_option == 'quiz_change':
        return await ask_theme(update, context)
    await send_text(update, context, 'Спасибо за участие в квизе!')
    context.user_data.clear()
    await stop(update, context)

    return ConversationHandler.END


app.add_handler(advice_conv_handler)


app.add_handler(ConversationHandler(
    entry_points=[CommandHandler('quiz', start_quiz)],
    states={
        CHOOSE_THEME: [CallbackQueryHandler(choose_theme, pattern='^quiz_.*')],
        ASK_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND,
                                      ask_question)],
        HANDLE_ANSWER: [MessageHandler(filters.TEXT & ~filters.COMMAND,
                                       handle_answer),
                        CallbackQueryHandler(menu_options, pattern='^quiz_.*')],
        MENU_OPTIONS: [CallbackQueryHandler(menu_options, pattern='^quiz_.*')]
    },
    fallbacks=[CommandHandler('stop', stop)]))


app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,
                               message_handler))


app.add_handler(CallbackQueryHandler(stop))


app.add_handler(CallbackQueryHandler(default_callback_handler))


app.run_polling()
