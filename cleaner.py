import json


def parse_llm_json_response(raw_response):
    """
    Parse JSON from an LLM response that might contain Markdown code block formatting.
    
    Args:
        raw_response (str): The raw text response from the LLM. Must be a string,
                           not an already parsed dictionary.
        
    Returns:
        dict: The parsed JSON data
        
    Raises:
        ValueError: If the response cannot be parsed as valid JSON
        TypeError: If the input is not a string
    """
    # Check that we're working with a string, not an already parsed dict
    if not isinstance(raw_response, (str, bytes, bytearray)):
        raise TypeError("Input must be a string (str, bytes, or bytearray), not %s" % type(raw_response).__name__)
    # Clean the response by removing whitespace
    cleaned_response = raw_response.strip()
    
    # Remove markdown code blocks if present (```json ... ```)
    if cleaned_response.startswith("```"):
        # Find the end of the code block
        end_marker_pos = cleaned_response.rfind("```")
        if end_marker_pos > 3:  # Make sure we're not just removing the first marker
            # Extract content between the markers
            # Skip the first line if it contains the language identifier (```json)
            first_newline = cleaned_response.find("\n")
            if first_newline > 0:
                cleaned_response = cleaned_response[first_newline+1:end_marker_pos].strip()
            else:
                cleaned_response = cleaned_response[3:end_marker_pos].strip()
        else:
            # Just remove the starting marker if no ending marker is found
            first_newline = cleaned_response.find("\n")
            if first_newline > 0:
                cleaned_response = cleaned_response[first_newline+1:].strip()
            else:
                cleaned_response = cleaned_response[3:].strip()
    
    # Try to parse the cleaned response as JSON
    try:
        return json.loads(cleaned_response)
    except json.JSONDecodeError as e:
        # If it still fails, try to extract any JSON-like content using regex
        import re
        json_matches = re.findall(r'\{.*?\}', cleaned_response, re.DOTALL)
        
        if json_matches:
            # Try each potential JSON match
            for potential_json in json_matches:
                try:
                    return json.loads(potential_json)
                except json.JSONDecodeError:
                    continue
                
        # If all attempts fail, raise a ValueError with the original error
        raise ValueError(f"Failed to parse LLM response as JSON: {str(e)}")