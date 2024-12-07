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
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - '
                           '%(message)s',
                    level=logging.DEBUG)
logging.getLogger('httpx').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


# Commands
# start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выводит главное меню"""
    context.user_data['usr_choice'] = 'main'
    text = load_message(context.user_data['usr_choice'])
    await send_image(update, context, context.user_data['usr_choice'])
    await send_text(update, context, text)
    await show_main_menu(update, context, {
        'start': 'Главное меню',
        'random': 'Узнать случайный интересный факт 🧠',
        'gpt': 'Задать вопрос чату GPT 🤖',
        'talk': 'Поговорить с известной личностью 👤',
        'quiz': 'Поучаствовать в квизе ❓'
    })


# message handler
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик выбора пользователя и запуск обработчика"""
    match context.user_data.get('usr_choice'):
        case 'main':
            await start(update, context)
        case 'random':
            await start(update, context)
        case 'gpt':
            await gpt_dialog(update, context)
        case 'talk':
            await gpt_dialog(update, context)


# random fact
async def random_fact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Генерирует случайный факт и показывает его пользователю"""
    context.user_data['usr_choice'] = 'random'
    text = load_message(context.user_data['usr_choice'])
    await send_image(update, context, context.user_data['usr_choice'])
    await send_text(update, context, text)
    prompt = load_prompt(context.user_data['usr_choice'])
    answer = await (chat_gpt.send_question(prompt, ''))
    await send_text_buttons(update, context, answer,
                            context.user_data['usr_choice']
                            )


# CallbackHandler для меню random_fact
async def random_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатия кнопок в меню random_fact"""
    if context.user_data.get('usr_choice') != 'random':
        return
    await update.callback_query.answer()
    await random_fact(update, context)


# gpt talk
async def gpt_talk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Разговор с gpt начало"""
    context.user_data['usr_choice'] = 'gpt'
    text = load_message(context.user_data.get('usr_choice'))
    await send_image(update, context, context.user_data.get('usr_choice'))
    await send_text(update, context, text)
    prompt = load_prompt(context.user_data.get('usr_choice'))
    chat_gpt.set_prompt(prompt)


# talk to the famous person
async def talk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Разговор с известным человеком начало"""
    context.user_data['usr_choice'] = 'talk'
    text = load_message(context.user_data['usr_choice'])
    await send_image(update, context, context.user_data['usr_choice'])
    await send_text_buttons(update, context, text,
                            context.user_data['usr_choice']
                            )


# CallbackHandler для меню talk
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


# stop
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /stop"""
    context.user_data.clear()
    await update.callback_query.answer()
    await start(update, context)


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

# Conversation handler for quiz command
CHOOSE_THEME, ASK_QUESTION, HANDLE_ANSWER, MENU_OPTIONS = range(4)


# Quiz functions
async def start_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """инициация квиза"""
    context.user_data['usr_choice'] = 'quiz'
    context.user_data['prompt'] = load_prompt(context.user_data['usr_choice'])
    context.user_data['score'] = 0
    context.user_data['questions'] = 0
    await send_image(update, context, context.user_data['usr_choice'])
    await ask_theme(update, context)
    return CHOOSE_THEME


# Запрос темы
async def ask_theme(update, context):
    """Выводит начальное меню квиза с кнопками выбора тем"""
    await send_text_buttons(update, context,
                            load_message(context.user_data['usr_choice']),
                            context.user_data['usr_choice']
                            )
    return CHOOSE_THEME


# Выбор темы
async def choose_theme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает выбор темы """
    await update.callback_query.answer()
    context.user_data['chosen_theme'] = update.callback_query.data
    await ask_question(update, context)
    return HANDLE_ANSWER


# Задает вопрос на тему
async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Генерирует и задает вопрос"""
    question = await chat_gpt.send_question(context.user_data['prompt'],
                                            context.user_data['chosen_theme']
                                            )
    context.user_data['questions'] += 1
    await send_text(update, context, question)
    return HANDLE_ANSWER


# Принимает ответ пользователя, получает оценку от GPT, запрашивает, что дальше
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


# Обрабатывает выбор после ответа на вопрос и вызывает обработчики
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
    await start(update, context)
    return ConversationHandler.END


# quiz СonversationHandler состояния
app.add_handler(ConversationHandler(
    entry_points=[CommandHandler('quiz', start_quiz)],
    states={
        CHOOSE_THEME: [CallbackQueryHandler(choose_theme, pattern='^quiz_.*'),
                       CallbackQueryHandler(ask_theme, pattern='^quiz_.*')
                       ],
        ASK_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND,
                                      ask_question)],
        HANDLE_ANSWER: [MessageHandler(filters.TEXT & ~filters.COMMAND,
                                       handle_answer),
                        CallbackQueryHandler(menu_options, pattern='^quiz_.*')
                        ],
        MENU_OPTIONS: [CallbackQueryHandler(menu_options, pattern='^quiz_.*')]
    },
    fallbacks=[CommandHandler('stop', stop)]))

#Message Handler
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,
                               message_handler))

#Default CallBack handler
app.add_handler(CallbackQueryHandler(default_callback_handler))

app.run_polling()
