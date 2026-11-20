# Деплой на PythonAnywhere

Инструкция для текущей MVP-версии: без админки, без эндпоинтов обратной связи и волонтёров. Сайт и API работают на одном домене: Django отдаёт `/api/` и `/admin/`, а `frontend/` раздаётся через WhiteNoise с корня сайта.

## 1. Что понадобится

- Аккаунт PythonAnywhere (free-тарифа достаточно для MVP).
- Репозиторий: `https://github.com/ThisIsEXE01/EcoGomel-app.git`.
- Ветка с деплоем: `develop` или `deploy/pythonanywhere-mvp` после merge.
- Python 3.12 или 3.13. Django 6.1 не поддерживает версии ниже 3.12.

## 2. Первый деплой

### 2.1. Клонирование и виртуальное окружение

Откройте Bash-консоль PythonAnywhere:

```bash
cd ~
git clone https://github.com/ThisIsEXE01/EcoGomel-app.git
cd EcoGomel-app
git checkout develop

mkvirtualenv --python=/usr/bin/python3.13 ecogomel
workon ecogomel
```

Если путь к Python другой, посмотрите доступные версии:

```bash
ls /usr/bin/python3*
```

### 2.2. Зависимости

```bash
cd ~/EcoGomel-app/backend
pip install -r requirements.txt
```

### 2.3. Настройки окружения

```bash
cd ~/EcoGomel-app/backend
cp .env.example .env
nano .env
```

Для production заполните:

```env
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=<сгенерированный ключ>
DJANGO_ALLOWED_HOSTS=USERNAME.pythonanywhere.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://USERNAME.pythonanywhere.com
DJANGO_CORS_ALLOWED_ORIGINS=
DJANGO_SECURE_SSL_REDIRECT=True
```

`USERNAME` замените на ваше имя пользователя PythonAnywhere.

Сгенерировать `SECRET_KEY`:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Файл `backend/.env` не коммитится в git.

### 2.4. База данных и статика

```bash
cd ~/EcoGomel-app/backend
python manage.py migrate
python manage.py import_waste
python manage.py import_dropoff_points
python manage.py collectstatic --noinput
```

Проверка:

```bash
python manage.py check --deploy
```

Должно быть `0 issues`.

### 2.5. Web-приложение

В Web-вкладке PythonAnywhere:

1. **Add a new web app**.
2. Выберите **Manual configuration**, затем Python 3.13 (или 3.12).
3. **Source code**: `/home/USERNAME/EcoGomel-app`.
4. **Working directory**: `/home/USERNAME/EcoGomel-app/backend`.
5. **Virtualenv**: `/home/USERNAME/.virtualenvs/ecogomel`.
6. Откройте **WSGI configuration file** и замените содержимое на шаблон из `deploy/pythonanywhere_wsgi.py.example`. Не забудьте заменить `USERNAME`.
7. **Static files**: ничего добавлять не обязательно — WhiteNoise отдаёт и `frontend/`, и `/static/`.
   При желании можно добавить mapping:
   - URL: `/static/`
   - Directory: `/home/USERNAME/EcoGomel-app/backend/staticfiles`

   Не добавляйте mapping на `/`: он перекроет Django и API.

8. Включите **Force HTTPS**.
9. Нажмите **Reload**.

## 3. Проверка после деплоя

Откройте:

- `https://USERNAME.pythonanywhere.com/` — главная;
- `https://USERNAME.pythonanywhere.com/map.html` — карта;
- `https://USERNAME.pythonanywhere.com/waste.html` — каталог;
- `https://USERNAME.pythonanywhere.com/about_project.html` — о проекте;
- `https://USERNAME.pythonanywhere.com/api/points/` — JSON пунктов;
- `https://USERNAME.pythonanywhere.com/api/waste/` — JSON отходов.

На карте кнопки «Добавить» и «Удалить все» скрыты — это админские действия, они появятся в релизной версии. Формы на странице «О проекте» показывают сообщение, что функция в разработке.

## 4. Обновление сайта

После merge изменений в `develop`:

```bash
cd ~/EcoGomel-app
git pull
bash deploy/update.sh
```

Затем нажмите **Reload** в Web-вкладке.

Скрипт `deploy/update.sh`:

- активирует virtualenv `ecogomel` (или `VENV_NAME`);
- устанавливает зависимости;
- выполняет `migrate`;
- повторно импортирует данные;
- собирает статику.

Импорты идемпотентны, но `import_dropoff_points` обновляет пункты по ID из JSON. Если в будущем появится админка и ручные правки, перед импортом делайте резервную копию базы.

## 5. Резервная копия SQLite

На PythonAnywhere файл `backend/db.sqlite3` сохраняется между перезапусками, но резервную копию лучше делать перед обновлениями:

```bash
cd ~/EcoGomel-app/backend
cp db.sqlite3 "db.sqlite3.backup-$(date +%F)"
```

## 6. Типовые проблемы

| Симптом | Причина | Решение |
|---|---|---|
| `400 DisallowedHost` | Домен не указан в `DJANGO_ALLOWED_HOSTS` | Проверить `backend/.env`, добавить `USERNAME.pythonanywhere.com`, перезапустить |
| `403 CSRF` при входе в админку | Не указан `DJANGO_CSRF_TRUSTED_ORIGINS` | Добавить `https://USERNAME.pythonanywhere.com` |
| Сайт открывается, но API отдаёт 404 | Неверный WSGI/working directory | Проверить `PROJECT_PATH` в WSGI и рабочую директорию |
| Нет CSS/JS | Не выполнен `collectstatic` | `python manage.py collectstatic --noinput` |
| `ImproperlyConfigured: DJANGO_SECRET_KEY is required` | Нет `backend/.env` или пустой ключ | Создать `.env` по примеру |
| Бесконечный редирект на HTTPS | `SECURE_SSL_REDIRECT` конфликтует с прокси | Поставить `DJANGO_SECURE_SSL_REDIRECT=False` и использовать Force HTTPS |
| Пустые карточки/карта | Не выполнены импорты | `python manage.py import_waste` и `python manage.py import_dropoff_points` |
| `pymorphy3` не устанавливается | Неподходящая версия Python | Использовать Python 3.12/3.13, пересоздать virtualenv |
| Ошибка `no such table` | Не выполнен `migrate` | `python manage.py migrate` |

## 7. Ограничения free-тарифа PythonAnywhere

- Один web app на бесплатном аккаунте.
- Ограничение CPU-секунд в сутки.
- Бесплатный домен вида `USERNAME.pythonanywhere.com`; свой домен — на платном тарифе.
- Аккаунт нужно периодически подтверждать, иначе приложение могут отключить.
- SQLite подходит для MVP, но при росте нагрузки стоит перейти на PostgreSQL.

## 8. Что не входит в MVP

- админка и создание superuser;
- эндпоинты обратной связи и волонтёров;
- добавление/удаление пунктов через API;
- авторизация, rate limiting, пагинация;
- email-уведомления.

Эти функции появятся в релизной версии.
