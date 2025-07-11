from dataclasses import dataclass
from typing import List, Dict, Optional
from abc import ABC, abstractmethod
# Proof-related classes
@dataclass
class WitnessData:
    id: str
    url: str

@dataclass
class ProviderClaimData:
    provider: str
    identifier: str
    parameters: str
    owner: str
    timestampS: int
    context: str
    epoch: int
    
    @classmethod
    def from_json(cls, json: Dict[str, any]) -> 'ProviderClaimData':
        return cls(json['provider'], json['identifier'], json['parameters'], json['owner'], json['timestampS'], json['context'], json['epoch'])

@dataclass
class Proof:
    identifier: str
    claimData: ProviderClaimData
    signatures: List[str]
    witnesses: List[WitnessData]
    publicData: Optional[Dict[str, str]] = None
    
    @classmethod
    def from_json(cls, json: Dict[str, any]) -> 'Proof':
        claimData = ProviderClaimData.from_json(json['claimData'])
        return cls(json['identifier'], claimData, json['signatures'], json['witnesses'], json.get('publicData'))

# Request-related classes
@dataclass
class RequestedProof:
    url: str
    parameters: Dict[str, str]

    def __init__(self):
        self.parameters: Dict[str, str] = {}

    def to_json(self) -> Dict[str, any]:
        return {
            'url': self.url,
            'parameters': self.parameters
        }

# Context class
@dataclass
class Context:
    contextAddress: str
    contextMessage: str
    
    @classmethod
    def from_json(cls, json: Dict[str, any]) -> 'Context':
        return cls(json['contextAddress'], json['contextMessage'])
    
    def to_json(self) -> Dict[str, any]:
        return {
            'contextAddress': self.contextAddress,
            'contextMessage': self.contextMessage
        }

# Beacon-related classes
@dataclass
class BeaconState:
    witnesses: List[WitnessData]
    epoch: int
    witnessesRequiredForClaim: int
    nextEpochTimestampS: int

class Beacon(ABC):
    @abstractmethod
    async def get_state(self, epoch_id: Optional[int] = None) -> BeaconState:
        pass

    @abstractmethod
    def close(self) -> None:
        pass