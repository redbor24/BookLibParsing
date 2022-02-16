import os
from pathlib import Path
from urllib.error import URLError

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename

BASE_URL = 'http://tululu.org/'


def check_for_redirect(response):
    if response.history:
        raise URLError('Текст недоступен для скачивания')


def get_book_params(book_id):
    url = f'{BASE_URL}b{book_id}'
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'lxml')
    content = soup.find('body').find('div', id='content')
    if not content:
        return None

    _ = content.find('h1').text.split('::')
    book_name = _[0].strip()
    book_author = _[1].strip()
    _ = content.find('table', class_='d_book').find('div', class_='bookimage')
    img_url = _.find('img')['src']
    return book_name, book_author, img_url


def download_txt(url, filename, folder='books/'):
    filename = Path(folder) / sanitize_filename(filename)
    response = requests.get(url)
    response.raise_for_status()
    with open(filename, 'w') as file:
        file.write(response.text)
    return filename


def download_book(path_to_save, book_id):
    file_type = 'txt'

    params = {'id': book_id}
    url = f'{BASE_URL}{file_type}.php'
    response = requests.get(url, params=params)
    response.raise_for_status()

    check_for_redirect(response)
    download_url = response.url
    book_name, book_author, img_url = get_book_params(book_id)
    file_name = f'{book_id}. {book_name}.{file_type}'
    download_txt(download_url, file_name, path_to_save)


if __name__ == '__main__':
    books_subfolder = 'books'
    os.makedirs(books_subfolder, exist_ok=True)
    book_id = 1
    book_count = 10
    for i in range(book_id, book_id + book_count):
        try:
            download_book(books_subfolder, i)
        except URLError as e:
            print(f'{i}: {e}')
