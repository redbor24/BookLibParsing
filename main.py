import requests
import pprint
import json

# Качаем картинку
# url = "https://dvmn.org/filer/canonical/1542890876/16/"
#
# response = requests.get(url)
# response.raise_for_status()
#
# filename = 'dvmn.svg'
# with open(filename, 'wb') as file:
#     file.write(response.content)

def download_book(book_id):
    url = f'http://tululu.org/txt.php?id={book_id}'

    response = requests.get(url)
    response.raise_for_status()
    filename = f'{book_id}.txt'
    with open(filename, 'w') as file:
        file.write(response.text)


if __name__ == '__main__':
    from_id = 32169
    for i in range(from_id, from_id + 10):
        # print(i)
        download_book(i)