from typing import List, Dict, Any, Optional, TypedDict, Callable, Awaitable
from web3 import Web3
from web3.contract import Contract
from eth_account.account import Account
from eth_typing import Address, HexStr
from .utils.interfaces import Beacon, BeaconState, WitnessData
from .contract_data.abi import ABI
import logging

# Setup logger
logger = logging.getLogger('reclaim')

DEFAULT_CHAIN_ID = 11155420

# Global cache for contracts
existing_contracts_map: Dict[str, Contract] = {}

# Contract configuration
CONTRACT_CONFIG = {
    "0x1a4": {
        "chainName": "opt-goerli",
        "address": "0xF93F605142Fb1Efad7Aa58253dDffF67775b4520",
        "rpcUrl": "https://opt-goerli.g.alchemy.com/v2/rksDkSUXd2dyk2ANy_zzODknx_AAokui"
    },
    "0xaa37dc": {
        "chainName": "opt-sepolia",
        "address": "0x6D0f81BDA11995f25921aAd5B43359630E65Ca96",
        "rpcUrl": "https://opt-sepolia.g.alchemy.com/v2/aO1-SfG4oFRLyAiLREqzyAUu0HTCwHgs"
    }
}

def get_contract(chain_id: int) -> Optional[Contract]:
    chain_key = f"0x{chain_id:x}"
    if chain_key not in existing_contracts_map:
        contract_data = CONTRACT_CONFIG.get(chain_key)
        if not contract_data:
            raise ValueError(f'Unsupported chain: "{chain_key}"')
        
        w3 = Web3(Web3.HTTPProvider(contract_data['rpcUrl']))
        contract = w3.eth.contract(
            address=contract_data['address'],
            abi=ABI
        )
        existing_contracts_map[chain_key] = contract
    
    return existing_contracts_map[chain_key]

async def fetch_epoch_data(contract: Contract, client: Web3, epoch_id: int = 0) -> BeaconState:
    try:
        # Call the fetchEpoch function with BigInt
        function = contract.functions.fetchEpoch(Web3.to_wei(epoch_id, 'wei'))
        response = function.call()
        
        if not response or len(response) < 5:
            logger.info(f'Invalid epoch ID: {epoch_id}')
            raise ValueError(f'Invalid epoch ID: {epoch_id}')

        # Extract data from response tuple
        epoch = int(response[0])
        witnesses_data = response[3]
        witnesses_required_for_claim = int(response[4])
        next_epoch_timestamp_s = int(response[2])

        # Convert witnesses data to list of WitnessData objects
        witnesses = [
            WitnessData(
                id=str(witness[0]),
                url=str(witness[1])
            ) for witness in witnesses_data
        ]

        beacon_state = BeaconState(
            epoch=epoch,
            witnesses=witnesses,
            witnessesRequiredForClaim=witnesses_required_for_claim,
            nextEpochTimestampS=next_epoch_timestamp_s
        )
        
        return beacon_state
        
    except Exception as e:
        logger.error(f'Error fetching epoch data: {str(e)}')
        raise ValueError(f'Error fetching epoch data: {str(e)}')



# Update the make_beacon function to use the cache
async def make_beacon(chain_id: Optional[int] = None) -> Optional[Beacon]:
    chain_id = chain_id or DEFAULT_CHAIN_ID
    contract = get_contract(chain_id)
    
    if contract:
        contract_data = CONTRACT_CONFIG[f"0x{DEFAULT_CHAIN_ID:x}"]
        client = Web3(Web3.HTTPProvider(contract_data['rpcUrl']))
        epoch_data = await fetch_epoch_data(contract, client)
        return BeaconImpl(contract, epoch_data)
    
    return None

class BeaconImpl(Beacon):
    contract: Contract
    state: BeaconState
    
    def __init__(self, contract: Contract, state: BeaconState):
        self.contract = contract
        self.state = BeaconState(
            epoch=state.epoch,
            witnesses=state.witnesses,
            witnessesRequiredForClaim=state.witnessesRequiredForClaim,
            nextEpochTimestampS=state.nextEpochTimestampS
        )
        
    async def get_state(self, epoch_id: Optional[int] = None) -> BeaconState:
        if epoch_id is None or epoch_id == self.state.epoch:
            return self.state

        client = Web3(Web3.HTTPProvider(CONTRACT_CONFIG[f"0x{DEFAULT_CHAIN_ID:x}"]['rpcUrl']))
        return await fetch_epoch_data(self.contract, client, epoch_id)
    
    def close(self) -> None:
        pass

