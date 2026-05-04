# SysDiag Monitor

Инструмент мониторинга диагностики и версий с веб-интерфейсом.

## Быстрый старт

```bash
pip install -r requirements.txt
# или если не захочет что либо устанавливаться
python -m pip install -r requirements.txt 
python app.py
```

Откройте браузер: http://localhost:5000

## Настройка серверов

В файле `app.py` найдите секцию `SERVERS` и добавьте ваши серверы:

```python
SERVERS = [
    {"id": "server1", "name": "Server 1", "url": "https://server1.example.com"},
    {"id": "server2", "name": "Server 2", "url": "https://server2.example.com"},
    {"id": "server3", "name": "Server 3", "url": "https://server3.example.com"},
]
```

## Настройка учётных данных

```python
LOGIN    = "aa"
PASSWORD = "aabb"
TIMEOUT  = 300  # секунд (5 минут)
```

## Описание работы

### Авторизация (автоматически)
1. GET /signin — получение `__secretToken`
2. POST /signin — вход с логином и паролем

### Режимы проверки

| Кнопка        | Эндпоинт        | Описание |
|---------------|-----------------|----------|
| Диагностика   | GET /index      | Проверка всех сервисов на alert-success |
| Версии        | GET /version    | Проверка версий и сравнение с footer |
| Всё сразу     | Оба             | Параллельная проверка обоих эндпоинтов |

### Статусы

| Иконка | Класс          | Значение |
|--------|----------------|----------|
| ✔      | alert-success  | Сервис в порядке |
| ⚠      | alert-warning  | Предупреждение |
| ✖      | alert-danger   | Ошибка |

Для `/version` версия подсвечивается **красным**, если не совпадает с версией в `<div id="footer">`.

## SSL

Если сервер использует самоподписанный сертификат, в `app.py` уже включено `session.verify = False`.
