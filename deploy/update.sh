#!/usr/bin/env bash
# Обновление проекта на PythonAnywhere.
# Запускать из Bash-консоли PythonAnywhere:
#   cd ~/EcoGomel-app
#   bash deploy/update.sh
#
# Если виртуальное окружение называется иначе, задайте VENV_NAME:
#   VENV_NAME=myenv bash deploy/update.sh

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_NAME="${VENV_NAME:-ecogomel}"

cd "$PROJECT_ROOT"

if command -v workon >/dev/null 2>&1; then
  # shellcheck disable=SC1090
  workon "$VENV_NAME"
elif [ -f "$HOME/.virtualenvs/$VENV_NAME/bin/activate" ]; then
  # shellcheck disable=SC1091
  source "$HOME/.virtualenvs/$VENV_NAME/bin/activate"
else
  echo "Виртуальное окружение '$VENV_NAME' не найдено." >&2
  echo "Создайте его или задайте VENV_NAME." >&2
  exit 1
fi

REQUIREMENTS_FILE="$PROJECT_ROOT/backend/requirements.txt"
REQUIREMENTS_HASH_FILE="${VIRTUAL_ENV:-$HOME/.virtualenvs/$VENV_NAME}/.ecogomel_requirements_hash"
REQUIREMENTS_HASH="$(sha256sum "$REQUIREMENTS_FILE" | awk '{print $1}')"

if [ ! -f "$REQUIREMENTS_HASH_FILE" ] || [ "$(cat "$REQUIREMENTS_HASH_FILE")" != "$REQUIREMENTS_HASH" ]; then
  echo "requirements.txt изменился — устанавливаю зависимости..."
  pip install -r "$REQUIREMENTS_FILE"
  printf '%s\n' "$REQUIREMENTS_HASH" > "$REQUIREMENTS_HASH_FILE"
else
  echo "requirements.txt не изменился — pip install пропущен."
fi

cd backend
python manage.py migrate --noinput
python manage.py import_waste
python manage.py import_dropoff_points
python manage.py collectstatic --noinput

echo "Готово. Не забудьте нажать Reload в Web-вкладке PythonAnywhere."
