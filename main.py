import argparse
import json
import logging
import os
import time
from collections import OrderedDict
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import unquote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename

BASE_URL = 'http://tululu.org/'
CATEGORY_URL = f'{BASE_URL}l55/'
# секунды
HTTP_TIMEOUT = 3
WAIT_TIME = 3

BOOKS_SUBPATH = 'books'
IMAGES_SUBPATH = 'images'

JSON_PATH = ''

logger = logging.getLogger()

headers = OrderedDict({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0)'
                  ' Gecko/20100101 Firefox/77.0',
    'Accept-Encoding': 'gzip, deflate, br'
})


def check_for_redirect(url, response):
    if response.history:
        parsed_url = ''.join(urlparse(url)._replace(scheme=''))
        parsed_resp_url = ''.join(urlparse(response.url)._replace(scheme=''))
        if parsed_url not in parsed_resp_url:
            raise HTTPError(
                response.url,
                response.history[0].status_code,
                'Текст недоступен для скачивания.',
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

    comments_soup = book_page_content.select('div.texts span.black')
    book_comments = [comment.text for comment in comments_soup]

    genres_soup = book_page_content.select('span.d_book a')
    book_genres = [genre.text for genre in genres_soup]

    return {
        'name': book_name,
        'author': book_author,
        'img_url': img_url,
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
    response = get_http(url, headers=headers)
    response.raise_for_status()
    with open(filename, 'wb') as file:
        file.write(response.content)


def download_book(book_url, book_sub_path, image_path, skip_book, skip_image):
    file_type = 'txt'
    logger.info(f'{book_url}: скачиваем книгу...')
    book_id = int(urlparse(book_url).path.replace('/', '').replace('b', ''))

    book_page_resp = get_http(book_url)
    book_page_resp.raise_for_status()
    check_for_redirect(book_url, book_page_resp)

    parsed_book = parse_book_page(book_page_resp.content)
    parsed_book['book_page_url'] = book_url

    params = {'id': book_id}
    url = f'{BASE_URL}{file_type}.php'
    book_resp = get_http(url, params=params)
    book_resp.raise_for_status()
    check_for_redirect(url, book_resp)

    saved_filename = ''
    if not skip_book:
        book_file_name = f'{book_id}. {parsed_book["name"]}.{file_type}'
        saved_filename = download_txt(book_resp, book_file_name, book_sub_path)

    img_filename = ''
    if not skip_image:
        img_url = urljoin(BASE_URL, parsed_book['img_url'])
        img_filename = unquote(
            str(Path(image_path) / os.path.basename(urlparse(img_url).path))
        )
        download_img(img_url, img_filename)

    logger.info(f'{book_url}: Книга скачана')

    return {
        'url': parsed_book['book_page_url'],
        'img_src': img_filename,
        'book_path': str(saved_filename),
        'title': parsed_book['name'],
        'author': parsed_book['author'],
        'comments': parsed_book['comments'],
        'genres': parsed_book['genres'],
    }


def get_page_count(category_page_soup):
    """
    Возвращает количество страниц пагинации
    :param category_page_soup: HTML страницы
    :return: int
    """
    category_content = category_page_soup.\
        select_one('body div#content p.center')
    paginator_soup = category_content.select('span,a')

    paginator_last_index = len(paginator_soup) - 1
    if paginator_soup:
        return int(paginator_soup[paginator_last_index].text)
    else:
        return 0


def get_books_links_from_page(category_page_soup):
    """
    Парсит category_page_soup для получения списка ссылок на книги
    :param category_page_soup: HTML страницы со списком книг
    :return: Список ссылок на книги
    """
    books_soup = category_page_soup.select('body div#content table.d_book')
    return [urljoin(BASE_URL, elem.select_one('a')['href'])
            for elem in books_soup
           ]


def get_links_for_category(category_url, start_page=1, end_page=0,
                           book_count=0):
    # Укажем значение номера страницы, которое вряд ли может быть в реальности
    incredeble_page_num = 10000
    if not end_page:
        end_page = incredeble_page_num

    if start_page > end_page > 0:
        raise(Exception('Номер начальной страницы должен быть меньше номера'
                        ' последней'))

    book_urls = []
    for page_number in range(start_page, end_page + 1):
        url = f'{category_url}{page_number}/'

        page_resp = get_http(url)
        page_resp.raise_for_status()
        page_resp_soup = BeautifulSoup(page_resp.content, 'html.parser')
        if end_page == incredeble_page_num:
            end_page = get_page_count(page_resp_soup)
        page_book_links = get_books_links_from_page(page_resp_soup)
        book_urls.extend(page_book_links)

        if book_count != 0 and len(book_urls) > book_count:
            book_urls = book_urls[:book_count]
            break

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


def download_category(category_url, start_page, end_page, book_count,
                      book_path, image_path,
                      skip_books, skip_images):
    book_links = get_links_for_category(category_url, start_page, end_page,
                                        book_count)

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

    filename = Path(JSON_PATH) / 'downloaded_books.json'
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
    parser.add_argument('-book_count', default=0, type=int,
                        help='Количество книг для скачивания')

    parser.add_argument('-dest_folder', type=str, default='.',
                        help='Папка для сохранения всех скачанных файлов')
    parser.add_argument('-skip_imgs', action='store_true',
                        help='Не сохранять картинки')
    parser.add_argument('-skip_books', action='store_true',
                        help='Не сохранять книги')
    parser.add_argument('-json_path', type=str, default='',
                        help='Путь к json-файлу с результатами скачивания')

    args = parser.parse_args()

    books_folder = Path(args.dest_folder) / BOOKS_SUBPATH
    images_folder = Path(args.dest_folder) / IMAGES_SUBPATH

    if not args.skip_books:
        os.makedirs(books_folder, exist_ok=True)
    if not args.skip_imgs:
        os.makedirs(images_folder, exist_ok=True)

    if args.json_path:
        JSON_PATH = args.json_path
        os.makedirs(JSON_PATH, exist_ok=True)

    logger.setLevel(logging.INFO)
    log_handler = logging.FileHandler('LibParser.log', encoding='utf-8')
    log_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(message)s')
    )
    logger.addHandler(log_handler)
    logger.info('------------------- Запуск программы -------------------')
    logger.info(f'Параметры запуска:')
    for param_name, param_value in args._get_kwargs():
        logger.info(f'  {param_name}: {param_value}')
    logger.info('--------------------------------------------------------')

    try:
        download_category(category_url=CATEGORY_URL,
                          start_page=args.start_page,
                          end_page=args.end_page,
                          book_count=args.book_count,
                          book_path=books_folder,
                          image_path=images_folder,
                          skip_books=args.skip_books,
                          skip_images=args.skip_imgs
                          )
    except Exception as e:
        logger.error(f'--! Ошибка: {e}')
    finally:
        logger.info('------------------- Работа завершена -------------------')
