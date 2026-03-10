import logging
from browser_history import get_history
from client.sqlite_db import batch_store_logs # Ensure this matches your batch logic

def collect_websites():
    """Collects history from all supported browsers and platforms automatically."""
    try:
        # 1. Fetch history from ALL browsers (Chrome, Firefox, Safari, Edge, etc.)
        # This returns a list of (datetime_obj, url)
        outputs = get_history()
        
        # 2. Convert to your standard log format
        formatted_logs = []
        for dt, url in outputs.histories:
            formatted_logs.append({
                "url": url,
                "timestamp": dt.isoformat(),
                "source": "browser_history_auto"
            })

        # 3. Batch store only the NEW logs (standard efficiency)
        if formatted_logs:
            batch_store_logs("website", formatted_logs)
            
    except Exception as e:
        logging.error(f"Website collector failed: {e}")

# In your sqlite_db.py, ensure your INSERT uses 'OR IGNORE' 
# to prevent duplicate URL entries if you run this frequently.
# c.executemany("INSERT OR IGNORE INTO logs ...")
