import requests
import os
from PIL import Image
from AdvancedHTMLParser import AdvancedHTMLParser
import html


class Elibrary:

    def __init__(self):
        self.session = requests.session()
        self.authorized = False
        self.parser = AdvancedHTMLParser()

    def authorize(self, username, password):
        req = {'username': username, 'password': password, 'redirect': '', 'language': 'ru_UN', 'action': 'login',
               'cookieverify': ''}
        result_url = self.session.post('http://elibrary.misis.ru/login.php', data=req).url
        if result_url == 'http://elibrary.misis.ru/browse.php':
            self.authorized = True
        else:
            self.authorized = False
        return self.authorized

    def search_book(self, query):
        books = list()
        req = {
            'txtQuery': f'(GeneralText contains "{query}")',
            'cbQuickQuery': '1',
            'cbQuickGeneral': '1',
        }
        result = self.session.post('http://elibrary.misis.ru/search2.php?action=process', data=req).text
        self.parser.parseStr(result)
        tbody = self.parser.getElementsByTagName('tbody')
        for tr in tbody[0].children:
            title = tr.children[1].children[1].children[0].innerText.strip()
            book_id = tr.children[1].children[1].children[0].href.split('=')[-1]
            author = tr.children[3].innerText.strip()
            year = tr.children[4].innerText.strip()
            book = Book(html.unescape(title), book_id, author, year)
            books.append(book)
        return books

    def get_page(self, book_id, page):
        while True:
            try:
                page_file = self.session.get(
                    f'http://elibrary.misis.ru/plugins/SecView/getDoc.php?id={book_id}&page={page}&type=large/slow').content
                break
            except:
                continue
        with open(f'{book_id}/{page}.jpg', 'wb') as out_file:
            out_file.write(page_file)
        return Image.open(f'{book_id}/{page}.jpg')

    def get_pages_qty(self, book_id):
        _pages = self.session.get(
            f'http://elibrary.misis.ru/action.php?kt_path_info=ktcore.SecViewPlugin.actions.document&fDocumentId={book_id}').text
        pages = 0
        for line in _pages.split('\n'):
            if '\'PageCount\'' in line:
                pages = int(line.split('\'')[3])
                break
        return pages

    def download_book_by_id(self, book_id):
        if not self.authorized:
            raise Exception('Unauthorized')
        try:
            os.makedirs(f'{book_id}')
        except:
            pass
        pages = self.get_pages_qty(book_id)
        images = list()
        for i in range(0, pages):
            images.append(self.get_page(book_id, i))
        images[0].save(f'{book_id}.pdf', "PDF", resolution=100.0, save_all=True, append_images=images[1:])
        return f'{book_id}.pdf'


class Book:
    def __init__(self, title, book_id, author, year):
        self.title = title
        self.book_id = book_id
        self.author = author
        self.year = year


client = Elibrary()
client.authorize('160415', 'Егор')
client.search_book('информационные технологии')
# client.download_book_by_id(7116)


