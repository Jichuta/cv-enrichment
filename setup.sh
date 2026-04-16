#!/usr/bin/env bash
# ── CV Enrichment API — Local Setup ─────────────────────────────────────────
# Run once to set up the virtual environment and install dependencies.
#
# Usage:
#   chmod +x setup.sh
#   ./setup.sh

set -e

PYTHON=${PYTHON:-python3}
VENV_DIR=".venv"

echo "── Creating virtual environment in ${VENV_DIR}/ ──"
$PYTHON -m venv $VENV_DIR

echo "── Activating virtual environment ──"
# shellcheck disable=SC1091
source $VENV_DIR/Scripts/activate 2>/dev/null || source $VENV_DIR/bin/activate

echo "── Upgrading pip ──"
pip install --upgrade pip --quiet

echo "── Installing dependencies ──"
pip install -r requirements.txt

echo "── Copying .env.example → .env (if not exists) ──"
if [ ! -f .env ]; then
    cp .env.example .env
    echo "   Created .env — fill in your DATABRICKS_TOKEN and API_SECRET_KEY"
else
    echo "   .env already exists, skipping"
fi

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env and set your DATABRICKS_TOKEN"
echo "  2. Activate the venv:"
echo "       Windows (Git Bash): source .venv/Scripts/activate"
echo "       Mac/Linux:          source .venv/bin/activate"
echo "  3. Start the server:"
echo "       python run.py"
echo "       # or: uvicorn app.main:app --reload"
echo ""
echo "  API docs: http://localhost:8000/docs"
