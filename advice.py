from telegram import Update
from telegram.ext import (CallbackQueryHandler,
                          ContextTypes, CommandHandler, MessageHandler, filters,
                          ConversationHandler)

from bot import stop
from util import default_callback_handler, send_image, send_text, \
    send_text_buttons, load_message, load_prompt


async def advice_entry(update: Update, context:ContextTypes.DEFAULT_TYPE):
    """Entry point for entertainment advice functionality.
    Demonstrates related image and text, initializes  local vars
    """
    context.user_data['usr_choice'] = 'advice'
    context.user_data['usr_mode'] = 'advice_entry'
    context.user_data['category'] = ''
    context.user_data['genre'] = ''
    context.user_data['prompt'] = ''
    text = load_message(context.user_data['usr_choice'])
    await send_image(update, context, context.user_data['usr_choice'])
    await send_text(update, context, text)
    await cat_request(update, context)
    return ADVICE_CAT


async def cat_request(update: Update,
                      context: ContextTypes.DEFAULT_TYPE) -> object:
    """ Requests the user to choose an entertainment category
    and provides the keys
    """
    context.user_data['usr_mode'] = 'advice_cat'
    text = load_message(context.user_data['usr_mode'])
    await send_text_buttons(update, context, text,
                            context.user_data['usr_mode'])
    return ADVICE_CAT


async def cat_handler(update: Update, context:ContextTypes.DEFAULT_TYPE):
    """ Handles category choice """

    await update.callback_query.answer()

    # Читаем кнопки и команды меню из соответствующего файла
    key_value_pairs = {}
    with open(f'resources/Menus/{context.user_data['usr_mode']}', "r",
              encoding="utf-8") as file:
        for line in file:

            # Убираем лишние пробелы и перевод строки
            line = line.strip()

            # Разбиваем строку на key и value по разделителю ":"
            if ":" in line:
                key, value = map(str.strip, line.split(":",1))
                key_value_pairs[key] = value
    key = update.callback_query.data

    # присваиваем свойству пользователя значение надписи нажатой кнопки
    if key in key_value_pairs:
        context.user_data['category'] = key_value_pairs[key]
    await genre_request(update, context)
    return ADVICE_GENRE


async def genre_request(update: Update, context:ContextTypes.DEFAULT_TYPE ):
    """ Requests user to provide a desired genre to look in """

    context.user_data['usr_mode'] = 'advice_genre'
    text = load_message(context.user_data['usr_mode'])
    await send_text(update, context, text)
    return ADVICE_GENRE


async def genre_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receives user genre description and collects prompt for gpt"""

    user_answer = update.message.text
    context.user_data['genre'] = user_answer
    await advice_ask_gpt(update, context)
    advice_prompt = load_prompt(context.user_data['usr_choice'])
    advice_prompt = '. '.join([advice_prompt, context.user_data['category'],
                               context.user_data['genre']])
    context.user_data['prompt'] = advice_prompt
    await advice_ask_gpt(update, context)
    return ADVICE_PREFS

async def advice_ask_gpt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Update prompt and Send request to GPT"""
    pass



async def recommend(update: Update, context:ContextTypes.DEFAULT_TYPE):
    """Provides advices alongside with keys like/dislike
    """
    pass


async def handle_prefs(update: Update, context:ContextTypes.DEFAULT_TYPE):
    """handles user preferences and develop updated list
    """
    pass


ADVICE_CAT, ADVICE_GENRE, ADVICE_PREFS = range(3)
advice_conv_handler = ConversationHandler(
    entry_points=[CommandHandler('advice', advice_entry)],
    states={
        ADVICE_CAT: [CallbackQueryHandler(cat_handler, pattern='^advice_.*')],
        ADVICE_GENRE: [MessageHandler(filters.TEXT & ~filters.COMMAND,
                                      genre_handler)],
        ADVICE_PREFS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_prefs)]
    },
    fallbacks=[CommandHandler('stop', stop)]
)

