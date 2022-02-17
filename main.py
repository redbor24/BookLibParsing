import os
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urljoin, urlparse, unquote

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename

BASE_URL = 'http://tululu.org/'
BOOKS_SUBPATH = 'books'
IMAGES_SUBPATH = 'images'


def check_for_redirect(response):
    if response.history:
        raise URLError('Текст недоступен для скачивания')


def get_book_params(book_id):
    url = f'{BASE_URL}b{book_id}'
    response = requests.get(url)
    response.raise_for_status()

    book_soup = BeautifulSoup(response.text, 'lxml')
    content = book_soup.find('body').find('div', id='content')
    if not content:
        return None

    _ = content.find('h1').text.split('::')
    book_name = _[0].strip()
    book_author = _[1].strip()
    _ = content.find('table', class_='d_book').find('div', class_='bookimage')
    img_url = _.find('img')['src']

    book_comments = get_book_comments(book_soup)

    return book_name, book_author, img_url, book_comments


def get_book_comments(book_soup):
    comments_soup = book_soup.find('body').find('div', id='content').\
                    find_all('div', class_='texts')
    comments = [
        comment.find('span', class_='black').text for comment in comments_soup
    ]

    return '\n'.join(comments)


def download_txt(url, filename, folder='books/'):
    filename = Path(folder) / sanitize_filename(filename)
    response = requests.get(url)
    response.raise_for_status()
    with open(filename, 'w') as file:
        file.write(response.text)
    return filename


def download_img(url, filename):
    response = requests.get(url)
    response.raise_for_status()
    with open(filename, 'wb') as file:
        file.write(response.content)


def download_book(book_path, image_path, book_id):
    file_type = 'txt'

    params = {'id': book_id}
    url = f'{BASE_URL}{file_type}.php'
    book_resp = requests.get(url, params=params)
    book_resp.raise_for_status()
    check_for_redirect(book_resp)

    download_url = book_resp.url
    book_name, book_author, img_url, book_comments = get_book_params(book_id)
    # print(f'book_params is {book_name, book_author, img_url, book_comments}')
    img_url = urljoin(BASE_URL, img_url)
    img_filename = unquote(
        str(Path(image_path) / os.path.basename(urlparse(img_url).path))
    )
    book_file_name = f'{book_id}. {book_name}.{file_type}'
    download_txt(download_url, book_file_name, book_path)
    download_img(img_url, img_filename)


if __name__ == '__main__':
    os.makedirs(BOOKS_SUBPATH, exist_ok=True)
    os.makedirs(IMAGES_SUBPATH, exist_ok=True)
    book_id = 1
    book_count = 10
    for i in range(book_id, book_id + book_count):
        try:
            download_book(BOOKS_SUBPATH, IMAGES_SUBPATH, i)
        except URLError as e:
            print(f'{i}: {e}')
