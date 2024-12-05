from telegram import Update
from telegram.ext import (CallbackQueryHandler,
                          ContextTypes, CommandHandler, MessageHandler, filters,
                          ConversationHandler)

from bot import chat_gpt
from util import send_image, load_prompt, send_text_buttons, send_text

CHOOSE_THEME, DIFF, ANSWER = range(3)

async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['usr_choice'] = 'quiz'
    context.user_data['score'] = 0
    chat_gpt.set_prompt(load_prompt(context.user_data.get('usr_choice')))
    await send_image(update, context, context.user_data.get('usr_choice'))
    await send_text_buttons(update, context, 'Выбери тему', buttons={
        'quiz_prog': 'Программирование',
        'quiz_math': 'Математика',
        'quiz_biology': 'Биология'
    })
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
