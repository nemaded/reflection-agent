from typing import List, Dict, Any
from collections import deque
import json

def build_prompt_structure(prompt: str, role: str) -> Dict[str, str]:
    """
    Builds a structured prompt for the LLM.
    
    Args:
        prompt (str): The actual prompt text
        role (str): The role of the message (system, user, or assistant)
        
    Returns:
        Dict[str, str]: A dictionary containing the role and content
    """
    return {
        "role": role,
        "content": prompt
    }

def completions_create(client: Any, history: List[Dict[str, str]], model: str) -> str:
    """
    Creates a completion using the provided client and history.
    
    Args:
        client: The LLM client (e.g., Groq client)
        history (List[Dict[str, str]]): The conversation history
        model (str): The model to use for completion
        
    Returns:
        str: The generated response
    """
    try:
        # Handle FixedFirstChatHistory objects
        if hasattr(history, 'get_messages'):
            messages = history.get_messages()
        else:
            messages = history
            
        # Updated for Groq 0.4.0 compatibility
        response = client.chat.completions.create(
            messages=messages,
            model=model,
            temperature=0.7,
            max_tokens=1000,
            # Remove any parameters that might cause issues
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error in completions_create: {str(e)}")
        # Try alternative approach if the first fails
        try:
            # Some versions might use different parameter formats
            if hasattr(history, 'get_messages'):
                messages = history.get_messages()
            else:
                messages = history
                
            response = client.chat.completions.create(
                messages=messages,
                model=model,
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as nested_e:
            print(f"Alternative approach also failed: {str(nested_e)}")
            raise

class FixedFirstChatHistory:
    """
    A class that maintains a fixed-length chat history while preserving the first message.
    The first message is typically the system prompt that should always be present.
    """
    
    def __init__(self, initial_messages: List[Dict[str, str]], total_length: int = 3):
        """
        Initialize the chat history.
        
        Args:
            initial_messages (List[Dict[str, str]]): Initial messages to add to the history
            total_length (int): Maximum number of messages to keep (including the first message)
        """
        self.total_length = total_length
        self.fixed_messages = list(initial_messages)  # Store fixed messages separately
        self.messages = list(initial_messages)  # Create a copy
    
    def append(self, message: Dict[str, str]) -> None:
        """
        Append a message to the history while maintaining the fixed length.
        The first N fixed messages are always preserved.
        
        Args:
            message (Dict[str, str]): The message to append
        """
        self.messages.append(message)
        
        # If we have more messages than the total_length, trim while preserving fixed messages
        if len(self.messages) > self.total_length:
            # Keep fixed messages and most recent ones up to total_length
            fixed_count = len(self.fixed_messages)
            self.messages = self.fixed_messages + self.messages[-(self.total_length - fixed_count):]
    
    def get_messages(self) -> List[Dict[str, str]]:
        """
        Get the current chat history as simple dictionaries.
        
        Returns:
            List[Dict[str, str]]: The current chat history as simple dictionaries
        """
        # Return a list of simple dictionaries to ensure JSON serializability
        return [{"role": msg["role"], "content": msg["content"]} for msg in self.messages]
        
    def __str__(self):
        """String representation for debugging"""
        return f"FixedFirstChatHistory(msgs={len(self.messages)}, fixed={len(self.fixed_messages)}, max={self.total_length})"
    
    def __iter__(self):
        """Make iterable for compatibility"""
        return iter(self.get_messages())
        
    def toJSON(self):
        """Make the object JSON serializable"""
        return self.get_messages()

def update_chat_history(history: FixedFirstChatHistory, content: str, role: str) -> None:
    """
    Updates the chat history with a new message.
    
    Args:
        history (FixedFirstChatHistory): The chat history to update
        content (str): The content of the new message
        role (str): The role of the message (system, user, or assistant)
    """
    message = build_prompt_structure(content, role)
    history.append(message) 