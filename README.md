## Описание
Программа скачивает из библиотеки tululu.ru книги жанра "Научная фантастика" с 
заданного диапазона страниц.
Лог работы сохраняется в файл `LibParser.log`.
Скачанные текстовые файлы книг и их обложки сохраняются в подпапки программы 
`/books` и `/images`.
Текстовые файлы формируются в кодировке `utf-8`.

## Requirements
    beautifulsoup4==4.10.0
    pathvalidate==2.5.0
    requests==2.27.1
    lxml==4.7.1

## Установка
    pip install -r requirements.txt

## Примеры использования
    > python main.py
    usage: main.py [-h] -start_page START_PAGE [-end_page END_PAGE] [-book_count BOOK_COUNT]
    main.py: error: the following arguments are required: -start_page

    > python main.py -h
    Программа скачивает из библиотеки tululu.ru книги жанра "Научная фантастика" с заданного диапазона страниц.
    
    optional arguments:
      -h, --help            show this help message and exit
      -start_page START_PAGE
                            Начальная страница категории
      -end_page END_PAGE    Конечная страница категории
      -book_count BOOK_COUNT
                            Количество книг для скачивания

    > python main.py -start_page 1 -end_page 10
    > python main.py -start_page 1 
    > python main.py -start_page 1 book_count 4
