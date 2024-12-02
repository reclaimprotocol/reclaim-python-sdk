import re
import httpx
from eth_account.messages import encode_defunct
from web3 import Web3
import json
import urllib.parse
from typing import Dict, List, Any, Set

from .interfaces import ProviderData, RequestedProof
from .types import SignedClaim, TemplateData
from .constants import BACKEND_BASE_URL, RECLAIM_SHARE_URL
from .validation_utils import validate_url
from .errors import ProofNotVerifiedError
from ..witness import create_sign_data_for_claim, fetch_witness_list_for_claim
import logging
from ..smart_contract import make_beacon

logger = logging.getLogger(__name__)

def generate_requested_proof(provider: ProviderData) -> RequestedProof:
    """
    Generates the requested proof for a given provider
    """
    
    provider_params: Dict[str, str] = {}
    for rs in provider.responseSelections:
        # Using regex to match parameters between {{ }}
        matches = re.findall(r'{{(.*?)}}', rs.responseMatch)
        for match in matches:
            provider_params[match] = ''
            
    proof: RequestedProof = {
        "url": provider.url,
        "parameters": provider_params
    }
        
    return proof

def get_filled_parameters(requested_proof: RequestedProof) -> Dict[str, str]:
    """
    Retrieves the parameters that have been filled with values from the requested proof
    """
    return {
        param: value 
        for param, value in requested_proof["parameters"].items() 
        if value
    }

async def get_shortened_url(url: str) -> str:
    """
    Retrieves a shortened URL for the given URL
    """
    logger.info(f"Attempting to shorten URL: {url}")
    try:
        validate_url(url, 'get_shortened_url')
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BACKEND_BASE_URL}/api/sdk/shortener",
                json={"fullUrl": url},
                headers={"Content-Type": "application/json"}
            )
            res = response.json()
            if response.status_code != 200:
                logger.info(f"Failed to shorten URL: {url}, Response: {json.dumps(res)}")
                return url
            
            shortened_verification_url = res["result"]["shortUrl"]
            return shortened_verification_url
    except Exception as err:
        logger.info(f"Error shortening URL: {url}, Error: {str(err)}")
        return url

async def create_link_with_template_data(template_data: TemplateData) -> str:
    """
    Creates a link with embedded template data
    """
    template = urllib.parse.quote(json.dumps(template_data))
    template = template.replace('(', '%28').replace(')', '%29')
    
    
    full_link = f"{RECLAIM_SHARE_URL}{template}"
    try:
        shortened_link = await get_shortened_url(full_link)
        return shortened_link
    except Exception as err:
        logger.info(f"Error creating link for sessionId: {template_data['sessionId']}, Error: {str(err)}")
        return full_link

async def get_witnesses_for_claim(epoch: int, identifier: str, timestamp_s: int) -> List[str]:
    """
    Retrieves the list of witnesses for a given claim
    """
    try:
        beacon = await make_beacon()
        if not beacon:
            logger.info('No beacon available for getting witnesses')
            raise Exception('No beacon available')
        
        state = await beacon.get_state(epoch)
        witness_list = fetch_witness_list_for_claim(state, identifier, timestamp_s)
        witnesses = [w.id.lower() for w in witness_list]
        return witnesses
    except Exception as err:
        logger.info(f'Error getting witnesses for claim: {str(err)}')
        raise Exception(f'Error getting witnesses for claim: {str(err)}')

def recover_signers_of_signed_claim(claim: SignedClaim) -> List[str]:
    """
    Recovers the signers' addresses from a signed claim
    """
    data_str = create_sign_data_for_claim(claim.claim)
    w3 = Web3()
    
    signers = []
    for signature in claim.signatures:
        message = encode_defunct(text=data_str)
        signer = w3.eth.account.recover_message(message, signature=signature)
        signers.append(signer.lower())
    
    return signers

def assert_valid_signed_claim(claim: SignedClaim, expected_witness_addresses: List[str]) -> None:
    """
    Asserts that a signed claim is valid by checking if all expected witnesses have signed
    """
    witness_addresses = recover_signers_of_signed_claim(claim)
    witnesses_not_seen: Set[str] = set(expected_witness_addresses)
    
    for witness in witness_addresses:
        if witness in witnesses_not_seen:
            witnesses_not_seen.remove(witness)
    
    if witnesses_not_seen:
        missing_witnesses = ", ".join(witnesses_not_seen)
        logger.info(f"Claim validation failed. Missing signatures from: {missing_witnesses}")
        raise ProofNotVerifiedError(f"Missing signatures from {missing_witnesses}")
