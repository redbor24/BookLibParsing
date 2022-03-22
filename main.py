import argparse
import json
import logging
import os
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import unquote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename

BASE_URL = 'http://tululu.org/'
CATEGORY_URL = f'{BASE_URL}l55/'

WAIT_TIME = 3  # секунды

BOOKS_SUBPATH = 'books'
IMAGES_SUBPATH = 'images'

logger = logging.getLogger()


class NoBookException(Exception):
    pass


def check_for_redirect(response):
    if len(response.history) == 2:
        raise HTTPError(response.url, 404, 'Запрошенная страница не найдена',
                        '', ''
                        )


def parse_book_page(page_content):
    book_page_soup = BeautifulSoup(page_content, 'html.parser')
    book_page_content = book_page_soup.select_one('body div#content')
    if not book_page_content:
        return None

    name_and_author = book_page_content.select_one('h1').text.split('::')
    book_name, book_author = [word.strip() for word in name_and_author]

    img_sub_url = book_page_soup. \
        select_one('table.d_book div.bookimage img')['src']
    img_url = urljoin(BASE_URL, img_sub_url)

    try:
        download_book_link = book_page_soup. \
            select_one('[href^="/txt.php"]')['href']
        download_book_link = urljoin(BASE_URL, download_book_link)
    except TypeError:
        download_book_link = None

    comments_soup = book_page_content.select('div.texts span.black')
    book_comments = [comment.text for comment in comments_soup]

    genres_soup = book_page_content.select('span.d_book a')
    book_genres = [genre.text for genre in genres_soup]

    return {
        'name': book_name,
        'author': book_author,
        'img_url': img_url,
        'download_book_url': download_book_link,
        'comments': book_comments,
        'genres': book_genres
    }


def download_txt(book_response, filename, folder):
    filename_for_save = unquote(
        str(Path(folder) / sanitize_filename(filename))
    )

    with open(filename_for_save, 'w', encoding='utf-8') as file:
        file.write(book_response.text)
    return filename_for_save


def download_img(url, filename):
    response = get_http(url)
    response.raise_for_status()
    with open(filename, 'wb') as file:
        file.write(response.content)


def download_book(book_url, book_sub_path, image_path, skip_book=False,
                  skip_image=False):
    file_type = 'txt'
    logger.info(f'{book_url}: скачиваем книгу...')
    book_id = urlparse(book_url).path.replace('/', '').replace('b', '')

    book_page_resp = get_http(book_url)
    book_page_resp.raise_for_status()
    check_for_redirect(book_page_resp)

    parsed_book = parse_book_page(book_page_resp.content)
    parsed_book['book_page_url'] = book_url

    if not parsed_book['download_book_url']:
        raise NoBookException('Книга недоступна для скачивания')
    book_resp = get_http(parsed_book['download_book_url'])
    book_resp.raise_for_status()
    check_for_redirect(book_resp)

    saved_filename = ''
    if not skip_book:
        book_file_name = f'{book_id}. {parsed_book["name"]}.{file_type}'
        saved_filename = download_txt(book_resp, book_file_name, book_sub_path)

    img_filename = ''
    if not skip_image:
        img_url = parsed_book['img_url']
        img_filename = unquote(
            str(Path(image_path) / os.path.basename(urlparse(img_url).path))
        )
        download_img(img_url, img_filename)

    logger.info(f'{book_url}: Книга скачана')

    return {
        'url': parsed_book['book_page_url'],
        'img_src': img_filename,
        'book_path': saved_filename,
        'title': parsed_book['name'],
        'author': parsed_book['author'],
        'comments': parsed_book['comments'],
        'genres': parsed_book['genres'],
    }


def get_links_for_category(category_url, start_page=1, end_page=0):
    if start_page > end_page > 0:
        raise(Exception('Номер начальной страницы должен быть меньше номера'
                        ' последней'))

    book_urls = []
    page_number = start_page
    while True:
        url = f'{category_url}{page_number}/'

        page_resp = get_http(url)
        page_resp.raise_for_status()
        try:
            check_for_redirect(page_resp)
        except HTTPError:
            break
        page_resp_soup = BeautifulSoup(page_resp.content, 'html.parser')

        books_soup = page_resp_soup.select('body div#content table.d_book')
        page_book_links = [urljoin(BASE_URL, elem.select_one('a')['href'])
                           for elem in books_soup
                           ]

        book_urls.extend(page_book_links)
        if page_number == end_page:
            break
        page_number += 1

    return book_urls


def get_http(url, headers=None, params=None, wait=True):
    resp_ok = False
    try_counter, max_try_count = 1, 10
    while not resp_ok and try_counter <= max_try_count:
        if wait:
            time.sleep(WAIT_TIME)
        resp = requests.get(url=url, headers=headers, params=params)
        resp_ok = resp.ok
        if not resp_ok:
            try_counter += 1
            logger.warning(f'{url}: status_code: {resp.status_code}'
                           f', try count: {try_counter}/{max_try_count}')
    resp.raise_for_status()
    return resp


def download_category(category_url, start_page, end_page,
                      book_path, image_path, json_path,
                      skip_books, skip_images):
    book_links = get_links_for_category(category_url, start_page, end_page)

    dowloaded_books = []
    for book_link in book_links:
        try:
            dowloaded_books.append(
                download_book(book_link, book_path, image_path,
                              skip_books, skip_images)
            )
        except HTTPError as http_error:
            logger.error(f'{book_link}: {http_error}')
        except Exception as error:
            logger.error(f'{book_link}: общая ошибка. {error}')

    filename = Path(json_path) / 'downloaded_books.json'
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(dowloaded_books, f, ensure_ascii=False)

    return dowloaded_books


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Программа скачивает из библиотеки tululu.ru книги жанра '
                    '"Научная фантастика" с заданного диапазона страниц.'
    )
    parser.add_argument('-start_page', required=True, type=int,
                        help='Начальная страница категории')
    parser.add_argument('-end_page', type=int, default=0,
                        help='Конечная страница категории')
    parser.add_argument('-dest_folder', type=str, default='.',
                        help='Папка для сохранения всех скачанных файлов')
    parser.add_argument('-json_path', type=str, default='.',
                        help='Путь к json-файлу с результатами скачивания')
    parser.add_argument('-skip_imgs', action='store_true',
                        help='Не сохранять картинки')
    parser.add_argument('-skip_books', action='store_true',
                        help='Не сохранять книги')

    args = parser.parse_args()

    books_folder = Path(args.dest_folder) / BOOKS_SUBPATH
    images_folder = Path(args.dest_folder) / IMAGES_SUBPATH

    if not args.skip_books:
        os.makedirs(books_folder, exist_ok=True)
    if not args.skip_imgs:
        os.makedirs(images_folder, exist_ok=True)
    if args.json_path != '.':
        os.makedirs(args.json_path, exist_ok=True)

    logger.setLevel(logging.INFO)
    log_handler = logging.FileHandler('LibParser.log', encoding='utf-8')
    log_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(message)s')
    )
    logger.addHandler(log_handler)

    logger.info('------------------- Запуск программы -------------------')
    logger.info('Параметры запуска:')
    for param_name, param_value in args._get_kwargs():
        logger.info(f'  {param_name}: {param_value}')
    logger.info('--------------------------------------------------------')

    try:
        download_category(category_url=CATEGORY_URL,
                          start_page=args.start_page,
                          end_page=args.end_page,
                          book_path=books_folder,
                          image_path=images_folder,
                          json_path=args.json_path,
                          skip_books=args.skip_books,
                          skip_images=args.skip_imgs
                          )
    except Exception as e:
        logger.error(f'--! Ошибка: {e}')
    finally:
        logger.info('------------------- Работа завершена -------------------')
