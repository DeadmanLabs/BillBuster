"""
LLM-based point extraction from legislative documents.
"""

import json
from typing import List, Dict, Any, Optional, Tuple
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage


class PointExtractor:
    """
    Uses LLM to extract key points from legislative document chunks.
    """
    
    def __init__(self, 
                 api_key: str,
                 model_name: str = "gpt-4-turbo",
                 temperature: float = 0.1):
        """
        Initialize the point extractor.
        
        Args:
            api_key: OpenAI API key
            model_name: Name of the LLM model to use
            temperature: Temperature for the model (lower is more deterministic)
        """
        self.model_name = model_name
        self.temperature = temperature
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            openai_api_key=api_key
        )
        
        # System prompt for the LLM
        self.system_prompt = """
        You are an expert legislative analyst tasked with extracting key points from bills and legislative documents.
        Your job is to identify specific actions, changes, or provisions in the legislation.
        
        For each chunk of text, identify the key legislative points with the following focus:
        1. Funding allocations or appropriations
        2. Changes to existing laws or regulations
        3. New classifications, definitions, or legal categories
        4. Requirements imposed on entities (people, businesses, agencies)
        5. Permissions granted or restrictions imposed
        6. Deadlines, timelines, or effective dates
        7. Penalties or enforcement mechanisms
        
        Each point should be specific, concrete, and directly supported by the text. Do not make interpretations beyond what is explicitly stated.
        Always note section numbers or references when mentioned.
        
        Format each point as a JSON object with the following fields:
        - "point_type": One of ["funding", "change", "classification", "requirement", "permission", "timeline", "penalty", "other"]
        - "description": A clear, concise description of the point
        - "entities": List of entities affected by this point
        - "reference": Section number or other reference if available
        - "citation": The exact text from the document that supports this point (direct quote)
        - "page_number": The page number where this point appears, if available
        - "confidence": Your confidence in this extraction (high, medium, low)
        
        Return a list of these points in JSON format.
        """
    
    def extract_points_from_chunk(self, 
                                chunk_text: str, 
                                memory_context: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Extract key points from a document chunk using the LLM.
        
        Args:
            chunk_text: The text chunk to analyze
            memory_context: Optional context from previous chunks
            
        Returns:
            A list of extracted points as dictionaries
        """
        # Prepare the prompt
        if memory_context:
            prompt = f"""
            CONTEXT FROM PREVIOUS SECTIONS:
            {memory_context}
            
            CURRENT SECTION TO ANALYZE:
            {chunk_text}
            
            Based on both the context and the current section, extract the key legislative points as described in your instructions.
            Only extract new points from the current section, but use the context to better understand them.
            Return the points as a JSON list.
            """
        else:
            prompt = f"""
            SECTION TO ANALYZE:
            {chunk_text}
            
            Extract the key legislative points as described in your instructions.
            Return the points as a JSON list.
            """
        
        # Create the messages
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt)
        ]
        
        # Get response from LLM
        response = self.llm.invoke(messages)
        
        # Parse the response
        try:
            # Try to extract JSON from the response
            response_text = response.content
            # Sometimes the model wraps the JSON in markdown code blocks
            if "```json" in response_text:
                # Extract the JSON part
                json_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                # Just extract from the code block
                json_text = response_text.split("```")[1].split("```")[0].strip()
            else:
                # Assume the entire response is JSON
                json_text = response_text
                
            points = json.loads(json_text)
            return points
        except Exception as e:
            # If JSON parsing fails, return an error point
            print(f"Error parsing LLM response: {e}")
            print(f"Response was: {response.content}")
            return [{
                "point_type": "error",
                "description": "Failed to parse points from LLM response",
                "entities": [],
                "reference": "",
                "confidence": "low"
            }]
    
    def summarize_points(self, points: List[Dict[str, Any]]) -> str:
        """
        Generate a summary of the extracted points.
        
        Args:
            points: List of extracted points
            
        Returns:
            A summary string
        """
        # Use the LLM to generate a summary
        if not points:
            return "No points extracted."
            
        points_text = json.dumps(points, indent=2)
        
        prompt = f"""
        Here is a list of legislative points extracted from a document:
        {points_text}
        
        Please provide a brief summary of these points, focusing on the most important aspects.
        Keep the summary concise (3-5 sentences).
        """
        
        messages = [
            SystemMessage(content="You are an expert legislative analyst providing concise summaries."),
            HumanMessage(content=prompt)
        ]
        
        response = self.llm.invoke(messages)
        
        return response.content.strip()
        
    def generate_tags(self, points: List[Dict[str, Any]]) -> List[str]:
        """
        Generate tags/keywords based on the extracted points.
        
        Args:
            points: List of extracted points
            
        Returns:
            A list of relevant tags
        """
        if not points:
            return []
            
        points_text = json.dumps(points, indent=2)
        
        prompt = f"""
        Here is a list of legislative points extracted from a document:
        {points_text}
        
        Please generate 5-10 relevant tags or keywords that best represent the subject matter and content of this legislation.
        Focus on specific topics, policy areas, affected sectors, and key themes.
        
        Return the tags as a JSON array of strings. Each tag should be a single word or short phrase (1-3 words).
        """
        
        messages = [
            SystemMessage(content="You are an expert legislative analyst identifying key topics and themes."),
            HumanMessage(content=prompt)
        ]
        
        response = self.llm.invoke(messages)
        
        # Parse the response to extract tags
        try:
            response_text = response.content
            
            # Try to extract JSON
            if "```json" in response_text:
                json_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_text = response_text.split("```")[1].split("```")[0].strip()
            else:
                json_text = response_text
                
            # Clean up the text to ensure it's valid JSON
            if json_text.startswith('[') and json_text.endswith(']'):
                tags = json.loads(json_text)
                return tags
            else:
                # If not a valid JSON array, try manual parsing
                if '[' in json_text and ']' in json_text:
                    array_content = json_text[json_text.find('[')+1:json_text.rfind(']')]
                    items = array_content.split(',')
                    tags = [item.strip().strip('"\'') for item in items if item.strip()]
                    return tags
        except Exception as e:
            print(f"Error parsing tags: {e}")
        
        # Fallback: simple text splitting
        # Split by commas, newlines, or other separators
        fallback_tags = response.content.replace('[', '').replace(']', '').split(',')
        fallback_tags = [tag.strip().strip('"\'') for tag in fallback_tags if tag.strip()]
        
        return fallback_tags
        
    def generate_full_summary(self, all_points: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a comprehensive summary and tags for the entire document.
        
        Args:
            all_points: All points extracted from the document
            
        Returns:
            Dictionary with summary and tags
        """
        if not all_points:
            return {
                "summary": ["No points extracted from the document."],
                "tags": []
            }
            
        # For large numbers of points, we'll summarize in batches and then combine
        batches = [all_points[i:i+20] for i in range(0, len(all_points), 20)]
        batch_summaries = []
        
        for batch in batches:
            batch_summary = self.summarize_points(batch)
            batch_summaries.append(batch_summary)
        
        # Generate final summary
        if len(batch_summaries) > 1:
            # If we have multiple batches, summarize them
            summaries_text = "\n".join(batch_summaries)
            prompt = f"""
            Here are summaries of different sections of a legislative document:
            {summaries_text}
            
            Please provide a comprehensive but concise summary of the entire document based on these section summaries.
            The summary should be 3-5 paragraphs and cover the main provisions and purpose of the legislation.
            Format your response as a single cohesive summary with multiple paragraphs.
            """
            
            messages = [
                SystemMessage(content="You are an expert legislative analyst providing comprehensive document summaries."),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            summary_text = response.content.strip()
                
        else:
            # If just one batch, use its summary directly
            summary_text = batch_summaries[0].strip()
        
        # Generate tags from all points
        tags = self.generate_tags(all_points)
        
        return {
            "summary": summary_text,
            "tags": tags
        }