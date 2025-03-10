#!/usr/bin/env python3
import os
import time
import json
import schedule
import requests
import logging
import threading
import asyncio
import aiohttp
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient
from pathlib import Path

# Import from our compressor library for bill processing
try:
    from compressor import DocumentProcessor
except ImportError:
    # If not available, we'll handle this gracefully later
    DocumentProcessor = None

'''
Note, Legiscan maxes out at 30k queries per month. Reset on the 1st of each month
'''

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("legiscan_poller.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Constants
LEGISCAN_API_KEY = os.getenv('LEGISCAN_API_KEY', 'your_api_key_here')
BILLS_DIRECTORY = os.getenv('BILLS_DIRECTORY', '/usr/src/app/bills')
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://mongodb:27017/billbuster')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

# Ensure bills directory exists
os.makedirs(BILLS_DIRECTORY, exist_ok=True)

# List of all states plus federal
STATES = [
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
    'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
    'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
    'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
    'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY',
    'DC', 'US'  # DC and US (federal)
]

# MongoDB connection
def get_mongodb_client():
    client = MongoClient(MONGODB_URI)
    return client

# Ensure MongoDB schema is initialized
def ensure_db_schema():
    """
    Initialize the MongoDB schema if it doesn't exist.
    This ensures the collections and indexes are properly set up.
    """
    try:
        client = get_mongodb_client()
        db = client.billbuster
        
        # Check if the bills collection exists, create it if not
        collections = db.list_collection_names()
        if 'bills' not in collections:
            logger.info("Creating bills collection")
            db.create_collection('bills')
        
        # Create index on billId for faster lookups
        db.bills.create_index('billId')
        
        # Create indexes on common search fields
        db.bills.create_index('state')
        db.bills.create_index('isFederal')
        db.bills.create_index('date')
        db.bills.create_index('tags')
        
        logger.info("MongoDB schema initialized")
        client.close()
    except Exception as e:
        logger.error(f"Error ensuring database schema: {str(e)}")

async def process_bill_async(bill_path):
    """
    Asynchronous function to process a downloaded bill
    """
    try:
        logger.info(f"Processing bill asynchronously: {bill_path}")
        
        # Check if we have the compressor and OpenAI API key
        if DocumentProcessor and OPENAI_API_KEY:
            try:
                logger.info(f"Using compressor to analyze bill content")
                processor = DocumentProcessor(
                    openai_api_key=OPENAI_API_KEY,
                    model_name="gpt-4-turbo", 
                    chunk_size=4000,
                    chunk_overlap=500
                )
                
                # Process the document
                result, stats = processor.process_document(bill_path)
                
                # Get MongoDB client
                client = get_mongodb_client()
                db = client.billbuster
                bills_collection = db.bills
                
                # Find the bill in the database by file path
                bill_query = {"filePath": {"$in": [bill_path]}}
                bill = bills_collection.find_one(bill_query)
                
                if bill:
                    # Update the bill with analysis results
                    # Join summary paragraphs into a single string, since the model expects a string, not an array
                    summary_text = " ".join(result["summary"]) if isinstance(result["summary"], list) else result["summary"]
                    
                    update_data = {
                        "summary": summary_text,
                        "tags": result["tags"],
                        "points": result["points"]
                    }
                    
                    bills_collection.update_one(
                        {"_id": bill["_id"]},
                        {"$set": update_data}
                    )
                    
                    logger.info(f"Updated bill {bill['_id']} with analysis results")
                else:
                    logger.warning(f"Bill not found in database for file path: {bill_path}")
                
                client.close()
                
                # Save a copy of the analysis results
                output_path = bill_path + '.analysis.json'
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2)
                
                logger.info(f"Analysis results saved to: {output_path}")
                
            except Exception as e:
                logger.error(f"Error using compressor to process bill: {str(e)}")
        else:
            # If compressor not available, log and continue
            if not DocumentProcessor:
                logger.warning("Compressor library not available for bill analysis")
            if not OPENAI_API_KEY:
                logger.warning("OpenAI API key not set, cannot analyze bill content")
                
        # Simulate some async processing
        await asyncio.sleep(1)
        
        logger.info(f"Finished processing bill: {bill_path}")
        return {"status": "success", "bill_path": bill_path}
    except Exception as e:
        logger.error(f"Error processing bill {bill_path}: {str(e)}")
        return {"status": "error", "bill_path": bill_path, "error": str(e)}

def start_bill_processing_thread(bill_path):
    """
    Start a new thread to process a bill asynchronously
    """
    def run_async_processing():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(process_bill_async(bill_path))
            logger.info(f"Async processing result: {result}")
        finally:
            loop.close()
    
    thread = threading.Thread(target=run_async_processing)
    thread.daemon = True
    thread.start()
    logger.info(f"Started processing thread for bill: {bill_path}")
    return thread

def get_bill_details(bill_id, state):
    """
    Get detailed information about a specific bill
    """
    try:
        url = f"https://api.legiscan.com/?key={LEGISCAN_API_KEY}&op=getBill&id={bill_id}&state={state}"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'OK':
                return data.get('bill', {})
            else:
                logger.error(f"LegiScan API error: {data.get('alert', 'Unknown error')}")
        else:
            logger.error(f"Failed to get bill details. Status code: {response.status_code}")
        
        return None
    except Exception as e:
        logger.error(f"Error getting bill details: {str(e)}")
        return None

def download_bill(bill_id, state):
    """
    Download a bill and save it to disk
    """
    try:
        url = f"https://api.legiscan.com/?key={LEGISCAN_API_KEY}&op=getBillText&id={bill_id}&state={state}"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'OK':
                text_data = data.get('text', {})
                if not text_data:
                    logger.warning(f"No text data available for bill {bill_id} in state {state}")
                    return None
                
                # Create state directory if it doesn't exist
                state_dir = os.path.join(BILLS_DIRECTORY, state)
                os.makedirs(state_dir, exist_ok=True)
                
                # Save bill text to file
                doc_id = text_data.get('doc_id', 'unknown')
                bill_number = text_data.get('bill_number', f'bill_{bill_id}')
                filename = f"{state}_{bill_number}_{doc_id}.txt"
                file_path = os.path.join(state_dir, filename)
                
                # Decode and save the bill text
                bill_text = text_data.get('doc', '')
                if bill_text:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(bill_text)
                    logger.info(f"Bill saved to {file_path}")
                    return file_path
                else:
                    logger.warning(f"Empty bill text for {bill_id} in state {state}")
            else:
                logger.error(f"LegiScan API error: {data.get('alert', 'Unknown error')}")
        else:
            logger.error(f"Failed to download bill. Status code: {response.status_code}")
        
        return None
    except Exception as e:
        logger.error(f"Error downloading bill: {str(e)}")
        return None

def check_for_new_bills(state):
    """
    Check for new bills in a specific state
    """
    try:
        logger.info(f"Checking for new bills in {state}")
        
        # Get MongoDB client
        client = get_mongodb_client()
        db = client.billbuster
        bills_collection = db.bills
        
        # Get the list of bills from LegiScan API
        url = f"https://api.legiscan.com/?key={LEGISCAN_API_KEY}&op=getMasterList&state={state}"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'OK':
                master_list = data.get('masterlist', {})
                
                # Process each bill in the master list
                for bill_id, bill_info in master_list.items():
                    if bill_id == 'session':  # Skip session info
                        continue
                    
                    # Check if we already have this bill in our database
                    existing_bill = bills_collection.find_one({
                        'billId': bill_id,
                        'state': state
                    })
                    
                    if not existing_bill:
                        logger.info(f"Found new bill: {bill_info.get('number')} in state {state}")
                        
                        # Get detailed bill information
                        bill_details = get_bill_details(bill_id, state)
                        if bill_details:
                            # Download the bill text
                            bill_path = download_bill(bill_id, state)
                            
                            if bill_path:
                                # Determine if the bill is federal
                                is_federal = (state == 'US')
                                
                                # Get proposer information if available
                                proposer = ''
                                if bill_details.get('sponsors'):
                                    sponsors = bill_details.get('sponsors')
                                    if isinstance(sponsors, list) and len(sponsors) > 0:
                                        proposer = sponsors[0].get('name', '')
                                
                                # Store bill info in MongoDB using the required schema
                                bill_record = {
                                    'billId': bill_id,
                                    'date': datetime.now(),
                                    'isFederal': is_federal,
                                    'state': state,
                                    'filePath': [bill_path],
                                    'proposer': proposer,
                                    'status': bill_details.get('status', {}).get('status_desc', ''),
                                    'title': bill_info.get('title', ''),
                                    'citation': [],  # Will be populated later with analysis
                                    'tags': [],      # Will be populated later with analysis
                                    'summary': '',   # Will be populated later with analysis
                                    'points': []     # Will be populated later with analysis
                                }
                                
                                bills_collection.insert_one(bill_record)
                                logger.info(f"Saved bill {bill_info.get('number')} to database")
                                
                                # Start a thread to process the bill asynchronously
                                start_bill_processing_thread(bill_path)
                            else:
                                logger.warning(f"Failed to download bill {bill_id} for state {state}")
                    else:
                        logger.debug(f"Bill {bill_info.get('number')} already exists in database")
            else:
                logger.error(f"LegiScan API error for state {state}: {data.get('alert', 'Unknown error')}")
        else:
            logger.error(f"Failed to get master list for state {state}. Status code: {response.status_code}")
        
        client.close()
    except Exception as e:
        logger.error(f"Error checking for new bills in state {state}: {str(e)}")

def poll_legiscan_api():
    """
    Poll the LegiScan API for all states and federal bills
    """
    try:
        logger.info("Starting LegiScan API polling process")
        
        # Process each state
        for state in STATES:
            check_for_new_bills(state)
            # Add a small delay between states to avoid rate limiting
            time.sleep(1)
        
        logger.info("Completed LegiScan API polling process")
    except Exception as e:
        logger.error(f"Error in poll_legiscan_api: {str(e)}")

def main():
    """
    Main function to schedule and run the API polling
    """
    logger.info("LegiScan API Poller service started")
    
    # Ensure the database schema is properly set up
    ensure_db_schema()
    
    # Run once at startup
    poll_legiscan_api()
    
    # Schedule to run every 24 hours
    schedule.every(24).hours.do(poll_legiscan_api)
    
    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute for pending tasks

if __name__ == "__main__":
    main()