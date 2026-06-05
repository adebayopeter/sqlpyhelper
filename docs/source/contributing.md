# Contributing

We welcome contributions from the open-source community.

## Setting up the development environment

1. Fork and clone the repository:

```bash
git clone https://github.com/your-username/sqlpyhelper.git
cd sqlpyhelper
```

2. Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate
pip install -e ".[all]"
pip install pytest pytest-mock sphinx sphinx-rtd-theme myst-parser
```

3. Copy the example environment file:

```bash
cp .env_example .env
```

## Running the tests

```bash
pytest test/ -v
```

## Running the pre-commit checks

```bash
./pre-commit.sh
```

## Submitting a pull request

1. Create a branch: `git checkout -b fix/your-fix-name`
2. Make your changes
3. Run `./pre-commit.sh` and confirm it passes
4. Commit with a clear message
5. Push and open a pull request against the `main` branch

## Reporting a bug

Open an issue at https://github.com/adebayopeter/sqlpyhelper/issues

Include: Python version, database type, minimal code to reproduce,
and the full error traceback.
