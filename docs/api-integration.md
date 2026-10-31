# Интеграция фронтенда с API

Документ для фронтенда, бэкенда и QA: как сайт получает данные из Django API, почему раньше возникала ошибка CORS и как добавлять новые страницы.

English version: [api-integration.en.md](api-integration.en.md)

## 1. Быстрый старт

Запуск бэкенда:

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py import_waste
python manage.py import_dropoff_points
python manage.py runserver
```

- API доступен по адресу `http://localhost:8000/api/`.
- Фронтенд открывается как файл `frontend/index.html`, локальный сервер не нужен.
- База — `backend/db.sqlite3`. Она в `.gitignore`, поэтому после клонирования репозитория её нужно создать командами `migrate` и импортами.
- Если база уже есть, повторные импорты не обязательны. Они обновляют записи, а не создают дубликаты.

## 2. Почему была ошибка CORS

При открытии HTML как файла браузер отправляет `Origin: null`. В настройках Django были указаны нерабочие origin'ы с плейсхолдерами и портами `5173`/`3000`, поэтому такой запрос отклонялся. Дополнительно фронтенд обращался к `/api/v1/points/`, а реальный путь — `/api/points/`.

Сейчас в `backend/config/settings.py` для разработки стоит:

```python
CORS_ALLOW_ALL_ORIGINS = DEBUG
```

Пока `DEBUG=True`, API разрешает запросы с любого origin, включая `file://`. При `DEBUG=False` это правило отключается: для хостинга нужно явно задать `CORS_ALLOWED_ORIGINS` и `ALLOWED_HOSTS`.

Проверка:

```bash
curl -i -H "Origin: null" http://localhost:8000/api/waste/
```

В ответе должен быть заголовок `access-control-allow-origin: *`.

## 3. API-клиент

Все запросы идут через `frontend/api.js`. Адрес API задаётся в одном месте — константе `API_BASE_URL`.

```js
const waste = await EcoAPI.getWaste({ category: 'Пластик' });
const item = await EcoAPI.getWasteItem(1);
const points = await EcoAPI.getPoints({ waste_id: 1 });
```

- `getWaste(params)` — список отходов с фильтрами;
- `getWasteItem(id)` — один отход;
- `getPoints(params)` — пункты приёма.

`apiRequest` сам собирает query-параметры и выбрасывает ошибку при статусе не 2xx. В странице запрос нужно оборачивать в `try/catch` и показывать понятное состояние ошибки.

Не хардкодьте адреса API в HTML-страницах: если адрес изменится, правится только `api.js`.

## 4. Эндпоинты

| Метод | Путь | Параметры | Назначение |
|---|---|---|---|
| GET | `/api/waste/` | `search`, `code`, `category`, `recyclable` | Список отходов |
| GET | `/api/waste/<id>/` | — | Один отход |
| GET | `/api/points/` | `waste_id` | Пункты приёма |

API возвращает массивы без пагинации. API только для чтения: `POST`, `PUT` и `DELETE` не реализованы.

Поля отхода:

- `id`, `name`, `code`, `category`;
- `recyclable` — boolean;
- `hazard_class` — строка, может быть пустой;
- `preparation_steps` — массив строк;
- `what_happens_next` — строка;
- `keywords` — массив строк;
- `map_filter_category` — категория для будущих фильтров карты, может быть `null`.

Поля пункта приёма:

- `id`, `name`, `address`, `working_hours`, `description`;
- `latitude`, `longitude` — числа;
- `accepted_types` — массив категорий.

Поиск работает по подстроке без морфологии: `?search=бутылки` найдёт ПЭТ-бутылки, а `?search=бутылка` — нет. Это важно учитывать в задаче поиска.

## 5. Типичные ошибки

| Симптом | Причина | Решение |
|---|---|---|
| CORS error в консоли | Неверные origin'ы или сервер запущен с `DEBUG=False` | Проверить `CORS_ALLOW_ALL_ORIGINS`, запускать с `DEBUG=True` |
| `Failed to fetch` / `ERR_CONNECTION_REFUSED` | Бэкенд не запущен | `python manage.py runserver` |
| 404 на `/api/v1/points/` | Устаревший путь | Использовать `/api/points/` |
| Карточки пустые | Нет данных в БД | Выполнить `migrate` и импорты |
| 404 на странице отхода | Неверный `id` в ссылке | Проверить ссылку и наличие записи |
| `DisallowedHost` | Запрос с другого IP, `ALLOWED_HOSTS` пуст | Настроить `ALLOWED_HOSTS` для нужного адреса |
| Иконка не видна | Не учтена тема или неверный путь | Проверить `data-theme` и имя SVG |

## 6. Чек-лист новой страницы

- данные берутся только через `api.js`;
- есть состояния загрузки, ошибки и «ничего не найдено»;
- текст из БД экранируется перед вставкой в HTML;
- проверены `file://`, светлая и тёмная темы, мобильная ширина;
- `map.html` не меняется без владельца карты;
- задача делается в отдельной ветке от `develop`, PR — небольшой.

## 7. Что пока не подключено

- карта работает на `localStorage`, а не на API;
- поиск на главной не реализован;
- демо-блок и сайдбар на главной содержат тестовые данные;
- нет API для добавления и удаления пунктов приёма;
- продакшн-настройки CORS и `ALLOWED_HOSTS` не заданы;
- для `84 C/PAP` и `ALU 41` нет отдельных иконок — кнопки текстовые;
- автоматических тестов API нет.

## 8. Ссылки

- `backend/waste/models.py` — модели;
- `backend/waste/views.py` — эндпоинты;
- `backend/waste/urls.py` — маршруты;
- `frontend/api.js` — клиент API;
- `frontend/waste.html` — пример страницы отхода;
- `README.md` — запуск проекта.
