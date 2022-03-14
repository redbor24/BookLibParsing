import json
import time

from collections import OrderedDict
from pprint import pprint

import argparse
import logging
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename

BASE_URL = 'http://tululu.org/'
CATEGORY_URL = f'{BASE_URL}l55/'
HTTP_TIMEOUT = 3  # секунды
WAIT_TIME = 3  # секунды

BOOKS_SUBFOLDER = 'books'
IMAGES_SUBFOLDER = 'images'

logger = logging.getLogger()

headers = OrderedDict({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0',
    'Accept-Encoding': 'gzip, deflate, br'
})


def check_for_redirect(url, response):
    if response.history:
        if not url in response.url:
            raise HTTPError(
                response.url,
                response.history[0].status_code,
                'Текст недоступен для скачивания.',
                '', ''
            )


def parse_book_page(page_content):
    book_page_soup = BeautifulSoup(page_content, 'lxml')
    book_page_content = book_page_soup.find('body').find('div', id='content')
    if not book_page_content:
        return None

    name_and_author = book_page_content.find('h1').text.split('::')
    book_name, book_author = [word.strip() for word in name_and_author]

    img_sub_url = book_page_content.find('table', class_='d_book'). \
        find('div', class_='bookimage'). \
        find('img')['src']
    img_url = urljoin(BASE_URL, img_sub_url)

    comments_soup = book_page_content.find_all('div', class_='texts')
    book_comments = [
        comment.find('span', class_='black').text for comment in comments_soup
    ]

    genres_soup = book_page_content.find('span', class_='d_book').find_all('a')
    book_genres = [genre.text for genre in genres_soup]

    return {
        'name': book_name,
        'author': book_author,
        'img_url': img_url,
        'comments': book_comments,
        'genres': book_genres
    }


def download_txt(book_response, filename, folder='books/'):
    filename_for_save = unquote(
        str(Path(folder) / sanitize_filename(filename))
    )

    with open(filename_for_save, 'w', encoding='utf-8') as file:
        file.write(book_response.text)
    return filename_for_save


def download_img(url, filename):
    # response = requests.get(url, headers=headers)
    response = http_get(url, headers=headers)
    response.raise_for_status()
    with open(filename, 'wb') as file:
        file.write(response.content)


# def download_book(book):
#     pass


def download_book(book_url, book_sub_path, image_path):
    file_type = 'txt'
    logger.info(f'Скачиваем книгу {book_url}...')
    book_id = int(urlparse(book_url).path.replace('/', '').replace('b', ''))

    # book_page_resp = requests.get(book_url, headers=headers)
    book_page_resp = http_get(book_url, headers=headers)
    book_page_resp.raise_for_status()
    check_for_redirect(book_url, book_page_resp)

    parsed_book = parse_book_page(book_page_resp.content)
    parsed_book['book_page_url'] = book_url
    logger.info(f'{book_url}: {parsed_book}')

    params = {'id': book_id}
    url = f'{BASE_URL}{file_type}.php'
    # book_resp = requests.get(url, params=params, headers=headers)
    book_resp = http_get(url, params=params, headers=headers)
    book_resp.raise_for_status()
    check_for_redirect(url, book_resp)

    book_file_name = f'{book_id}. {parsed_book["name"]}.{file_type}'
    saved_filename = download_txt(book_resp, book_file_name, book_sub_path)

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
        find('body').\
        find('div', id='content')
    paginator_soup = category_content.\
        find('p', class_='center').\
        find_all(['span', 'a'])
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
    books_soup = category_page_soup.find('body').find('div', id='content')
    books_links = []
    for book_soup in books_soup.find_all('table'):
        book_sub_url = book_soup.find_all('tr')[1].find('a')['href']
        books_links.append(urljoin(BASE_URL, book_sub_url))
    return books_links


def get_links_for_category(category_url, start_page=1, end_page=0, book_count=0):
    if end_page == 0:
        end_page = get_page_count(category_url)
    if start_page > end_page:
        raise(Exception('Номер начальной страницы должен быть меньше номера'
                        ' последней'))

    book_urls = []
    for page in range(start_page, end_page + 1):
        if page == 1:
            url = f'{category_url}'
        else:
            url = f'{category_url}{page}/'

        # page_resp = requests.get(url, headers=headers)
        page_resp = http_get(url, headers=headers)
        page_resp.raise_for_status()
        page_resp_soup = BeautifulSoup(page_resp.content, 'lxml')
        page_book_links = get_books_links_from_page(page_resp_soup)
        book_urls.extend(page_book_links)

        if book_count != 0 and len(book_urls) > book_count:
            book_urls = book_urls[:book_count]
            break

    return book_urls


def http_get(url, headers=None, params=None, wait=True):
    resp_ok = False
    try_counter, max_try_count = 0, 10
    while not resp_ok and try_counter <= max_try_count:
        if wait:
            time.sleep(WAIT_TIME)
        resp = requests.get(url=url, headers=headers, params=params)
        resp_ok = resp.ok
        if not resp_ok:
            logger.warning(f'url: {url}, status_code: {resp.status_code}'
                           f', try count: {try_counter}/{max_try_count}')
            # print(f'url: {url}, status_code: {resp.status_code}, try count:'
            #       f' {try_counter}/{max_try_count}')
            try_counter += 1
    resp.raise_for_status()
    return resp


def get_category_links(logger, category_url, start_page=1, end_page=0,
                       book_count=0):
    book_links = get_links_for_category(category_url, start_page, end_page,
                                        book_count)

    if book_count > 0:
        return book_links[:book_count]
    else:
        return book_links


def download_category(category_url, start_page=1, end_page=0, book_count=0):
    book_links = get_category_links(logger, category_url, start_page, end_page,
                               book_count)

    dowloaded_books = []
    for book_link in book_links:
        try:
            dowloaded_books.append(
                download_book(book_link, BOOKS_SUBFOLDER, IMAGES_SUBFOLDER)
            )
        except HTTPError as e:
            logger.error(f'{book_link}: {e}')
        except Exception as e2:
            logger.error(f'{book_link}: общая ошибка. {e2}')

    filename = 'downloaded_books.json'
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(dowloaded_books, f, ensure_ascii=False)

    pprint(f'dowloaded_books: {dowloaded_books}')


if __name__ == '__main__':
    # parser = argparse.ArgumentParser(
    #     description='Программа скачивает из библиотеки tululu.ru книги'
    #                 ' по указанному диапазону их id.'
    # )
    # parser.add_argument('start_id',
    #                     help='Начальный id книги для скачивания',
    #                     type=int)
    # parser.add_argument('end_id',
    #                     help='Конечный id книги для скачивания',
    #                     type=int)
    # args = parser.parse_args()
    # start_id = args.start_id
    # end_id = args.end_id
    start_id = 239
    end_id = 250

    logger.setLevel(logging.INFO)
    log_handler = logging.FileHandler('LibParser.log', encoding='utf-8')
    log_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(message)s')
    )
    logger.addHandler(log_handler)
    logger.info(f'-------------------- Запуск программы --------------------')
    try:

        os.makedirs(BOOKS_SUBFOLDER, exist_ok=True)
        os.makedirs(IMAGES_SUBFOLDER, exist_ok=True)

        download_category(CATEGORY_URL, start_page=1, end_page=1, book_count=4)
    finally:
        logger.info(f'-------------------- Запуск программы --------------------')
