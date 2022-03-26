import argparse
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler

from jinja2 import Environment, FileSystemLoader, select_autoescape
from livereload import Server, shell


def render_page(lib_path):
    with open(lib_path, 'r', encoding='utf-8') as f:
        books = json.load(f)
    return books


def rebuild():
    template = env.get_template('template.html')
    rendered_page = template.render(
        books=render_page('downloaded_books.json')
    )
    with open('index.html', 'w', encoding="utf8") as file:
        file.write(rendered_page)
    print('Page is rerendered')


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

    server = Server()
    server.watch('template.html', rebuild)
    server.watch('css/*.css', rebuild)
    server.serve(root='.')


