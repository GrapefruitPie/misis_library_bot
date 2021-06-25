from classes.elibrary import Elibrary
import util.DB as DB
import util.config as config
import requests


def send_to_tg(user_id, file_id=None, file_path=None):
    req = {'chat_id': (None, user_id)}
    if file_id is not None:
        req['document'] = (None, file_id)
    elif file_path is not None:
        req['document'] = ('file.pdf', open(file_path, 'rb'))
    result = requests.post(f'https://api.telegram.org/bot{config.TG_TOKEN}/sendDocument', files=req).json()
    return result['result']['document']['file_id']


def download_book(entry):
    if (file_id := DB.get_book_from_cache(entry['book_id'])) is not None:
        send_to_tg(entry['user'], file_id=file_id)
        return
    client = Elibrary()
    user_info = DB.get_user(entry['user'])
    result = client.authorize(user_info['username'], user_info['password'])
    if not result:
        return
    file_path = client.download_book_by_id(entry['book_id'])
    file_id = send_to_tg(entry['user'], file_path=file_path)
    DB.save_to_cache(entry['book_id'], file_id)
    DB.remove_from_queue(entry['_id'])


if __name__ == '__main__':
    for queue_entry in DB.get_queue():
        download_book(queue_entry)

