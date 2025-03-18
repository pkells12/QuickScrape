# Getting Started with QuickScrape

This guide will help you start using QuickScrape for your first web scraping project.

## First-Time Setup

After installing QuickScrape, you'll want to set up your environment:

1. **Initialize QuickScrape**:
   ```bash
   quickscrape init
   ```
   This command creates a default configuration directory at `~/.quickscrape` and sets up the required folder structure.

2. **Configure API Keys** (Optional):
   If you plan to use natural language selector generation with Claude API:
   ```bash
   # Create an environment file
   touch ~/.quickscrape/.env
   
   # Edit the file with your favorite editor
   # Add the following lines:
   # CLAUDE_API_KEY=your_api_key_here
   ```

## Creating Your First Scraping Project

QuickScrape offers two ways to create a scraping project:

### Using the Interactive Wizard

The wizard is the easiest way for beginners to create a scraping configuration:

```bash
quickscrape wizard
```

The wizard will:
1. Guide you through entering the target URL
2. Help you identify elements to scrape
3. Configure pagination if needed
4. Set up export options
5. Save your configuration with a name of your choice

### Manual Configuration

For more experienced users, you can create a configuration file manually:

1. Create a new YAML file in the `~/.quickscrape/configs` directory:
   ```bash
   touch ~/.quickscrape/configs/my_first_scrape.yaml
   ```

2. Edit the file with a structure like this:
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

3. Validate your configuration:
   ```bash
   quickscrape validate my_first_scrape
   ```

## Running Your First Scrape

Once you have a configuration, you can start scraping:

```bash
quickscrape scrape my_first_scrape
```

This command will:
1. Load your configuration
2. Connect to the specified URL
3. Extract data according to your selectors
4. Handle pagination if configured
5. Save the results in the specified output format

## Understanding the Results

After the scrape completes, you'll find your data in the format specified in your configuration:

- **CSV**: A comma-separated values file that can be opened in spreadsheet applications
- **JSON**: A structured JSON file with all scraped data
- **Excel**: An XLSX file with formatted data
- **SQLite**: A database file that can be queried with SQL

You can examine the data with appropriate tools:

```bash
# For CSV files
cat products.csv
# or
head -n 10 products.csv

# For JSON files
jq . products.json

# For Excel files
# Open with your preferred spreadsheet application

# For SQLite
sqlite3 products.db "SELECT * FROM scraped_data LIMIT 10;"
```

## Scheduling Your First Job

To run your scrape on a schedule:

```bash
quickscrape job create --config my_first_scrape --schedule daily
```

This creates a job that will run your scrape configuration daily.

To list your scheduled jobs:

```bash
quickscrape job list
```

## Next Steps

Now that you've created and run your first scraping project, you can:

- [Explore advanced configuration options](configuration.md)
- [Learn about different selector strategies](scraping-basics.md)
- [Configure more detailed job schedules](scheduling.md)
- [Experiment with different export formats](export-options.md) 