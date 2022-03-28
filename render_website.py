import argparse
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib import parse

from jinja2 import Environment, FileSystemLoader, select_autoescape
from livereload import Server, shell
from more_itertools import chunked, grouper

EMPTY_BOOK = {
    'url': '',
    'img_src': '',
    'book_path': '',
    'title': '',
    'author': '',
    'comments': '',
    'genres': ''
}


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
        grouper(list(map(lambda book: quote_book(book), books)), 2, EMPTY_BOOK)
                )


def render_page(lib_path, template_path, page_path):
    def render():
        template = env.get_template(template_path)
        rendered_page = template.render(
            books=load_books(lib_path)
        )
        with open(page_path, 'w', encoding="utf8") as file:
            file.write(rendered_page)

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
    page_path = 'index.html'

    server = Server()
    server.watch(template_path, render_page(lib_path, template_path, page_path))
    server.watch('css/*.css', render_page(lib_path, template_path, page_path))
    server.serve(root='.', port=80)
