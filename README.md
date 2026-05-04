# INDEX/VERSION MONITOR

Простой монитор для отслеживания состояния сервисов и их версий на нескольких серверах.

## Требования

- Python 3.8+
- Установленные зависимости из `requirements.txt`

## Настройка

### 1. Переменные окружения (.env)
Создайте файл `.env` на основе `.env.example` и заполните учетные данные и параметры парсинга:

```env
LOGIN=your_login
PASSWORD=your_password
TIMEOUT=300
SIGNIN_TAIL=/path/to/signin
VERSION_TAIL=/path/to/version
INDEX_TAIL=/path/to/index
PAGE_AUTH_TOKEN=auth_token_field_name
PAGE_INPUT_LOGIN=login_field_name
PAGE_INPUT_PASSWORD=password_field_name
PAGE_PARSER_BODY=main_content_id
```

### 2. Конфигурация серверов (config.json)
Создайте файл `config.json` на основе `config.example.json`. Укажите список серверов для мониторинга:

```json
{
  "servers": [
    {
      "id": "prod-1",
      "name": "Production Server 1",
      "url": "https://server1.example.com"
    }
  ]
}
```

## Установка и запуск (с доступом к интернету)

### Использование venv (рекомендуется)

1. **Создайте виртуальное окружение:**
   ```bash
   python -m venv venv
   ```

2. **Активируйте его:**
   - Windows: `venv\Scripts\activate`
   - Linux/macOS: `source venv/bin/activate`

3. **Установите зависимости:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Запустите приложение:**
   ```bash
   python app.py
   ```
   Приложение будет доступно по адресу `http://localhost:5000`.

---

## Установка на машине без доступа к интернету

Если целевая машина не имеет доступа к сети, выполните следующие шаги:

### Шаг 1: Подготовка на машине С ИНТЕРНЕТОМ
1. Скачайте все зависимости в папку `packages`:
   ```bash
   pip download -d packages -r requirements.txt
   ```
2. Перенесите проект и папку `packages` на целевую машину (например, через USB).

### Шаг 2: Установка на машине БЕЗ ИНТЕРНЕТА
1. Перейдите в папку проекта.
2. Создайте виртуальное окружение:
   ```bash
   python -m venv venv
   ```
3. Активируйте его (см. выше).
4. Установите зависимости локально из папки `packages`:
   ```bash
   pip install --no-index --find-links=packages -r requirements.txt
   ```
5. Запустите приложение: `python app.py`

## Особенности
- **Проверка конфигурации**: При запуске приложение проверяет `config.json` на наличие дубликатов ID, имен или URL и выводит предупреждение в интерфейсе.
- **Сравнение версий**: В окне деталей версии сравниваются с целевой (из футера).
  - <span style="color: green">↑ Зеленая стрелка</span>: версия выше целевой.
  - <span style="color: red">↓ Красная стрелка</span>: версия ниже целевой.
