from pymongo import MongoClient

client = MongoClient()

users = client['elibrary']['users']
# {"user": <tg_id>, "username": <username>, "password": <password>}

books = client['elibrary']['books']
# {"book_id": <book_id>, "path": <path>}

queue = client['elibrary']['queue']
# {"user": <tg_id>, "book_id": <id>}


def user_exists(user):
    if users.find_one({'user': user}) is not None:
        return True
    return False


def get_user(user):
    return users.find_one({'user': user})


def create_user(user, username, password):
    users.insert_one({'user': user, 'username': username, 'password': password})


def remove_user(user):
    users.delete_one({'user': user})


def add_to_queue(user, book_id):
    queue.insert_one({'user': user, 'book_id': book_id})


def get_queue():
    return queue.find()


def remove_from_queue(_id):
    queue.delete_one({'_id': _id})


def save_to_cache(book_id, file_id):
    books.insert_one({'book_id': book_id, 'file_id': file_id})


def get_book_from_cache(book_id):
    if (book := books.find_one({'book_id': book_id})) is not None:
        return book['file_id']
    return None

