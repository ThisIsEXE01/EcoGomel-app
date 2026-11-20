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

pip install -r backend/requirements.txt

cd backend
python manage.py migrate --noinput
python manage.py import_waste
python manage.py import_dropoff_points
python manage.py collectstatic --noinput

echo "Готово. Не забудьте нажать Reload в Web-вкладке PythonAnywhere."
