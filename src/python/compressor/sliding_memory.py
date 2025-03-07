"""
Sliding memory window to maintain context across document chunks.
"""

from typing import List, Dict, Optional, Deque
from collections import deque


class SlidingMemory:
    """
    Maintains a sliding window of context memory for processing large documents.
    This helps maintain continuity when analyzing documents that span multiple chunks.
    """
    
    def __init__(self, 
                 max_items: int = 5, 
                 max_summary_length: int = 1000):
        """
        Initialize the sliding memory window.
        
        Args:
            max_items: Maximum number of items to keep in memory
            max_summary_length: Maximum length of the summary in characters
        """
        self.max_items = max_items
        self.max_summary_length = max_summary_length
        self.memory: Deque[str] = deque(maxlen=max_items)
        self.summary = ""
        self.entities = {}  # Track important entities and concepts
        self.key_points = []  # List of key points identified so far
    
    def add_chunk_context(self, context: str):
        """
        Add a new chunk's context to the memory window.
        
        Args:
            context: The context information extracted from a chunk
        """
        self.memory.append(context)
    
    def update_summary(self, new_summary: str):
        """
        Update the running summary with new information.
        
        Args:
            new_summary: New summary information to incorporate
        """
        # Simple concatenation with length limit
        if len(self.summary) + len(new_summary) > self.max_summary_length:
            # If we would exceed the max length, truncate the beginning of the summary
            truncate_length = len(self.summary) + len(new_summary) - self.max_summary_length
            self.summary = self.summary[truncate_length:] + new_summary
        else:
            self.summary += " " + new_summary
        
        self.summary = self.summary.strip()
    
    def add_entities(self, new_entities: Dict[str, str]):
        """
        Add new entities to the tracked entities map.
        
        Args:
            new_entities: Dictionary of entity names to descriptions
        """
        self.entities.update(new_entities)
    
    def add_key_point(self, point: str):
        """
        Add a key point from the document.
        
        Args:
            point: The key point to add
        """
        if point not in self.key_points:
            self.key_points.append(point)
    
    def get_context(self) -> str:
        """
        Get the current context to provide to the LLM.
        
        Returns:
            A string containing the current context
        """
        memory_text = "\n".join(list(self.memory))
        
        context = f"DOCUMENT SUMMARY SO FAR:\n{self.summary}\n\n"
        
        if len(self.entities) > 0:
            context += "IMPORTANT ENTITIES AND CONCEPTS:\n"
            for entity, description in self.entities.items():
                context += f"- {entity}: {description}\n"
            context += "\n"
        
        if len(self.key_points) > 0:
            context += "KEY POINTS IDENTIFIED SO FAR:\n"
            for point in self.key_points:
                context += f"- {point}\n"
            context += "\n"
        
        context += "RECENT CONTEXT:\n" + memory_text
        
        return context
    
    def get_key_points(self) -> List[str]:
        """
        Get the list of key points identified in the document.
        
        Returns:
            The list of key points
        """
        return self.key_points
    
    def clear(self):
        """
        Clear the memory.
        """
        self.memory.clear()
        self.summary = ""
        self.entities = {}
        self.key_points = []