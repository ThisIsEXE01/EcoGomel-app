# 🌿 EcoGomel — Интерактивный эко-помощник

Веб-сервис по раздельному сбору отходов и поиску пунктов приёма вторсырья для жителей города Гомеля. Проект разрабатывается в рамках дисциплины «Введение в разработку ПО» по методологии Scrum.

---

## 🎯 Ключевые возможности сервиса
- 🔍 **Умный поиск отходов:** мгновенный поиск по бытовым названиям предметов («бутылка», «батарейка», «шина») и справочник маркировок (01–07 пластик, стекло, макулатура).
- 📋 **Инструкции по сортировке:** пошаговые правила подготовки сырья к сдаче и классы опасности (I–V).
- 🗺️ **Интерактивная карта Гомеля:** карта пунктов приёма на базе **Leaflet / OpenStreetMap** с фильтрацией по видам сырья.
- 🌓 **Адаптивность:** светлая и тёмная темы оформления, приоритет на смартфоны (**Mobile-First**).

---

## 🛠 Технологический стек
- **Backend:** Python 3.12+, Django 6.1, SQLite
- **Frontend:** HTML5, CSS3, JavaScript, библиотека Leaflet.js
- **Дизайн & Айдентика:** Figma, векторные SVG-иконки
- **Управление проектом:** Jira Cloud, GitHub (Git Flow)

---

## 👥 Команда проекта
- **Тимлид / Аналитик:** Управление требованиями, процессы, защита проекта.
- **Frontend-разработчики (4):** Вёрстка страниц, интерактивная карта, темы оформления.
- **Backend-разработчики (4):** Архитектура базы данных, REST API, админ-панель.
- **UI/UX Дизайнер:** Mobile-First макеты и вайрфреймы в Figma.
- **Маркетинг и контент (2):** Опрос жителей Гомеля, промо-визитки движения, эко-мероприятия.
- **QA-инженер:** Кроссбраузерное тестирование сайта, оформление баг-репортов.

---

## 🚀 Как запустить проект

> ⚠️ **Важно:** для запуска сервера теперь нужен файл `backend/.env`. Без него `runserver` падает с ошибкой `ImproperlyConfigured: DJANGO_SECRET_KEY is required when DJANGO_DEBUG=False`.
>
> ```bash
> # Windows
> copy backend\.env.example backend\.env
>
> # Linux/macOS
> cp backend/.env.example backend/.env
> ```
>
> Для локальной разработки в примере уже включён `DJANGO_DEBUG=True`, править ничего не нужно.

### 1. Сервер (Backend):
```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

```bash
python manage.py migrate
python manage.py import_waste
python manage.py import_dropoff_points
python manage.py runserver
```

Бэкенд будет доступен по адресу `http://localhost:8000`, API — по префиксу `/api/`.

### Если сервер не запускается

- `ImproperlyConfigured: DJANGO_SECRET_KEY is required when DJANGO_DEBUG=False` — нет `backend/.env`. Скопируйте `.env.example` в `.env` (см. блок выше).
- `ModuleNotFoundError: No module named 'dotenv'` или `'whitenoise'` — не установлены зависимости. Активируйте venv и выполните `pip install -r requirements.txt`.
- `DisallowedHost` — проверьте `DJANGO_ALLOWED_HOSTS` в `backend/.env`.

### 2. Клиент (Frontend):
Бэкенд должен быть запущен. Можно открыть `frontend/index.html` в браузере или тот же сайт через Django: `http://localhost:8000/` — WhiteNoise раздаёт папку `frontend/` с корня.

Адрес API задаётся в одном месте — `frontend/api.js` (`API_BASE_URL`).

### Основные эндпоинты API:
- `GET /api/waste/` — список отходов (поиск и фильтры через query-параметры);
- `GET /api/waste/<id>/` — один отход;
- `GET /api/points/` — пункты приёма (фильтр `?waste_id=<id>`).

Подробнее об интеграции с API — [docs/api-integration.md](docs/api-integration.md) (English: [api-integration.en.md](docs/api-integration.en.md)).
