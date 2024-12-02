import json
from json_canonical import canonicalize
from sha3 import keccak_256
from eth_account.messages import encode_defunct
from web3 import Web3
from eth_utils import to_checksum_address
from typing import Any, Dict, List, Optional, TypedDict
from .logger import logger
from .errors import InvalidParamError, InvalidSignatureError

class ParamValidation(TypedDict):
    input: Any
    param_name: str
    is_string: bool

def validate_function_params(params: List[ParamValidation], function_name: str) -> None:
    for param in params:
        if param['input'] is None:
            logger.info(f"Validation failed: {param['param_name']} in {function_name} is null or undefined")
            raise InvalidParamError(f"{param['param_name']} passed to {function_name} must not be null or undefined.")
        
        if param.get('is_string', False):
            if not isinstance(param['input'], str):
                logger.info(f"Validation failed: {param['param_name']} in {function_name} is not a string")
                raise InvalidParamError(f"{param['param_name']} passed to {function_name} must be a string.")
            
            if not param['input'].strip():
                logger.info(f"Validation failed: {param['param_name']} in {function_name} is an empty string")
                raise InvalidParamError(f"{param['param_name']} passed to {function_name} must not be an empty string.")

def validate_url(url: str, function_name: str) -> None:
    from urllib.parse import urlparse
    try:
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            raise ValueError("Invalid URL format")
    except Exception as e:
        logger.info(f"URL validation failed for {url} in {function_name}: {str(e)}")
        raise InvalidParamError(f"Invalid URL format {url} passed to {function_name}.", e)

def validate_signature(provider_id: str, signature: str, application_id: str, timestamp: str) -> None:
    try:
        logger.info(f"Starting signature validation for providerId: {provider_id}, applicationId: {application_id}, timestamp: {timestamp}")
        canonical_data = canonicalize(
                {
                    "providerId": provider_id,
                    "timestamp": timestamp,
                }
            )

        message_hash = keccak_256(canonical_data).hexdigest()
        message_hash_bytes = bytes.fromhex(message_hash)
       
        w3 = Web3()
        
        # Create the message hash
        message = encode_defunct(message_hash_bytes)
        
        # Recover the address from the signature
        recovered_address = w3.eth.account.recover_message(message, signature=signature)
        recovered_address = recovered_address.lower()
        
        if to_checksum_address(recovered_address) != to_checksum_address(application_id):
            logger.info(f"Signature validation failed: Mismatch between derived appId ({recovered_address}) and provided applicationId ({application_id})")
            raise InvalidSignatureError(f"Signature does not match the application id: {recovered_address}")
        
        logger.info(f"Signature validated successfully for applicationId: {application_id}")
    
    except Exception as err:
        logger.info(f"Signature validation failed: {str(err)}")
        raise InvalidSignatureError(f"Failed to validate signature: {str(err)}")

def validate_requested_proof(requested_proof: Dict[str, Any]) -> None:
    logger.info(f"Validating requested proof: {requested_proof}")
    
    if not requested_proof.get('url'):
        logger.info("Requested proof validation failed: Provided url in requested proof is not valid")
        raise InvalidParamError("The provided url in requested proof is not valid")
    
    if not isinstance(requested_proof.get('parameters'), dict):
        logger.info("Requested proof validation failed: Provided parameters in requested proof is not valid")
        raise InvalidParamError("The provided parameters in requested proof is not valid")

def validate_context(context: Dict[str, Any]) -> None:
    if not context.get('contextAddress'):
        logger.info("Context validation failed: Provided context address in context is not valid")
        raise InvalidParamError("The provided context address in context is not valid")
    
    if not context.get('contextMessage'):
        logger.info("Context validation failed: Provided context message in context is not valid")
        raise InvalidParamError("The provided context message in context is not valid")
    
    validate_function_params([
        {
            'input': context.get('contextAddress'),
            'param_name': 'contextAddress',
            'is_string': True
        },
        {
            'input': context.get('contextMessage'),
            'param_name': 'contextMessage',
            'is_string': True
        }
    ], 'validateContext')

def validate_options(options: Dict[str, Any]) -> None:
    if 'acceptAiProviders' in options and not isinstance(options['acceptAiProviders'], bool):
        logger.info("Options validation failed: Provided acceptAiProviders in options is not valid")
        raise InvalidParamError("The provided acceptAiProviders in options is not valid")
    
    if 'log' in options and not isinstance(options['log'], bool):
        logger.info("Options validation failed: Provided log in options is not valid")
        raise InvalidParamError("The provided log in options is not valid")
