## Описание
Программа скачивает из библиотеки tululu.ru первые 4 книги жанра "Научная фантастика".
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

## Использование
    python main.py start_id end_id

### Примеры
    python main.py
