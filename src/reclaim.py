import json
import time
from typing import Dict, List, Optional, Any, Union
from eth_account import Account
from eth_account.messages import encode_defunct
from web3 import Web3
import canonicaljson
from .utils.interfaces import Proof, Context, ProviderClaimData, ProviderData, RequestedProof
from .utils.types import (
    ClaimInfo,
    SignedClaim
)
from .utils.errors import (
    InitError,
    InvalidParamError,
    ProviderNotFoundError,
    SessionNotStartedError,
    BuildProofRequestError,
    SignatureNotFoundError,
    UpdateSessionError,
    InitSessionError,
    GetStatusUrlError,
    GetRequestUrlError,
    BackendServerError,
    NoProviderParamsError,
    SetParamsError,
    AddContextError,
    ProofNotVerifiedError
)
from .utils.proof_utils import (
    assert_valid_signed_claim,
    get_witnesses_for_claim
)

from .witness import get_identifier_from_claim_info

from .utils.logger import Logger

logger = Logger()

async def verify_proof(proof: Proof) -> bool:
    """
    Verify a proof by checking signatures and witness data
    
    Args:
        proof (Proof): The proof object to verify
        
    Returns:
        bool: True if proof is valid, False otherwise
        
    Raises:
        SignatureNotFoundError: If no signatures are present in the proof
    """
    if not proof.signatures:
        raise SignatureNotFoundError('No signatures')

    try:
        # Check if witness array exists and first element is manual-verify
        witnesses = []
        if proof.witnesses and proof.witnesses[0].get('url') == 'manual-verify':
            witnesses.append(proof.witnesses[0]['id'])
        else:
            witnesses = await get_witnesses_for_claim(
                proof.claimData.epoch,
                proof.identifier,
                proof.claimData.timestampS
            )

        claim_data = ClaimInfo(
            # canonicalize claim data parameters without adding b'' to the string and dont add escape characters
            parameters=proof.claimData.parameters,
            provider=proof.claimData.provider,
            context=proof.claimData.context
        )
        
        # Use JSON canonicalization instead of the canonicalize module
        calculated_identifier = get_identifier_from_claim_info(claim_data)

        # Remove quotes from identifier for comparison
        proof.identifier = proof.identifier.replace('"', '')

        # Check if identifiers match
        if calculated_identifier != proof.identifier:
            raise ProofNotVerifiedError('Identifier Mismatch')


        claim_data: ProviderClaimData = proof.claimData
        signed_claim = SignedClaim(
            claim=claim_data,
            signatures=[bytes.fromhex(sig.replace('0x', '')) for sig in proof.signatures]
        )
        

        assert_valid_signed_claim(signed_claim, witnesses)

    except Exception as e:
        logger.info(f'Error verifying proof: {str(e)}')
        return False

    return True