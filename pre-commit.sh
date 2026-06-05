#!/bin/bash
set -e

echo "🔍 Running pre-commit checks..."

echo "1️⃣ Formatting code with Black..."
black sqlpyhelper/ test/

echo "2️⃣ Sorting imports with isort..."
isort sqlpyhelper/ test/

echo "3️⃣ Checking linting with flake8..."
flake8 sqlpyhelper/ test/

echo "4️⃣ Type checking with mypy..."
mypy sqlpyhelper/

echo "5️⃣ Running tests..."
pytest test/ -v

echo "✅ All checks passed! Ready to commit."
