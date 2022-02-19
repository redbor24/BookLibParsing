import argparse
import logging
import os
from pathlib import Path
from urllib.error import URLError
from urllib.parse import unquote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename

BASE_URL = 'http://tululu.org/'
BOOKS_SUBFOLDER = 'books'
IMAGES_SUBFOLDER = 'images'

logger = logging.getLogger()


def check_for_redirect(response):
    if response.history:
        raise URLError('Текст недоступен для скачивания')


def parse_book_page(book_html):
    book_soup = BeautifulSoup(book_html, 'lxml')
    book_content = book_soup.find('body').find('div', id='content')
    if not book_content:
        return None

    _ = book_content.find('h1').text.split('::')
    book_name = _[0].strip()
    book_author = _[1].strip()
    _ = book_content.find('table', class_='d_book').\
        find('div', class_='bookimage')
    img_url = _.find('img')['src']

    book_comments = get_book_comments(book_content)
    book_genres = get_book_genres(book_content)
    return {
        'name': book_name,
        'author': book_author,
        'img_url': img_url,
        'comments': book_comments,
        'genres': book_genres
    }


def get_book_genres(soup):
    _ = soup.find('span', class_='d_book').find_all('a')
    return [genre.text for genre in _]


def get_book_comments(soup):
    comments_soup = soup.find_all('div', class_='texts')
    return [
        comment.find('span', class_='black').text for comment in comments_soup
    ]


def download_txt(book_response, filename, folder='books/'):
    filename = Path(folder) / sanitize_filename(filename)

    with open(filename, 'w', encoding='utf-8') as file:
        file.write(book_response.text)
    return filename


def download_img(url, filename):
    response = requests.get(url)
    response.raise_for_status()
    with open(filename, 'wb') as file:
        file.write(response.content)


def download_book(book_path, image_path, book_id):
    file_type = 'txt'

    book_page_url = f'{BASE_URL}b{book_id}'
    book_page_resp = requests.get(book_page_url)
    book_page_resp.raise_for_status()
    parsed_book = parse_book_page(book_page_resp.content)
    logger.info(book_page_url)

    params = {'id': book_id}
    url = f'{BASE_URL}{file_type}.php'
    book_resp = requests.get(url, params=params)
    book_resp.raise_for_status()
    check_for_redirect(book_resp)

    book_file_name = f'{book_id}. {parsed_book["name"]}.{file_type}'
    download_txt(book_resp, book_file_name, book_path)

    img_url = urljoin(BASE_URL, parsed_book['img_url'])
    img_filename = unquote(
        str(Path(image_path) / os.path.basename(urlparse(img_url).path))
    )
    download_img(img_url, img_filename)
    logger.info('  Книга скачана')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Программа скачивает из библиотеки tululu.ru книги'
                    ' по указанному диапазону их id.'
    )
    parser.add_argument('start_id',
                        help='Начальный id книги для скачивания',
                        type=int)
    parser.add_argument('end_id',
                        help='Конечный id книги для скачивания',
                        type=int)
    args = parser.parse_args()

    logger.setLevel(logging.INFO)
    log_handler = logging.FileHandler('LibParser.log', encoding='utf-8')
    log_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(message)s')
    )
    logger.addHandler(log_handler)

    os.makedirs(BOOKS_SUBFOLDER, exist_ok=True)
    os.makedirs(IMAGES_SUBFOLDER, exist_ok=True)
    for book in range(args.start_id, args.end_id + 1):
        try:
            download_book(BOOKS_SUBFOLDER, IMAGES_SUBFOLDER, book)
        except URLError as e:
            logger.info(f'{book}: {e}')
