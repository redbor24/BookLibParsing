## Описание
Программа скачивает из библиотеки [tululu.ru](tululu.ru) книги жанра 
"Научная фантастика" с заданного диапазона страниц.

Лог работы сохраняется в файл `LibParser.log` в папке программы.

Скачанные текстовые файлы книг и их обложки сохраняются в папке программы в 
подпапках `/books` и `/images`.
Их местоположение может быть задана параметром `-dest_folder`
(см. описание Параметров вызова).
Файлы книг формируются в кодировке `utf-8`.

Список скачанных книг сохраняется в файле `downloaded_books.json`. 
Его местоположение может быть задано параметром `-json_path` 
(см. описание Параметров вызова). По умолчанию файл сохраняется в папке 
программы. 

## Requirements
    beautifulsoup4==4.10.0
    pathvalidate==2.5.0
    requests==2.27.1
    lxml==4.7.1

## Установка
    pip install -r requirements.txt

## Параметры вызова
    -h, --help            Показ справки
    -start_page           Начальная страница категории
    -end_page             Конечная страница категории
    -dest_folder          Папка для сохранения всех скачанных файлов
    -skip_imgs            Не сохранять картинки
    -skip_books           Не сохранять книги
    -json_path            Путь к json-файлу с результатами скачивания

## Примеры вызовов
    > python main.py
    usage: main.py [-h] -start_page START_PAGE [-end_page END_PAGE]
    main.py: error: the following arguments are required: -start_page

    > python main.py -start_page 1 -end_page 10

    > python main.py -start_page 1 

    > python main.py -start_page 1 book_count 4
