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


def quote_book(book):
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

    return list(
        chunked(
            grouper(list(map(lambda book: quote_book(book), books)), 2, None),
            INDEX_PAGE_CHUNK
        )
    )


def render_page(lib_path, template_path, page_path, is_debug=False):
    def render():
        template = env.get_template(template_path)
        books = load_books(lib_path)
        page_count = len(books)
        for index, page in enumerate(books, 1):
            rendered_page = template.render(
                books=page,
                page_count=page_count,
                page_num=index
            )
            with open(page_path.format(index), 'w', encoding="utf8") as file:
                file.write(rendered_page)

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

    env = Environment(
        loader=FileSystemLoader('.'),
        autoescape=select_autoescape(['html', 'xml'])
    )
    template_path = 'template.html'
    lib_path = 'downloaded_books.json'
    pages_path = 'pages'
    os.makedirs(pages_path, exist_ok=True)
    page_path = f'{pages_path}/index{{0}}.html'

    server = Server()
    server.watch(
        template_path,
        render_page(lib_path, template_path, page_path)
    )
    server.watch(
        'css/*.css',
        render_page(lib_path, template_path, page_path)
    )
    server.serve(root='.', port=80, default_filename='pages/index1.html')
