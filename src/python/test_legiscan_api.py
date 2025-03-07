#!/usr/bin/env python3
"""
Simple script to test the LegiScan API key.
Run this script to verify that your API key is working correctly.

Usage:
    python test_legiscan_api.py <your_api_key>
"""

import sys
import requests
import json

def test_legiscan_api(api_key):
    """Test the LegiScan API key by making a simple request."""
    print(f"Testing LegiScan API key: {api_key[:5]}...")
    
    # Test URL - get the master list for US (federal)
    url = f"https://api.legiscan.com/?key={api_key}&op=getMasterList&state=US"
    
    try:
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('status') == 'OK':
                print("✅ API key is valid!")
                print("\nSample data from the API:")
                
                # Print some sample data
                session = data.get('masterlist', {}).get('session', {})
                if session:
                    print(f"Session: {session.get('name', 'Unknown')}")
                    print(f"Session ID: {session.get('session_id', 'Unknown')}")
                
                # Count the number of bills
                bill_count = sum(1 for k in data.get('masterlist', {}).keys() if k != 'session')
                print(f"Number of bills in the master list: {bill_count}")
                
                return True
            else:
                print(f"❌ API Error: {data.get('alert', 'Unknown error')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
    
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
    
    return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_legiscan_api.py <your_api_key>")
        sys.exit(1)
    
    api_key = sys.argv[1]
    success = test_legiscan_api(api_key)
    
    if not success:
        print("\nPlease check your API key and try again.")
        print("You can obtain a LegiScan API key from: https://legiscan.com/legiscan")
        sys.exit(1)
    
    print("\nYour API key is working correctly. You can now use it in the Docker setup.")
    print("Add it to the .env file or set it as an environment variable when running docker-compose.")
