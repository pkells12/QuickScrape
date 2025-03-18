# Setting Up Daily Scrapes

This example demonstrates how to set up a daily scraping job using QuickScrape's scheduling system.

## Use Case: Daily Price Monitoring

In this example, we'll set up a job to scrape product prices daily from an e-commerce website and save them to a CSV file with the date in the filename.

## Step 1: Create the Scraping Configuration

First, we need a configuration for our scrape. We can create it using the wizard:

```bash
quickscrape wizard --name price_monitor
```

Follow the wizard prompts:
1. Enter the target URL (e.g., `https://example-store.com/products`)
2. Select elements to scrape:
   - Product name: `.product-title`
   - Product price: `.product-price`
   - Product ID: `.product-sku`
3. Configure pagination if needed
4. Set the output format to CSV

## Step 2: Test the Configuration

Before scheduling, verify that the configuration works:

```bash
quickscrape scrape price_monitor
```

Check the output file to ensure it contains the expected data.

## Step 3: Create a Daily Job

Now, let's schedule this to run daily at 9:00 AM:

```bash
quickscrape job create \
  --config price_monitor \
  --schedule daily \
  --at "09:00" \
  --output-path "prices_{date}.csv" \
  --description "Daily price monitoring at 9 AM"
```

The `{date}` placeholder in the output path will be replaced with the current date (format: YYYY-MM-DD) when the job runs.

## Step 4: Start the Scheduler

Start the scheduler to execute the job according to its schedule:

```bash
quickscrape scheduler start
```

You can check that the job is properly scheduled:

```bash
quickscrape job list
```

You should see your job with its next scheduled run time.

## Step 5: Add Notifications (Optional)

To get notified when the job completes or fails, you can add callback scripts:

Create a success notification script (`notify_success.sh`):

```bash
#!/bin/bash
# notify_success.sh
echo "Price monitoring completed successfully on $(date)" >> ~/price_monitoring.log
# Add email or other notification methods here
```

Create a failure notification script (`notify_failure.sh`):

```bash
#!/bin/bash
# notify_failure.sh
echo "Price monitoring failed on $(date)" >> ~/price_monitoring.log
# Add email or other notification methods here
```

Make them executable:

```bash
chmod +x notify_success.sh notify_failure.sh
```

Update the job to use these callbacks:

```bash
quickscrape job update JOB_ID \
  --on-success "/path/to/notify_success.sh" \
  --on-failure "/path/to/notify_failure.sh"
```

Replace `JOB_ID` with the ID shown in the job list.

## Step 6: Set Up as a System Service (For Production)

For reliable operation on a server, set up the scheduler as a system service:

### For systemd (Linux):

Create a service file:

```bash
sudo nano /etc/systemd/system/quickscrape.service
```

Add the following content:

```ini
[Unit]
Description=QuickScrape Scheduler
After=network.target

[Service]
ExecStart=/usr/local/bin/quickscrape scheduler start
User=your_username
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl enable quickscrape
sudo systemctl start quickscrape
```

## Step 7: Analyzing the Collected Data

After running for several days, you can analyze the price trends:

```python
import pandas as pd
import glob
import matplotlib.pyplot as plt

# Read all CSV files
all_files = glob.glob('prices_*.csv')
dfs = []

for filename in all_files:
    df = pd.read_csv(filename)
    # Extract date from filename
    date = filename.split('_')[1].split('.')[0]
    df['date'] = pd.to_datetime(date)
    dfs.append(df)

# Combine all data
combined_df = pd.concat(dfs)

# Plot price trends for a specific product
product_df = combined_df[combined_df['product_name'] == 'Example Product']
plt.figure(figsize=(10, 5))
plt.plot(product_df['date'], product_df['product_price'])
plt.title('Price Trend for Example Product')
plt.xlabel('Date')
plt.ylabel('Price')
plt.savefig('price_trend.png')
```

## Complete Example Script

Here's a Python script that sets up the daily scrape programmatically:

```python
from quickscrape.config import ConfigManager
from quickscrape.scheduling import JobManager, JobSchedule, Scheduler
import os

# Ensure configuration directory exists
os.makedirs(os.path.expanduser("~/.quickscrape/configs"), exist_ok=True)

# Create configuration if not exists
config_manager = ConfigManager()
if not config_manager.config_exists("price_monitor"):
    config = {
        "url": "https://example-store.com/products",
        "selectors": {
            "product_name": ".product-title",
            "product_price": ".product-price",
            "product_id": ".product-sku"
        },
        "pagination": {
            "type": "next_button",
            "selector": ".pagination .next",
            "max_pages": 5
        },
        "output": {
            "format": "csv",
            "path": "prices.csv"
        }
    }
    config_manager.save_config("price_monitor", config)

# Create job manager
job_manager = JobManager()

# Create daily schedule at 9:00 AM
schedule = JobSchedule.daily(time="09:00")

# Create job with the schedule
job = job_manager.create_job(
    config_name="price_monitor",
    schedule=schedule,
    description="Daily price monitoring at 9 AM",
    output_format="csv",
    output_path="prices_{date}.csv",
    on_success="/path/to/notify_success.sh",
    on_failure="/path/to/notify_failure.sh"
)

print(f"Created job with ID: {job.id}")

# Start the scheduler
scheduler = Scheduler(job_manager)
scheduler.start()

print("Scheduler started. Press Ctrl+C to stop.")
try:
    # Keep the script running
    import time
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Stopping scheduler...")
    scheduler.stop()
    print("Scheduler stopped.")
```

## Additional Tips

1. **Rotating Files**: For long-running jobs, consider implementing file rotation to avoid disk space issues.

2. **Error Handling**: Set appropriate retry values for jobs that might fail due to temporary network issues:
   ```bash
   quickscrape job update JOB_ID --max-retries 3 --retry-delay 300
   ```

3. **Monitoring**: Regularly check job status and logs:
   ```bash
   quickscrape job list
   quickscrape job logs JOB_ID
   ```

4. **Backup**: Back up your collected data regularly:
   ```bash
   # Example backup script
   tar -czf price_data_backup_$(date +%F).tar.gz prices_*.csv
   ```

5. **Resource Usage**: Monitor system resource usage, especially for frequent or large scraping jobs.