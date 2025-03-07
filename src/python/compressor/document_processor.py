"""
Main document processing functionality that integrates all components.
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple, Union
from .document_chunker import DocumentChunker
from .point_extractor import PointExtractor
from .sliding_memory import SlidingMemory
from .queue_manager import QueueManager


class DocumentProcessor:
    """
    Main class that orchestrates the processing of legislative documents:
    1. Chunks documents into manageable pieces
    2. Extracts key points from each chunk using LLMs
    3. Maintains context across chunks with sliding memory
    4. Pushes extracted points to a queue for further processing
    """
    
    def __init__(self, 
                 openai_api_key: str,
                 model_name: str = "gpt-4-turbo",
                 chunk_size: int = 4000,
                 chunk_overlap: int = 500,
                 memory_size: int = 5,
                 queue_size: int = 1000,
                 log_level: int = logging.INFO):
        """
        Initialize the document processor.
        
        Args:
            openai_api_key: OpenAI API key for LLM access
            model_name: Name of the LLM model to use
            chunk_size: Size of document chunks
            chunk_overlap: Overlap between chunks
            memory_size: Number of previous chunks to keep in memory
            queue_size: Maximum size of the points queue
            log_level: Logging level
        """
        # Configure logging
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("DocumentProcessor")
        
        # Initialize components
        self.chunker = DocumentChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self.extractor = PointExtractor(api_key=openai_api_key, model_name=model_name)
        self.memory = SlidingMemory(max_items=memory_size)
        self.queue = QueueManager(max_queue_size=queue_size)
        
        # Track processing stats
        self.stats = {
            "total_chunks": 0,
            "processed_chunks": 0,
            "total_points": 0,
            "processing_errors": 0
        }
        
        self.logger.info(f"Document processor initialized with model {model_name}")
    
    def process_document(self, file_path: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Process a legislative document and extract key points.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            A tuple of (result dictionary with points, summary, and tags, processing statistics)
        """
        self.logger.info(f"Starting to process document: {file_path}")
        
        # Reset state for new document
        self.memory.clear()
        self.queue.clear()
        self.stats = {
            "total_chunks": 0,
            "processed_chunks": 0,
            "total_points": 0,
            "processing_errors": 0
        }
        
        # Check if file exists
        if not os.path.exists(file_path):
            self.logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Chunk the document
        try:
            chunks = self.chunker.process_file(file_path)
            self.stats["total_chunks"] = len(chunks)
            self.logger.info(f"Document split into {len(chunks)} chunks")
        except Exception as e:
            self.logger.error(f"Error chunking document: {str(e)}")
            raise
        
        # Process each chunk
        all_points = []
        for i, chunk in enumerate(chunks):
            self.logger.info(f"Processing chunk {i+1}/{len(chunks)}")
            
            try:
                # Get context from memory
                memory_context = self.memory.get_context() if i > 0 else None
                
                # Extract points from the chunk
                points = self.extractor.extract_points_from_chunk(chunk, memory_context)
                
                # Update stats
                self.stats["processed_chunks"] += 1
                self.stats["total_points"] += len(points)
                
                # Update memory with new points and context
                for point in points:
                    if point["point_type"] != "error":
                        self.memory.add_key_point(point["description"])
                
                # Generate a summary of this chunk
                chunk_summary = self.extractor.summarize_points(points)
                self.memory.update_summary(chunk_summary)
                
                # Add chunk to memory
                self.memory.add_chunk_context(chunk[:500])  # Add first 500 chars as context
                
                # Add points to the queue and collection
                for point in points:
                    # Add document metadata to each point
                    point["document_path"] = file_path
                    point["chunk_index"] = i
                    point["document_name"] = os.path.basename(file_path)
                    
                    # Add to queue and collection
                    self.queue.add_point(point)
                    all_points.append(point)
                
                self.logger.info(f"Extracted {len(points)} points from chunk {i+1}")
                
            except Exception as e:
                self.logger.error(f"Error processing chunk {i+1}: {str(e)}")
                self.stats["processing_errors"] += 1
        
        # Mark processing as complete
        self.queue.mark_complete()
        self.logger.info(f"Document processing complete. Total points: {self.stats['total_points']}")
        
        # Generate comprehensive summary and tags
        self.logger.info("Generating document summary and tags")
        summary_result = self.extractor.generate_full_summary(all_points)
        
        # Return the final result
        result = {
            "points": all_points,
            "summary": summary_result["summary"],
            "tags": summary_result["tags"]
        }
        
        self.logger.info(f"Generated summary with {len(summary_result['summary'])} paragraphs and {len(summary_result['tags'])} tags")
        
        return result, self.stats
    
    def get_all_points(self) -> List[Dict[str, Any]]:
        """
        Get all points extracted from the document.
        
        Returns:
            List of all extracted points
        """
        # Export all points from the queue to a list
        points = []
        while not self.queue.is_empty():
            point = self.queue.get_point(timeout=0.1)
            if point:
                points.append(point)
        
        return points
    
    def save_points_to_file(self, file_path: str) -> int:
        """
        Save all points to a JSON file.
        
        Args:
            file_path: Path to save the JSON file
            
        Returns:
            Number of points saved
        """
        points = self.queue.export_points_to_json(file_path)
        self.logger.info(f"Saved {len(points)} points to {file_path}")
        return len(points)