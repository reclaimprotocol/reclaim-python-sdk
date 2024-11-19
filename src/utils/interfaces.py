from dataclasses import dataclass
from typing import List, Dict, Optional
from abc import ABC, abstractmethod

# Provider-related classes
@dataclass
class ResponseSelection:
    invert: bool
    responseMatch: str
    xPath: Optional[str] = None
    jsonPath: Optional[str] = None

@dataclass
class BodySniff:
    enabled: bool
    regex: Optional[str] = None
    template: Optional[str] = None

@dataclass
class ProviderData:
    httpProviderId: str
    name: str
    url: str
    loginUrl: str
    responseSelections: List[ResponseSelection]
    bodySniff: Optional[BodySniff] = None

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

@dataclass
class Proof:
    identifier: str
    claimData: ProviderClaimData
    signatures: List[str]
    witnesses: List[WitnessData]
    publicData: Optional[Dict[str, str]] = None

# Request-related classes
@dataclass
class RequestedProof:
    url: str
    parameters: Dict[str, str]

# Context class
@dataclass
class Context:
    contextAddress: str
    contextMessage: str

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