## Описание
Программа скачивает из библиотеки tululu.ru книги по указанному диапазону их id.

Скачанные текстовые файлы книг и их обложки сохраняются в подпапки программы 
`/books` и `/images`.

Текстовые файлы формируются в кодировке `utf-8`.

Не все книги из библиотеки могут быть скачаны. Для таких книг в консоль выдаётся
сообщение.

## Requirements
    beautifulsoup4==4.10.0
    pathvalidate==2.5.0
    requests==2.27.1
    lxml==4.7.1

## Установка
    pip install -r requirements.txt

## Использование
    python main.py start_id end_id

### Примеры
    python main.py 1 10


    python main.py -h
    usage: main.py [-h] start_id end_id
    
    Программа скачивает из библиотеки tululu.ru книги по указанному диапазону их id
    
    positional arguments:
      start_id    Начальный id книги для скачивания
      end_id      Конечный id книги для скачивания
    
    optional arguments:
      -h, --help  show this help message and exit


    python main.py
    usage: main.py [-h] start_id end_id
    main.py: error: the following arguments are required: start_id, end_id
