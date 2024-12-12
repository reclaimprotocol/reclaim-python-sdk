from typing import List, Dict, Any, Union
from eth_account.messages import encode_defunct
from web3 import Web3
from eth_typing import HexStr
from .utils.interfaces import WitnessData, ProviderClaimData
import json

from .utils.types import ClaimInfo, BeaconState, WitnessData, ProviderClaimData, SignedClaim

def get_identifier_from_claim_info(info: ClaimInfo) -> str:
    """
    Generate a unique identifier from claim info
    
    Args:
        info (ClaimInfo): Claim information containing provider, parameters and context
        
    Returns:
        str: Hex string identifier
    """
    string = f"{info.provider}\n{info.parameters}\n{info.context}"
    hash_bytes = Web3.keccak(text=string)
    return '0x' + hash_bytes.hex().lower()

def fetch_witness_list_for_claim(
    beacon_state: BeaconState,
    params: Union[str, ClaimInfo],
    timestamp_s: int
) -> List[WitnessData]:
    """
    Select witnesses for a claim based on deterministic randomness
    
    Args:
        beacon_state (BeaconState): Current beacon state
        params (Union[str, ClaimInfo]): Claim parameters or identifier
        timestamp_s (int): Timestamp in seconds
        
    Returns:
        List[WitnessData]: Selected witness list
    """
    identifier = params if isinstance(params, str) else get_identifier_from_claim_info(params)
    
    complete_input = "\n".join([
        identifier,
        str(beacon_state.epoch),
        str(beacon_state.witnessesRequiredForClaim),
        str(timestamp_s)
    ])
    
    complete_hash = Web3.keccak(text=complete_input)
    witnesses_left = beacon_state.witnesses.copy()
    selected_witnesses = []
    byte_offset = 0
    
    for i in range(beacon_state.witnessesRequiredForClaim):
        # Get 4 bytes for random seed
        random_seed = int.from_bytes(
            complete_hash[byte_offset:byte_offset + 4],
            byteorder='big'
        )
        witness_index = random_seed % len(witnesses_left)
        witness = witnesses_left[witness_index]
        selected_witnesses.append(witness)
        
        # Remove selected witness
        witnesses_left[witness_index] = witnesses_left[-1]
        witnesses_left.pop()
        byte_offset = (byte_offset + 4) % len(complete_hash)
    
    return selected_witnesses

def create_sign_data_for_claim(data: ProviderClaimData) -> str:
    """
    Create string to be signed for a claim
    
    Args:
        data (ProviderClaimData): Claim data
        
    Returns:
        str: Data string to sign
    """
    lines = [
        data.identifier,
        data.owner.lower(),
        str(data.timestampS),
        str(data.epoch)
    ]
    return "\n".join(lines)