# Frontend API integration

This document is for frontend, backend and QA: how the site gets data from the Django API, why CORS failed before, and how to add new pages.

Russian version: [api-integration.md](api-integration.md)

## 1. Quick start

Start the backend:

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

- The API is available at `http://localhost:8000/api/`.
- The frontend is opened as a file: `frontend/index.html`. No local server is required.
- The database is `backend/db.sqlite3`. It is listed in `.gitignore`, so after cloning the repository it must be created with `migrate` and the import commands.
- If the database already exists, re-running the imports is optional. They update records instead of creating duplicates.

## 2. Why CORS failed

When an HTML file is opened directly, the browser sends `Origin: null`. Django settings contained invalid origins with placeholders and ports `5173`/`3000`, so such requests were rejected. The frontend also requested `/api/v1/points/`, while the real path is `/api/points/`.

For local development `backend/config/settings.py` now contains:

```python
CORS_ALLOW_ALL_ORIGINS = DEBUG
```

While `DEBUG=True`, the API accepts requests from any origin, including `file://`. With `DEBUG=False` this rule is disabled: production must define `CORS_ALLOWED_ORIGINS` and `ALLOWED_HOSTS` explicitly.

Check:

```bash
curl -i -H "Origin: null" http://localhost:8000/api/waste/
```

The response must include `access-control-allow-origin: *`.

## 3. API client

All requests go through `frontend/api.js`. The API address is defined in one place — the `API_BASE_URL` constant.

```js
const waste = await EcoAPI.getWaste({ category: 'Пластик' });
const item = await EcoAPI.getWasteItem(1);
const points = await EcoAPI.getPoints({ waste_id: 1 });
```

- `getWaste(params)` — waste list with filters;
- `getWasteItem(id)` — a single waste item;
- `getPoints(params)` — drop-off points.

`apiRequest` builds query parameters and throws on a non-2xx status. Wrap page requests in `try/catch` and render a clear error state.

Do not hardcode API URLs in HTML pages: if the address changes, only `api.js` must be updated.

## 4. Endpoints

| Method | Path | Parameters | Purpose |
|---|---|---|---|
| GET | `/api/waste/` | `search`, `code`, `category`, `recyclable` | Waste list |
| GET | `/api/waste/<id>/` | — | Single waste item |
| GET | `/api/points/` | `waste_id` | Drop-off points |

The API returns arrays without pagination. It is read-only: `POST`, `PUT` and `DELETE` are not implemented.

Waste item fields:

- `id`, `name`, `code`, `category`;
- `recyclable` — boolean;
- `hazard_class` — string, may be empty;
- `preparation_steps` — array of strings;
- `what_happens_next` — string;
- `keywords` — array of strings;
- `map_filter_category` — category for future map filters, may be `null`.

Drop-off point fields:

- `id`, `name`, `address`, `working_hours`, `description`;
- `latitude`, `longitude` — numbers;
- `accepted_types` — array of categories.

Search is a case-insensitive substring match without morphology: `?search=бутылки` finds PET bottles, while `?search=бутылка` does not. Keep this in mind for the search feature.

## 5. Common errors

| Symptom | Cause | Fix |
|---|---|---|
| CORS error in console | Wrong origins or the server runs with `DEBUG=False` | Check `CORS_ALLOW_ALL_ORIGINS`, run with `DEBUG=True` |
| `Failed to fetch` / `ERR_CONNECTION_REFUSED` | Backend is not running | `python manage.py runserver` |
| 404 on `/api/v1/points/` | Obsolete path | Use `/api/points/` |
| Empty cards | No data in the database | Run `migrate` and the imports |
| 404 on a waste page | Invalid `id` in the link | Check the link and the existing record |
| `DisallowedHost` | Request from another IP, empty `ALLOWED_HOSTS` | Configure `ALLOWED_HOSTS` for the address |
| Icon is invisible | Theme is not handled or the path is wrong | Check `data-theme` and the SVG file name |

## 6. New page checklist

- data is loaded through `api.js` only;
- loading, error and empty states are implemented;
- database text is escaped before being inserted into HTML;
- `file://`, light/dark themes and mobile width are checked;
- `map.html` is not changed without the map owner;
- the task is done in a separate branch from `develop`, the PR is small.

## 7. Not connected yet

- the map uses `localStorage`, not the API;
- search on the main page is not implemented;
- the demo block and sidebar on the main page contain test data;
- there is no API for adding or deleting drop-off points;
- production CORS and `ALLOWED_HOSTS` are not configured;
- `84 C/PAP` and `ALU 41` have no dedicated icons, so their buttons are text-only;
- there are no automated API tests.

## 8. Links

- `backend/waste/models.py` — models;
- `backend/waste/views.py` — endpoints;
- `backend/waste/urls.py` — routes;
- `frontend/api.js` — API client;
- `frontend/waste.html` — waste page example;
- `README.md` — project setup.
