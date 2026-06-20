# Contributing to SQLPyHelper

Thank you for your interest in contributing. This document explains how to
get set up and submit a pull request.

## Setting up the development environment

1. Fork and clone the repository:
   git clone https://github.com/your-username/sqlpyhelper.git
   cd sqlpyhelper

2. Create a virtual environment and install dependencies:
   python -m venv venv
   source venv/bin/activate        # Windows: venv\Scripts\activate
   pip install -e ".[all]"
   pip install pytest pytest-mock pytest-asyncio

3. Copy the example environment file:
   cp .env_example .env
   # Edit .env with your local database credentials if running integration tests

## Running the tests

   pytest test/

## Submitting a pull request

1. Create a branch: git checkout -b fix/your-fix-name
2. Make your changes
3. Run the tests and confirm they pass
4. Commit with a clear message describing what changed and why
5. Push and open a pull request against the main branch

## Reporting a bug

Open an issue at https://github.com/adebayopeter/sqlpyhelper/issues
Include: Python version, database type, minimal code to reproduce, and the
full error traceback.

## Code style

- Follow PEP 8
- Add type annotations to any new public methods
- Add or update tests for any changed behaviour