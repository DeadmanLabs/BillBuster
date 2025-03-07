"""
Example usage of the BillBuster Compressor library.
"""

import os
import json
from dotenv import load_dotenv
from compressor import DocumentProcessor

# Load environment variables
load_dotenv()

def process_bill_example():
    """
    Example function demonstrating how to process a legislative document.
    """
    # Get OpenAI API key from environment
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    
    # File path to a legislative document (PDF or text)
    bill_path = os.getenv('BILL_PATH', 'path/to/your/bill.pdf')
    if not os.path.exists(bill_path):
        raise FileNotFoundError(f"Bill file not found: {bill_path}")
    
    # Initialize the document processor
    processor = DocumentProcessor(
        openai_api_key=openai_api_key,
        model_name="gpt-4-turbo",  # Can use gpt-3.5-turbo for lower cost but less accuracy
        chunk_size=4000,
        chunk_overlap=500,
        memory_size=5,
        queue_size=1000
    )
    
    print(f"Processing bill: {bill_path}")
    
    # Process the document
    result, stats = processor.process_document(bill_path)
    
    points = result["points"]
    summary = result["summary"]
    tags = result["tags"]
    
    print(f"Processing complete. Extracted {len(points)} points.")
    print(f"Stats: {json.dumps(stats, indent=2)}")
    
    # Save points to a JSON file
    output_path = bill_path + '.results.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    
    print(f"Results saved to: {output_path}")
    
    # Print summary and tags
    print("\nSUMMARY:")
    print(summary)
    
    print("\nTAGS:")
    print(", ".join(tags))
    
    # Print a few example points
    print("\nExample points:")
    for i, point in enumerate(points[:3]):
        print(f"\nPoint {i+1}:")
        print(f"Type: {point['point_type']}")
        print(f"Description: {point['description']}")
        print(f"Citation: {point.get('citation', 'N/A')[:100]}...")
        print(f"Page: {point.get('page_number', 'N/A')}")
        print(f"Confidence: {point['confidence']}")
        if point.get('reference'):
            print(f"Reference: {point['reference']}")

if __name__ == "__main__":
    process_bill_example()