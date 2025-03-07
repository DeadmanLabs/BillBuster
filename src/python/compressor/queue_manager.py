"""
Queue management for handling extracted points from documents.
"""

import json
import queue
from typing import List, Dict, Any, Optional
import threading


class QueueManager:
    """
    Manages queues for storing and retrieving extracted points from legislative documents.
    Supports thread-safe operations for concurrent processing.
    """
    
    def __init__(self, max_queue_size: int = 1000):
        """
        Initialize the queue manager.
        
        Args:
            max_queue_size: Maximum size of the queue
        """
        self.points_queue = queue.Queue(maxsize=max_queue_size)
        self.lock = threading.Lock()
        self.processing_complete = False
    
    def add_point(self, point: Dict[str, Any]):
        """
        Add a point to the queue.
        
        Args:
            point: Dictionary containing point data
        """
        try:
            self.points_queue.put(point, block=False)
        except queue.Full:
            # Handle the queue being full
            # For now, just log it, but could implement more sophisticated handling
            print("Warning: Points queue is full. Point not added.")
    
    def add_points(self, points: List[Dict[str, Any]]):
        """
        Add multiple points to the queue.
        
        Args:
            points: List of dictionaries containing point data
        """
        with self.lock:
            for point in points:
                self.add_point(point)
    
    def get_point(self, timeout: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """
        Get a point from the queue.
        
        Args:
            timeout: How long to wait for a point (None means wait indefinitely)
            
        Returns:
            A point dictionary or None if the queue is empty and processing is complete
        """
        try:
            return self.points_queue.get(block=True, timeout=timeout)
        except queue.Empty:
            if self.processing_complete:
                return None
            return None
    
    def mark_complete(self):
        """
        Mark processing as complete.
        """
        self.processing_complete = True
    
    def is_empty(self) -> bool:
        """
        Check if the queue is empty.
        
        Returns:
            True if the queue is empty, False otherwise
        """
        return self.points_queue.empty()
    
    def size(self) -> int:
        """
        Get the current size of the queue.
        
        Returns:
            Current number of items in the queue
        """
        return self.points_queue.qsize()
    
    def clear(self):
        """
        Clear the queue.
        """
        with self.lock:
            while not self.points_queue.empty():
                try:
                    self.points_queue.get_nowait()
                except queue.Empty:
                    break
            self.processing_complete = False
    
    def export_points_to_json(self, file_path: str):
        """
        Export all points in the queue to a JSON file.
        Note: This empties the queue.
        
        Args:
            file_path: Path to save the JSON file
        """
        points = []
        with self.lock:
            while not self.points_queue.empty():
                try:
                    point = self.points_queue.get_nowait()
                    points.append(point)
                except queue.Empty:
                    break
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(points, f, indent=2)
            
        return points