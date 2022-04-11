## Описание
Учебный проект devman.

Программа позволяет скачать из библиотеки [tululu.ru](tululu.ru) книги жанра 
"Научная фантастика" с заданного диапазона страниц и сгенерировать из них 
локальный каталог с разбивкой на страницы

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
### Скачивание книг
```
python main.py
usage: main.py [-h] -start_page START_PAGE [-end_page END_PAGE]
main.py: error: the following arguments are required: -start_page
```
Скачивание книг со страниц с 1 по 10
```
python main.py -start_page 1 -end_page 10
```
Скачивание книг со страниц с 2 до последней
```
python main.py -start_page 2 
```
### Формирование локального каталога
```
python render_website.py
```

## Сайт на GitHub Pages
[Скачанный каталог](https://redbor24.github.io/BookLibParsing/pages/index1.html)
 книг на GitHub Pages.