# QuickScrape

![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

A powerful, flexible, and user-friendly web scraping tool designed to make web scraping accessible to complete novices while providing advanced features for experienced users.

## 🚀 Features

- **User-Friendly CLI**: Simple command-line interface for web scraping tasks
- **Interactive Setup**: Terminal-based wizard for creating scraping configurations
- **Intelligent Backend Selection**: Automatic detection of appropriate scraping technology
- **Multiple Scraping Engines**: Support for static (requests/BeautifulSoup) and dynamic (Playwright) websites
- **Anti-Bot Measures**: Built-in methods to avoid detection and blocking
- **Data Processing**: Robust data extraction, cleaning, and type conversion
- **Flexible Export Options**: Export to CSV, JSON, Excel, and more
- **Natural Language Processing**: Generate CSS selectors from natural language descriptions using Claude API
- **Powerful Scheduling System**: Schedule scraping jobs to run at specific times or intervals
- **Comprehensive Error Handling**: Detailed error reporting and recovery mechanisms

## 📋 Installation

### Prerequisites

- Python 3.10 or higher
- pip or uv (recommended)

### Install from PyPI

```bash
pip install quickscrape
```

### Install using uv (recommended)

```bash
uv install quickscrape
```

### Development Installation

1. Clone the repository:
```bash
git clone https://github.com/pkells12/QuickScrape.git
cd QuickScrape
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies with uv:
```bash
uv pip install -e ".[dev]"
```

## 🚀 Quick Start

### Basic Usage

1. Initialize a new scraping configuration:
```bash
quickscrape init
```

2. Use the setup wizard to create a scraping configuration:
```bash
quickscrape wizard
```

3. Run a scraping job:
```bash
quickscrape scrape my_config
```

4. List available configurations:
```bash
quickscrape list
```

### Job Scheduling

1. Create a new scheduled job:
```bash
quickscrape job create --name daily_news --config news_scraper --schedule daily --time "08:00"
```

2. List all scheduled jobs:
```bash
quickscrape job list
```

3. Start the scheduler:
```bash
quickscrape scheduler start
```

4. Check scheduler status:
```bash
quickscrape scheduler status
```

## ⚙️ Configuration

QuickScrape uses YAML files for configuration. These can be created manually or using the setup wizard.

Example configuration:
```yaml
url: https://example.com/products
selectors:
  product_name: ".product-title"
  product_price: ".product-price"
  product_description: ".product-description"
pagination:
  type: "next_button"
  selector: ".pagination .next"
  max_pages: 5
output:
  format: "csv"
  path: "products.csv"
```

## 📊 Export Options

QuickScrape supports multiple export formats:

- CSV
- JSON
- Excel
- SQLite
- Custom exporters

Example export configuration:
```yaml
output:
  format: "excel"
  path: "products.xlsx"
  options:
    sheet_name: "Product Data"
    include_index: false
```

## 🔄 Scheduling System

The scheduling system allows you to run scraping jobs automatically:

- **One-time jobs**: Run jobs at a specific date and time
- **Recurring jobs**: Schedule jobs to run daily, weekly, or monthly
- **Custom schedules**: Create complex schedules using cron syntax

Jobs can be managed through the CLI:
```bash
# Create a weekly job running every Monday at 9 AM
quickscrape job create --name weekly_data --config data_scraper --schedule weekly --day monday --time "09:00"

# Update an existing job
quickscrape job update weekly_data --schedule daily --time "10:00"

# Delete a job
quickscrape job delete weekly_data
```

## 📚 Documentation

For more detailed documentation, please refer to the [docs](docs/) directory:

- [User Guide](docs/user-guide/) - Installation, configuration, and usage instructions
- [API Reference](docs/api-reference/) - Detailed API documentation
- [Examples](docs/examples/) - Example configurations and use cases
- [Troubleshooting](docs/troubleshooting/) - Solutions to common issues

## 🧪 Testing

Run tests with pytest:

```bash
pytest
```

Run tests with coverage reports:

```bash
pytest --cov=quickscrape
```

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request 