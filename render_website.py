
import logging
import argparse
import json
import os
from pathlib import Path
from urllib import parse

from jinja2 import Environment, FileSystemLoader, select_autoescape
from livereload import Server
from more_itertools import grouper, chunked
from pprint import pprint


INDEX_PAGE_CHUNK = 5  # Количество книг на одной странице
logger = logging.getLogger()


def quote_book(book):
    ss = '\n'.join(map(str, book['genres']))
    print(f'ss: {ss}')
    return {
        'url': book['url'],
        'img_src': parse.quote(book['img_src'].replace('\\', '/')),
        'book_path': parse.quote(book['book_path'].replace('\\', '/')),
        'title': book['title'],
        'author': book['author'],
        'comments': book['comments'],
        'genres': book['genres']
    }


def load_books(path):
    with open(path, 'r', encoding='utf-8') as f:
        books = json.load(f)

    lst1 = list(map(lambda book: quote_book(book), books))
    lst2 = list(grouper(lst1, 2, None))
    return list(chunked(lst2, INDEX_PAGE_CHUNK))


def render_page(lib_path, template_path, pages_path, page_filename, is_debug=False):
    def render():
        logger.info('Рендерим странички...')
        template = env.get_template(template_path)
        books = load_books(lib_path)
        logger.info(f'books: {len(books)}')
        page_count = len(books)
        for index, page in enumerate(books, 1):
            logger.info(f'  рендерим страничку: {index}')
            rendered_page = template.render(
                books=page,
                pages_path=pages_path,
                page_count=page_count,
                page_num=index
            )
            with open(Path(pages_path) / page_path.format(index), 'w', encoding="utf8") as file:
                file.write(rendered_page)
        logger.info('Странички отрендерены')

    if is_debug:
        render()

    print('Page is rerendered')

    return render


if __name__ == '__main__':
    # parser = argparse.ArgumentParser(
    #     description='Программа генерирует html-страничку со списком ранее'
    #                 ' скачанных книг'
    # )
    # parser.add_argument('-lib_path', required=True, type=str,
    #                     help='Имя json-файла со списком скачанных книг')
    #
    # args = parser.parse_args()

    logger.setLevel(logging.INFO)
    log_handler = logging.FileHandler('LibParser.log', encoding='utf-8')
    log_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(message)s')
    )
    logger.addHandler(log_handler)

    env = Environment(
        loader=FileSystemLoader('.'),
        autoescape=select_autoescape(['html', 'xml'])
    )
    template_path = 'template.html'
    lib_path = 'downloaded_books.json'
    pages_path = 'pages'
    os.makedirs(pages_path, exist_ok=True)
    page_path = 'index{0}.html'

    logger.info('------------------- Запуск программы -------------------')
    logger.info('Параметры запуска:')
    logger.info(f'  template_path: {template_path}')
    logger.info(f'  lib_path: {lib_path}')
    logger.info(f'  pages_path: {pages_path}')
    logger.info(f'  page_path: {page_path}')
    logger.info('--------------------------------------------------------')

    render_page(lib_path, template_path, pages_path, page_path, True)

    server = Server()
    server.watch(
        template_path,
        render_page(lib_path, template_path, pages_path, page_path)
    )
    server.watch(
        'css/*.css',
        render_page(lib_path, template_path, pages_path, page_path)
    )
    server.serve(root='.', port=80, default_filename='pages/index1.html')
