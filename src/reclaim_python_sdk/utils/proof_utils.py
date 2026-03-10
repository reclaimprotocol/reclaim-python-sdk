import httpx
from eth_account.messages import encode_defunct
from web3 import Web3
import json
import urllib.parse
from typing import List, Set
from .types import SignedClaim, TemplateData
from .constants import BACKEND_BASE_URL, RECLAIM_SHARE_URL
from .validation_utils import validate_url
from .errors import ProofNotVerifiedError
from ..witness import create_sign_data_for_claim, fetch_witness_list_for_claim
import logging
from ..smart_contract import make_beacon

logger = logging.getLogger(__name__)

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

async def get_attestors() -> List[str]:
    """
    Retrieves the list of witnesses (attestors) from the backend
    """
    from .constants import DEFAULT_ATTESTORS_URL
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(DEFAULT_ATTESTORS_URL)
            if response.status_code != 200:
                response.read()
                raise Exception(f"Failed to fetch witness addresses: {response.status_code}")
            
            res_data = response.json()
            # The JS SDK expects data: { address: string }[] but handles res.data
            address_list = res_data.get("data", [])
            witnesses = [w["address"].lower() for w in address_list if "address" in w]
            return witnesses
    except Exception as err:
        logger.info(f'Error getting attestors: {str(err)}')
        raise Exception(f'Error getting attestors: {str(err)}')

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
    Asserts that a signed claim is valid by checking if at least one expected witness has signed
    """
    witness_addresses = recover_signers_of_signed_claim(claim)
    
    # ensure at least one signer is an attestor
    is_valid = any(signer in expected_witness_addresses for signer in witness_addresses)
    
    if not is_valid:
        logger.info("Claim validation failed. Identifier mismatch or no signature from expected witnesses.")
        raise ProofNotVerifiedError("Identifier mismatch")
