import os
from pathlib import Path

import requests


def download_book(path_to_save, book_id):
    url = f'http://tululu.org/txt.php?id={book_id}'

    response = requests.get(url)
    response.raise_for_status()
    filename = Path(path_to_save) / f'{book_id}.txt'
    with open(filename, 'w') as file:
        file.write(response.text)


if __name__ == '__main__':
    books_subfolder = 'books'
    os.makedirs(books_subfolder, exist_ok=True)
    from_id = 1
    for i in range(from_id, from_id + 10):
        download_book(books_subfolder, i)
