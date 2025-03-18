# Configuration Guide

QuickScrape uses YAML configuration files to define scraping projects. This guide explains the configuration options and provides examples.

## Configuration File Format

Configuration files are stored in `~/.quickscrape/configs/` by default and use the YAML format.

### Basic Structure

```yaml
# Basic configuration structure
url: "https://example.com/products"  # Target URL to scrape
name: "Example Scraper"              # Human-readable name (optional)
description: "Scrapes product data"  # Description (optional)
selectors:                           # Elements to extract
  product_name: ".product-title"
  product_price: ".product-price"
pagination:                          # How to navigate through pages (optional)
  type: "next_button"
  selector: ".pagination .next"
output:                              # How to save extracted data
  format: "csv"
  path: "products.csv"
```

## Required Settings

### URL

The target URL to scrape. This can be a single URL or a list of URLs:

```yaml
# Single URL
url: "https://example.com/products"

# Multiple URLs
urls:
  - "https://example.com/products/page1"
  - "https://example.com/products/page2"
```

### Selectors

Defines what data to extract from the page. Each selector is a key-value pair where:
- The key is the name of the data field
- The value is a CSS or XPath selector to locate the element

```yaml
selectors:
  # CSS selectors (recommended)
  product_name: ".product-title"
  product_price: ".product-price"
  
  # XPath selectors
  product_sku: "xpath://div[@class='sku']"
  
  # Attribute extraction
  product_url: 
    selector: ".product-link" 
    attribute: "href"
  
  # Nested elements
  product_details:
    selector: ".product-details"
    children:
      weight: ".weight"
      dimensions: ".dimensions"
```

### Output

Defines how and where to save the extracted data:

```yaml
output:
  format: "csv"         # Format: csv, json, excel, sqlite
  path: "products.csv"  # Output file path
```

## Optional Settings

### Pagination

Configures how to navigate through multiple pages:

```yaml
pagination:
  # Using a "Next" button
  type: "next_button"
  selector: ".pagination .next"
  max_pages: 5  # Optional limit
  
  # Using page numbers
  type: "page_number"
  url_template: "https://example.com/products?page={page}"
  start_page: 1
  end_page: 10
  
  # Using "Load More" buttons
  type: "load_more"
  selector: ".load-more-button"
  max_clicks: 5
```

### Headers and User Agent

Set custom HTTP headers or user agent:

```yaml
headers:
  User-Agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
  Accept-Language: "en-US,en;q=0.9"
  
# Or set just the user agent
user_agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
```

### Delays

Add delays between requests to avoid rate limiting:

```yaml
delays:
  # Fixed delay (in seconds)
  type: "fixed"
  value: 2
  
  # Random delay (in seconds)
  type: "random"
  min: 1
  max: 5
```

### Authentication

Configure authentication for protected pages:

```yaml
authentication:
  # Basic form login
  type: "form"
  login_url: "https://example.com/login"
  form_selector: "#login-form"
  fields:
    username: "your_username"
    password: "your_password"
  submit_button: "#submit-button"
  
  # HTTP Basic Authentication
  type: "http_basic"
  username: "your_username"
  password: "your_password"
```

### Scraping Backend

Specify which backend to use:

```yaml
backend: "playwright"  # Options: requests, cloudscraper, playwright
```

### Data Cleaning

Configure automatic data cleaning:

```yaml
data_cleaning:
  strip_html: true
  normalize_whitespace: true
  trim: true
  convert_numbers: true
  convert_dates: true
```

## Configuration Examples

### E-commerce Product Listing

```yaml
name: "E-Commerce Products"
description: "Scrapes product data from an e-commerce site"
url: "https://example-store.com/products"
backend: "playwright"  # For JavaScript-heavy sites

selectors:
  product_name: ".product-item h3"
  product_price: ".product-price .current-price"
  product_rating: ".product-rating .stars"
  product_url:
    selector: ".product-item a"
    attribute: "href"
  product_image:
    selector: ".product-image img" 
    attribute: "src"
    
pagination:
  type: "next_button"
  selector: ".pagination .next"
  max_pages: 10
  
delays:
  type: "random"
  min: 1
  max: 3
  
data_cleaning:
  strip_html: true
  normalize_whitespace: true
  convert_numbers: true

output:
  format: "excel"
  path: "products.xlsx"
```

### News Articles

```yaml
name: "News Articles"
description: "Scrapes news articles from a news website"
url: "https://example-news.com/tech"

selectors:
  article_title: "article h2"
  article_date: ".article-date"
  article_summary: ".article-summary"
  article_author: ".article-author"
  article_content: 
    selector: "article .content"
    extract_html: true  # Keep HTML formatting
    
pagination:
  type: "load_more"
  selector: ".load-more-button"
  max_clicks: 5
  
data_cleaning:
  normalize_whitespace: true
  convert_dates: true
  
output:
  format: "json"
  path: "articles.json"
```

## Validating Configurations

To validate a configuration file:

```bash
quickscrape validate my_config
```

This checks the configuration for errors before running a scrape.

## Using Environment Variables

You can use environment variables in your configuration files:

```yaml
authentication:
  type: "form"
  fields:
    username: "${USERNAME}"
    password: "${PASSWORD}"
```

Set these variables in your `.env` file in the QuickScrape directory or as system environment variables.

## Next Steps

- [Learn about scraping basics](scraping-basics.md)
- [Explore CLI usage](cli-usage.md)
- [Check out advanced usage options](advanced-usage.md) 