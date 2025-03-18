# Installation Guide

This guide will walk you through the process of installing QuickScrape on your system.

## System Requirements

- **Python**: 3.10 or higher
- **Operating System**: Windows, macOS, or Linux
- **Disk Space**: Approximately 100MB including dependencies
- **Memory**: Minimum 512MB RAM (2GB+ recommended for larger scraping jobs)
- **Internet Connection**: Required for installation and most scraping tasks

## Installation Methods

### Using pip (Python Package Installer)

The simplest way to install QuickScrape is using pip:

```bash
pip install quickscrape
```

### Using uv (Recommended)

For faster installation and dependency resolution, we recommend using [uv](https://github.com/astral-sh/uv):

```bash
uv install quickscrape
```

### Development Installation

For developers or those who want to contribute to QuickScrape:

1. Clone the repository:
```bash
git clone https://github.com/yourusername/quickscrape.git
cd quickscrape
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the package in development mode:
```bash
pip install -e ".[dev]"
```

## Virtual Environment Setup

We recommend using a virtual environment to avoid conflicts with other Python packages:

### Using venv (Built into Python)

```bash
# Create a virtual environment
python -m venv quickscrape-env

# Activate the environment
# On Windows:
quickscrape-env\Scripts\activate
# On macOS/Linux:
source quickscrape-env/bin/activate

# Install QuickScrape
pip install quickscrape
```

### Using uv with Virtual Environments

```bash
# Create a virtual environment
uv venv

# Activate the environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install QuickScrape
uv install quickscrape
```

## Verifying Installation

To verify that QuickScrape was installed correctly:

```bash
quickscrape --version
```

You should see the version number of QuickScrape printed to the console.

## Troubleshooting Installation

If you encounter issues during installation:

1. **Outdated pip**: Try upgrading pip before installation:
   ```bash
   pip install --upgrade pip
   ```

2. **Missing dependencies**: Some dependencies may require additional system packages:
   - On Ubuntu/Debian: `sudo apt-get install python3-dev build-essential`
   - On Fedora: `sudo dnf install python3-devel gcc`
   - On macOS: `xcode-select --install`
   - On Windows: Ensure Visual C++ Build Tools are installed

3. **Permission errors**: If you encounter permission errors, try:
   ```bash
   pip install --user quickscrape
   ```

4. **Environment variables**: After installation with `--user`, you may need to add the user bin directory to your PATH.

For more troubleshooting help, see the [Troubleshooting Guide](../troubleshooting/installation-issues.md).

## Next Steps

Now that you have QuickScrape installed, you can:

- Continue to the [Getting Started Guide](getting-started.md)
- Learn about [Configuration Options](configuration.md)
- Explore [CLI Usage](cli-usage.md) 