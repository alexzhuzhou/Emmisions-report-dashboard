"""String processing and normalization utilities."""

import re
import unicodedata


def normalize_text(text: str) -> str:
    """
    Normalize text by standardizing unicode, quotes, dashes, and whitespace.
    
    Args:
        text: Input text to normalize
        
    Returns:
        Normalized text with standardized characters and whitespace
    """
    # Normalize unicode
    text = unicodedata.normalize('NFKC', text)
    # Standardize quotes and dashes
    text = text.replace('"', '"').replace("'", "'")
    text = text.replace('-', '-')
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Strip leading/trailing whitespace
    text = text.strip()
    return text


def safe_filename_for_output_path(name: str) -> str:
    """
    Convert a string to a safe filename by removing/replacing problematic characters.
    
    Args:
        name: Input string to convert to filename
        
    Returns:
        Safe filename string with only alphanumeric, underscore, and dash characters
    """
    name = name.strip().lower()
    name = re.sub(r'\s+', '_', name)
    name = re.sub(r'[^a-z0-9_-]+', '', name)
    name = re.sub(r'[_]+', '_', name)
    name = re.sub(r'[-]+', '-', name)
    return name.strip('_-') 