# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build/Run Commands
- Run app: `flask run` or `python src/main.py`
- Docker: `docker-compose up --build`
- Tests: `pytest tests/`
- Linting: `flake8 src/`

## Code Style Guidelines
- Naming: snake_case for variables/functions, PascalCase for classes
- Imports: stdlib first, then third-party, then local modules
- Docstrings: Full docstrings with parameter descriptions and return types
- Type hints: Use Python typing system (e.g., `pd.DataFrame | None`)
- Error handling: Always use try/except with proper logging
- Logging: Use logging module with appropriate levels
- New agents should follow existing agent class patterns
- Use f-strings for string formatting
- Conform to PEP 8 style guide

## Architecture
- Flask-based web app with MySQL backend
- Agent-based ML pipeline with distinct processing stages
- MLflow for experiment tracking
- Standard Python package structure