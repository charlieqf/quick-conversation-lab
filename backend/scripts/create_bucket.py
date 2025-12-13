from google.cloud import storage
import logging

logging.basicConfig(level=logging.INFO)

def create_bucket_if_not_exists(bucket_name):
    storage_client = storage.Client()
    
    try:
        bucket = storage_client.get_bucket(bucket_name)
        logging.info(f"Bucket {bucket_name} already exists.")
    except Exception:
        logging.info(f"Bucket {bucket_name} not found. Creating...")
        try:
            bucket = storage_client.create_bucket(bucket_name, location="asia-northeast1")
            logging.info(f"Bucket {bucket_name} created.")
        except Exception as e:
            logging.error(f"Failed to create bucket: {e}")

if __name__ == "__main__":
    create_bucket_if_not_exists("voice-model-lab")
