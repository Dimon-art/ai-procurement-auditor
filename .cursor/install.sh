#!/usr/bin/env bash
# Idempotent bootstrap for the AI Procurement Auditor Cloud Agent environment.
set -euo pipefail

cd "$(dirname "$0")/.."

# System dependency required to create Python virtual environments on the
# default Ubuntu image.
if ! dpkg -s python3-venv >/dev/null 2>&1; then
    sudo apt-get update -qq
    sudo apt-get install -y -qq python3-venv
fi

# Create the virtual environment once, then keep dependencies in sync.
if [ ! -x .venv/bin/python ]; then
    python3 -m venv .venv
fi

.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

# Local development configuration. The real SECRET_KEY and OCR credentials are
# never committed; these development defaults use the built-in mock OCR
# provider so the app runs without external services.
if [ ! -f .env ]; then
    cat > .env <<'EOF'
SECRET_KEY=dev-insecure-secret-key-for-local-cloud-agent-only
DEBUG=True
OCR_PROVIDER=mock
YANDEX_OCR_API_KEY=placeholder-dev-key
YANDEX_FOLDER_ID=placeholder-dev-folder
EOF
fi

# Apply database migrations (SQLite, created in the project directory).
.venv/bin/python manage.py migrate --noinput

echo "Install complete."
