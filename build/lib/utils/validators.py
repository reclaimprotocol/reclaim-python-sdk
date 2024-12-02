from typing import Dict, Any
import re
from .types import ProofParams, ProofRequest

def is_valid_url(url: str) -> bool:
    """
    Validate if a string is a valid URL
    
    Args:
        url (str): URL to validate
        
    Returns:
        bool: True if URL is valid, False otherwise
    """
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return bool(url_pattern.match(url))

def validate_proof_request(request: Dict[str, Any]) -> bool:
    """
    Validate a proof request object
    
    Args:
        request (Dict): The proof request to validate
        
    Returns:
        bool: True if request is valid, False otherwise
    """
    required_fields = ['callbackUrl', 'provider', 'params']
    
    # Check if all required fields exist
    if not all(field in request for field in required_fields):
        return False
    
    # Validate callback URL
    if not is_valid_url(request['callbackUrl']):
        return False
    
    # Validate provider (should be a non-empty string)
    if not isinstance(request['provider'], str) or not request['provider']:
        return False
    
    # Validate params
    params = request['params']
    if not isinstance(params, dict):
        return False
    
    # If credentials exist in params, it should be a list of strings
    if 'credentials' in params:
        if not isinstance(params['credentials'], list):
            return False
        if not all(isinstance(cred, str) for cred in params['credentials']):
            return False
    
    return True

def validate_proof_callback(headers: Dict[str, str], body: Dict[str, Any]) -> bool:
    """
    Validate a proof callback
    
    Args:
        headers (Dict): Request headers
        body (Dict): Request body
        
    Returns:
        bool: True if callback is valid, False otherwise
    """
    # Check if required header exists
    if 'x-reclaim-auth' not in headers:
        return False
    
    # Validate body structure
    if not isinstance(body, dict) or 'proof' not in body:
        return False
    
    proof = body['proof']
    required_proof_fields = [
        'identifier',
        'provider',
        'params',
        'ownerPublicKey',
        'timestampS',
        'signatures'
    ]
    
    # Check if all required fields exist in proof
    if not all(field in proof for field in required_proof_fields):
        return False
    
    # Validate signatures array
    if not isinstance(proof['signatures'], list):
        return False
    
    return True 