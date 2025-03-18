# Packaging and Distribution Guide

This guide explains how to prepare QuickScrape for distribution via PyPI and other channels.

## Package Structure

QuickScrape follows the standard Python package structure:

```
quickscrape/
├── src/
│   └── quickscrape/
│       ├── __init__.py
│       ├── api/
│       ├── cli/
│       ├── config/
│       ├── core/
│       ├── export/
│       ├── exporters/
│       ├── scraper/
│       ├── scheduler/
│       ├── scheduling/
│       └── utils/
├── tests/
├── docs/
├── examples/
├── samples/
├── pyproject.toml
├── README.md
└── .env.example
```

## Distribution Files

### pyproject.toml

The `pyproject.toml` file defines the build system requirements and package metadata:

```toml
[build-system]
requires = ["setuptools>=42.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "quickscrape"
version = "0.1.0"
description = "A flexible and powerful web scraping tool"
authors = [
    {name = "QuickScrape Team", email = "info@quickscrape.io"}
]
readme = "README.md"
requires-python = ">=3.10"
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Topic :: Internet :: WWW/HTTP :: Browsers",
    "Topic :: Software Development :: Libraries :: Python Modules",
]
dependencies = [
    "click>=8.1.3",
    "rich>=13.0.0",
    "pyyaml>=6.0",
    "pydantic>=2.0.0",
    "beautifulsoup4>=4.11.1",
    "requests>=2.28.1",
    "cloudscraper>=1.2.60",
    "playwright>=1.39.0",
    "pandas>=2.0.0",
    "openpyxl>=3.0.10",
    "nest-asyncio>=1.5.8",
    "httpx>=0.24.0"
]
```

### README.md

The README file provides an overview and basic usage instructions:

```markdown
# QuickScrape

A Python-based CLI tool designed to make web scraping accessible to complete novices.

## Features

- Simple CLI interface for web scraping tasks
- Interactive terminal-based setup wizard
- Automatic detection of appropriate scraping backend
- Support for static and dynamic websites
- Built-in data cleaning and export functionality
- Natural language processing for selector generation
- Basic scheduling system for recurring scraping tasks

## Installation

```bash
pip install quickscrape
```

## Quick Start

```bash
# Initialize
quickscrape init

# Create configuration with wizard
quickscrape wizard

# Run a scrape
quickscrape scrape my_config
```

For more information, see the [documentation](https://quickscrape.readthedocs.io/).
```

### MANIFEST.in

The `MANIFEST.in` file specifies additional files to include in the distribution:

```
include LICENSE
include README.md
include .env.example
include pyproject.toml
recursive-include samples *.yaml
recursive-include docs *.md
recursive-include examples *.py
recursive-include examples *.md
```

## Distribution Preparation

### 1. Update Version

Update the version number in `pyproject.toml`:

```toml
[project]
name = "quickscrape"
version = "0.1.0"  # Change this to the new version
```

### 2. Clean Build Directories

Remove previous build artifacts:

```bash
rm -rf build/ dist/ *.egg-info/
```

### 3. Create Source Distribution

```bash
python -m build --sdist
```

### 4. Create Wheel Distribution

```bash
python -m build --wheel
```

### 5. Check Distributions

Verify the distributions:

```bash
twine check dist/*
```

## Testing the Package

### Test in a Clean Environment

```bash
# Create a clean virtual environment
python -m venv test_env
source test_env/bin/activate  # On Windows: test_env\Scripts\activate

# Install the package from the local dist directory
pip install dist/quickscrape-0.1.0-py3-none-any.whl

# Test basic functionality
quickscrape --version
quickscrape --help
```

### Test with pytest

```bash
# In the project root
python -m pytest
```

## Publishing to PyPI

### Test PyPI First

```bash
# Upload to Test PyPI
twine upload --repository-url https://test.pypi.org/legacy/ dist/*

# Install from Test PyPI
pip install --index-url https://test.pypi.org/simple/ quickscrape
```

### Publish to PyPI

```bash
# Upload to PyPI
twine upload dist/*
```

## Distribution Checklist

- [ ] Update version number
- [ ] Update CHANGELOG.md
- [ ] Run full test suite
- [ ] Build source and wheel distributions
- [ ] Check distributions with twine
- [ ] Test install from local wheel
- [ ] Upload to Test PyPI
- [ ] Test install from Test PyPI
- [ ] Upload to PyPI
- [ ] Tag release in git
- [ ] Create GitHub release

## Continuous Integration

Set up GitHub Actions for continuous integration:

```yaml
# .github/workflows/python-package.yml
name: Python package

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.10, 3.11]

    steps:
    - uses: actions/checkout@v3
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install pytest pytest-cov build twine
        pip install -e ".[dev]"
    - name: Lint with ruff
      run: |
        python -m ruff check .
    - name: Test with pytest
      run: |
        pytest --cov=quickscrape
    - name: Build package
      run: |
        python -m build
    - name: Check package
      run: |
        twine check dist/*
```

## Automatic Release

Set up GitHub Actions for automatic releases:

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install build twine
    - name: Build and publish
      env:
        TWINE_USERNAME: ${{ secrets.PYPI_USERNAME }}
        TWINE_PASSWORD: ${{ secrets.PYPI_PASSWORD }}
      run: |
        python -m build
        twine upload dist/*
```

## Next Steps

After successful release, update the documentation site and announce the release on appropriate channels. 