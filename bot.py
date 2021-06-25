from classes.elibrary import Elibrary
import util.DB as DB
import util.config as config
from telegram import *
from telegram.ext import *


def start(update, context):
    user = update.message.from_user.id
    if DB.user_exists(user):
        update.message.reply_text('Пожалуйста, отправьте поисковый запрос или ссылку на книгу')
    else:
        reply_keyboard = [['Авторизация']]
        update.message.reply_text(
            'Пожалуйста, авторизуйтесь',
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, True, one_time_keyboard=True)
        )
    return ConversationHandler.END


def authorization_start(update, context):
    update.message.reply_text(
        'Введите номер читательского билета\n\nНажмите /cancel для отмены',
        reply_markup=ReplyKeyboardRemove()
    )
    return USERNAME


def authorization_username(update, context):
    context.user_data['username'] = update.message.text
    update.message.reply_text('Введите пароль\n\nНажмите /cancel для отмены')
    return PASSWORD


def authorization_password(update, context):
    user = update.message.from_user.id
    username = context.user_data['username']
    password = update.message.text
    if Elibrary().authorize(username, password):
        DB.create_user(user, username, password)
        update.message.reply_text('Авторизация успешна')
    else:
        update.message.reply_text('Авторизация неуспешна')
    return start(update, context)


def download_by_url(update, context):
    user = update.message.from_user.id
    url = update.message.text
    book_id = url.split('=')[-1]
    DB.add_to_queue(user, book_id)
    update.message.reply_text('Книга добавлена в очередь загрузки')


def search_by_title(update, context):
    user = update.message.from_user.id
    if not DB.user_exists(user):
        update.message.reply_text('Сначала авторизуйтесь')
        return start(update, context)
    user_info = DB.get_user(user)
    lib_client = Elibrary()
    result = lib_client.authorize(user_info['username'], user_info['password'])
    if not result:
        update.message.reply_text('Авторизуйтесь заново')
        DB.remove_user(user)
        return start(update, context)
    search_results = lib_client.search_book(update.message.text)
    if len(search_results) == 0:
        update.message.reply_text('Нет результатов')
        return
    msg = 'Результаты поиска:\n\n'
    for i in range(len(search_results)):
        book = search_results[i]
        msg += f'/{i} {book.title}, {book.author} ({book.year})\n'
    msg += '\nНажмите на индекс книги для загрузки'
    context.user_data['books'] = search_results
    update.message.reply_text(msg)


def download_by_index(update, context):
    user = update.message.from_user.id
    index = int(update.message.text.split('/')[1])
    book = context.user_data['books'][index]
    DB.add_to_queue(user, book.book_id)
    update.message.reply_text('Книга добавлена в очередь загрузки')


if __name__ == '__main__':
    updater = Updater(config.TG_TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    USERNAME, PASSWORD = range(2)
    dispatcher.add_handler(ConversationHandler(
        entry_points=[MessageHandler(Filters.regex('^Авторизация$'), authorization_start)],
        states={
            USERNAME: [MessageHandler(Filters.text & ~ Filters.command, authorization_username)],
            PASSWORD: [MessageHandler(Filters.text & ~ Filters.command, authorization_password)]
        },
        fallbacks=[CommandHandler('cancel', start)],
    ))
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(MessageHandler(Filters.regex(r'^http\:\/\/elibrary\.misis\.ru\/action.php\?kt_path_info=ktcore\.SecViewPlugin\.actions\.document&fDocumentId=\d{1,7}$'), download_by_url))
    dispatcher.add_handler(MessageHandler(Filters.regex(r'^\/\d{1,2}$'), download_by_index))
    dispatcher.add_handler(MessageHandler(Filters.text, search_by_title))
    updater.start_polling()

