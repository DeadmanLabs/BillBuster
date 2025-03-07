"""
Document chunking functionality for handling large legislative documents.
"""

import os
from typing import List, Dict, Optional, Union
import PyPDF2
from langchain.text_splitter import RecursiveCharacterTextSplitter


class DocumentChunker:
    """
    Handles splitting large documents into manageable chunks for processing by LLMs.
    Supports both text and PDF files.
    """
    
    def __init__(self, 
                 chunk_size: int = 4000, 
                 chunk_overlap: int = 500):
        """
        Initialize the document chunker.
        
        Args:
            chunk_size: Maximum size of each chunk in characters
            chunk_overlap: Number of characters of overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def read_file(self, file_path: str) -> str:
        """
        Read a file (text or PDF) and return its content as text.
        
        Args:
            file_path: Path to the file to read
            
        Returns:
            The text content of the file
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.pdf':
            return self._read_pdf(file_path)
        else:
            # Assume it's a text file
            return self._read_text(file_path)
    
    def _read_pdf(self, file_path: str) -> str:
        """
        Read a PDF file and extract its text content.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            The text content of the PDF
        """
        text = ""
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for i, page in enumerate(reader.pages):
                # Extract text and add page marker
                page_text = page.extract_text()
                page_marker = f"\n\n[PAGE {i+1}]\n\n"
                text += page_marker + page_text
        return text
    
    def _read_text(self, file_path: str) -> str:
        """
        Read a text file.
        
        Args:
            file_path: Path to the text file
            
        Returns:
            The content of the text file
        """
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    
    def chunk_document(self, content: str) -> List[str]:
        """
        Split the document content into manageable chunks.
        
        Args:
            content: The document content as a string
            
        Returns:
            A list of document chunks
        """
        return self.text_splitter.split_text(content)
    
    def process_file(self, file_path: str) -> List[str]:
        """
        Read a file and split it into chunks.
        
        Args:
            file_path: Path to the file to process
            
        Returns:
            A list of document chunks
        """
        content = self.read_file(file_path)
        return self.chunk_document(content)