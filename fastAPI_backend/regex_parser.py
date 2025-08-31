import os
import re
from bs4 import BeautifulSoup

def read_input(input_data):
    if input_data.endswith('.txt') and os.path.isfile(input_data):
        with open(input_data, 'r', encoding='utf-8') as f:
            return f.read()
    return input_data

def remove_html_tags(text):
    return BeautifulSoup(text, 'html.parser').get_text(separator=' ', strip=True)

def clean_text(text):
    lines = text.splitlines()
    non_empty = [line.strip() for line in lines if line.strip()]
    return ' '.join(non_empty)

def format_for_openai(text, max_tokens=3500):
    """
    Splits the text into chunks that stay under the token limit.
    Assumes ~4 characters per token.
    Returns a list of text chunks.
    """
    max_chars = max_tokens * 4
    chunks = []

    start = 0
    while start < len(text):
        end = start + max_chars
        # Try to break at the nearest space before the limit for cleaner chunks
        if end < len(text):
            space_index = text.rfind(' ', start, end)
            if space_index > start:
                end = space_index
        chunks.append(text[start:end].strip())
        start = end

    return chunks

def write_output(chunks, output_path):
    """
    If chunks is a list, write each chunk to a separate file with numbered suffixes.
    If it's a single string, write directly to the specified file.
    """
    if isinstance(chunks, list):
        base, ext = os.path.splitext(output_path)
        for i, chunk in enumerate(chunks, 1):
            chunk_path = f"{base}_{i}{ext}"
            with open(chunk_path, 'w', encoding='utf-8') as f:
                f.write(chunk)
        return f"{base}_*.{ext[1:]}"  # wildcard pattern
    else:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(chunks)
        return output_path


def process_input(input_data, output_path=None):
    raw = read_input(input_data)
    stripped_html = remove_html_tags(raw)
    cleaned = clean_text(stripped_html)
    formatted = format_for_openai(cleaned)

    if output_path:
        write_output(formatted, output_path)
        return output_path
    return formatted

# Example usage:
result = process_input('example_input.txt', output_path='clean_output.txt')
print('Output saved to:', result)
