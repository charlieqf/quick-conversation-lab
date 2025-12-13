import os
import sys
import json
import datetime
from sqlalchemy import create_engine, inspect, text
from google.cloud import storage
import logging

# Add parent directory to path to import config if needed, 
# but we basically just need database connection and bucket name.
# We will use standalone logic to avoid complex dependencies, 
# but we need to load .env variables.

from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def backup_to_gcs():
    # 1. Load Environment Variables
    # Assuming script is run from project root or backend dir
    # Try to find .env in backend/ or ./
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
    else:
        load_dotenv() # Try default

    database_url = os.getenv("DATABASE_URL")
    bucket_name = os.getenv("GCS_BUCKET_NAME", "voice-model-lab") # Default fallback

    if not database_url:
        logger.error("DATABASE_URL not found in environment variables.")
        return

    logger.info(f"Starting backup process...")
    logger.info(f"Target Bucket: {bucket_name}")

    # 2. Connect to Database
    try:
        # SQLite handling for local dev compatibility
        connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
        engine = create_engine(database_url, connect_args=connect_args)
        connection = engine.connect()
        logger.info("Connected to database successfully.")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        return

    # 3. Setup GCS Client
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
    except Exception as e:
        logger.error(f"Failed to initialize GCS client: {e}")
        logger.error("Ensure GOOGLE_APPLICATION_CREDENTIALS is set or you are authenticated.")
        # We might continue if just testing DB extraction, but for this script we fail.
        return

    # 4. Backup Tables
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    
    for table in table_names:
        logger.info(f"Backing up table: {table}")
        try:
            # Fetch all data using text query to avoid ORM complexity for raw dump
            result = connection.execute(text(f"SELECT * FROM {table}"))
            keys = result.keys()
            rows = result.fetchall()
            
            # Convert to list of dicts
            data = []
            for row in rows:
                # Handle non-serializable types if any (datetime, etc)
                row_dict = {}
                for idx, key in enumerate(keys):
                    val = row[idx]
                    if isinstance(val, (datetime.date, datetime.datetime)):
                        val = val.isoformat()
                    row_dict[key] = val
                data.append(row_dict)
            
            # Serialize to JSON
            json_data = json.dumps(data, indent=2, ensure_ascii=False)
            
            # Upload to GCS
            blob_name = f"backups/{timestamp}/{table}.json"
            blob = bucket.blob(blob_name)
            blob.upload_from_string(json_data, content_type='application/json')
            
            logger.info(f"Uploaded {len(data)} records to gs://{bucket_name}/{blob_name}")
            
        except Exception as e:
            logger.error(f"Error backing up table {table}: {e}")

    connection.close()
    logger.info("Backup process completed.")

if __name__ == "__main__":
    backup_to_gcs()
