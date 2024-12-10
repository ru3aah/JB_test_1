from telegram import Update

from config import chat_gpt
from util import (default_callback_handler, send_image, send_text,
                  send_text_buttons, load_message, load_prompt)
from telegram.ext import (CallbackQueryHandler, ContextTypes, CommandHandler,
                          MessageHandler, filters, ConversationHandler)


async def advice_entry(update: Update, context:ContextTypes.DEFAULT_TYPE):
    """Entry point for entertainment advice functionality.
    Demonstrates related image and text, initializes  local vars
    """
    initialize_user_data(context)
    text = load_message(context.user_data['usr_choice'])
    await send_image(update, context, context.user_data['usr_choice'])
    await send_text(update, context, text)
    await cat_request(update, context)

    return ADVICE_CAT


def initialize_user_data(context: ContextTypes.DEFAULT_TYPE):
    """Initializes user data for advice entry."""
    user_data = context.user_data
    user_data['usr_choice'] = 'advice'
    user_data['usr_mode'] = 'advice_entry'
    user_data['category'] = ''
    user_data['genre'] = ''
    user_data['prompt'] = ''
    user_data['recommended'] = ''


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

    advice_prompt = load_prompt(context.user_data['usr_choice'])
    request = '. '.join(['Категория произведения: ',
                               context.user_data['category'],
                               '. Жанр произведения: ',
                               context.user_data['genre']])
    context.user_data['recommended'] = request
    context.user_data['prompt'] = advice_prompt
    await advice_ask_gpt(update, context)
    return ADVICE_RECOMMEND

async def advice_ask_gpt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ Send request to GPT, get recommendation and ask user choice"""

    context.user_data['usr_mode'] = 'advice_ask_gpt'
    advice_prompt = str(context.user_data['prompt'])
    chat_gpt.set_prompt(advice_prompt)
    message = await send_text(update, context, 'Thinking...')
    request = context.user_data['recommended']
    recommended = await chat_gpt.add_message(request)
    context.user_data['recommended'] = recommended
    await message.delete()
    message = " ".join([f'Вот что я могу порекомендовать в категории '
                         f'{context.user_data["category"]} в жанре '
                         f'{context.user_data["genre"]}: ', recommended])
    await send_text_buttons(update, context, message,
                                context.user_data['usr_mode'])
    return ADVICE_RECOMMEND

async def ask_query_handler(update: Update, context:
ContextTypes.DEFAULT_TYPE):
    """ Handles user choice upon receiving recommendation """

    await update.callback_query.answer()
    key = update.callback_query.data
    if key == 'advice_more':
        recommended = "  ".join([context.user_data['recommended'],
                                 "- не нравится; "])
        context.user_data['recommended'] = recommended
        return await advice_ask_gpt(update, context)
    elif key == 'advice_like':
        recommended = "  ".join([context.user_data['recommended'],
                                 "- нравится; "])
        context.user_data['recommended'] = recommended
        return await advice_ask_gpt(update, context)
    elif key == 'advice_stop':
        await advice_stop(update, context)
        return ConversationHandler.END

    return ADVICE_RECOMMEND


async def advice_stop(update: Update, context:ContextTypes.DEFAULT_TYPE):
    """ finishes conversation """
    context.user_data.clear()
    context.user_data['usr_choice'] = 'main'
    return ConversationHandler.END


# ConversationHandler for advice
ADVICE_CAT, ADVICE_GENRE, ADVICE_RECOMMEND = range(3)

advice_conv_handler = ConversationHandler(
    entry_points=[CommandHandler('advice', advice_entry)],
    states={
        ADVICE_CAT: [CallbackQueryHandler(cat_handler, pattern='^advice_.*')],
        ADVICE_GENRE: [MessageHandler(filters.TEXT & ~filters.COMMAND,
                                      genre_handler)],
        ADVICE_RECOMMEND: [CallbackQueryHandler(ask_query_handler,
                                                pattern='^advice_.*')],
    },
    fallbacks=[CommandHandler('stop', advice_stop)],
    allow_reentry=True,
    name="advice_conv_handler"
)

