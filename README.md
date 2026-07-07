# UMT-pythonweb-hw-03

Найпростіший веб-додаток на Python socket + Jinja2 для домашнього завдання 3.

## Що реалізовано

- маршрути `/`, `/index.html`, `/message.html`;
- обробка статичних ресурсів `/style.css` та `/logo.png`;
- форма на `/message.html` відправляє `username` та `message` методом POST на `/message`;
- повідомлення зберігаються у `storage/data.json` у форматі `{timestamp: {username, message}}`;
- маршрут `/read` відображає всі повідомлення через Jinja2-шаблон `read.html`;
- помилка 404 повертає сторінку `error.html`;
- додано `Dockerfile` для запуску в контейнері.

## Запуск локально

```bash
pip install -r requirements.txt
python main.py
```

Після запуску відкрийте:

```text
http://localhost:3000
```

## Запуск через Docker

```bash
docker build -t umt-pythonweb-hw-03 .
docker run -p 3000:3000 -v $(pwd)/storage:/app/storage umt-pythonweb-hw-03
```

Для Windows PowerShell:

```powershell
docker run -p 3000:3000 -v ${PWD}/storage:/app/storage umt-pythonweb-hw-03
```
