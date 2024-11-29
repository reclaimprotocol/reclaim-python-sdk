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
    
    @classmethod
    def from_json(cls, json: Dict[str, any]) -> 'ResponseSelection':
        return cls(json['invert'], json['responseMatch'], json['xPath'], json['jsonPath'])

@dataclass
class BodySniff:
    enabled: bool
    regex: Optional[str] = None
    template: Optional[str] = None
    
    @classmethod
    def from_json(cls, json: Dict[str, any]) -> 'BodySniff':
        return cls(json['enabled'], json['regex'], json['template'])
    
    
    def to_json(self) -> Dict[str, any]:
        return {
            'enabled': self.enabled,
            'regex': self.regex,
            'template': self.template
        }

@dataclass
class ProviderData:
    httpProviderId: str
    name: str
    url: str
    loginUrl: str
    responseSelections: List[ResponseSelection]
    bodySniff: Optional[BodySniff] = None
    

    @classmethod
    def from_json(cls, json: Dict[str, any]) -> 'ProviderData':
        httpProviderId = json['httpProviderId']
        name = json['name']
        url = json['url']
        loginUrl = json['loginUrl']
        responseSelections = [ResponseSelection.from_json(rs) for rs in json['responseSelections']]
        bodySniff = BodySniff.from_json(json['bodySniff']) if json['bodySniff'] else None
        
        return cls(httpProviderId, name, url, loginUrl, responseSelections, bodySniff)

    def to_json(self) -> Dict[str, any]:
        return {
            'httpProviderId': self.httpProviderId,
            'name': self.name,
            'url': self.url,
            'loginUrl': self.loginUrl,
            'responseSelections': [rs.to_json() for rs in self.responseSelections],
            'bodySniff': self.bodySniff.to_json() if self.bodySniff else None
        }

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