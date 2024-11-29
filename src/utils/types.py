from typing import Dict, Any, Optional, Callable, List
from .interfaces import *
from enum import Enum

ClaimID = str

@dataclass
class ClaimInfo:
    context: str
    provider: str
    parameters: str

    @classmethod
    def from_json(cls, json: Dict[str, Any]) -> 'ClaimInfo':
        return cls(
            context=json.get('context', ''),
            provider=json['provider'],
            parameters=json['parameters']
        )

    def to_json(self) -> Dict[str, Any]:
        return {
            'context': self.context,
            'provider': self.provider,
            'parameters': self.parameters
        }

@dataclass
class AnyClaimInfo:
    claim_info: Optional[ClaimInfo] = None
    identifier: Optional[ClaimID] = None

    @classmethod
    def from_claim_info(cls, claim_info: ClaimInfo) -> 'AnyClaimInfo':
        return cls(claim_info=claim_info)

    @classmethod
    def from_identifier(cls, identifier: ClaimID) -> 'AnyClaimInfo':
        return cls(identifier=identifier)

    @classmethod
    def from_json(cls, json: Dict[str, Any]) -> 'AnyClaimInfo':
        if 'identifier' in json:
            return cls.from_identifier(json['identifier'])
        return cls.from_claim_info(ClaimInfo.from_json(json))

    def to_json(self) -> Dict[str, Any]:
        if self.claim_info is not None:
            return self.claim_info.to_json()
        return {'identifier': self.identifier}

@dataclass
class CompleteClaimData:
    owner: str
    timestamp_s: int
    epoch: int
    any_claim_info: AnyClaimInfo

    @classmethod
    def from_json(cls, json: Dict[str, Any]) -> 'CompleteClaimData':
        return cls(
            owner=json['owner'],
            timestamp_s=json['timestampS'],
            epoch=json['epoch'],
            any_claim_info=AnyClaimInfo.from_json(json)
        )

    def to_json(self) -> Dict[str, Any]:
        return {
            'owner': self.owner,
            'timestampS': self.timestamp_s,
            'epoch': self.epoch,
            **self.any_claim_info.to_json()
        }

@dataclass
class SignedClaim:
    claim: ProviderClaimData
    signatures: List[List[int]]

    @classmethod
    def from_json(cls, json: Dict[str, Any]) -> 'SignedClaim':
        return cls(
            claim=ProviderClaimData.from_json(json['claim']),
            signatures=[list(sig) for sig in json['signatures']]
        )

    def to_json(self) -> Dict[str, Any]:
        return {
            'claim': self.claim.to_json(),
            'signatures': self.signatures
        }

QueryParams = Dict[str, Any]

@dataclass
class CreateVerificationRequest:
    provider_ids: List[str]
    application_secret: Optional[str] = None

@dataclass
class StartSessionParams:
    on_success: Callable[['Proof'], None]
    on_error: Callable[[Exception], None]

@dataclass
class ProofRequestOptions:
    log: Optional[bool] = None
    accept_ai_providers: Optional[bool] = None
    use_app_clip: Optional[bool] = None

    @classmethod
    def from_json(cls, json: Dict[str, Any]) -> 'ProofRequestOptions':
        return cls(
            log=json.get('log'),
            accept_ai_providers=json.get('acceptAiProviders'),
            use_app_clip=json.get('useAppClip')
        )

    def to_json(self) -> Dict[str, Any]:
        return {
            'log': self.log,
            'acceptAiProviders': self.accept_ai_providers,
            'useAppClip': self.use_app_clip
        }

@dataclass
class InitSessionResponse:
    session_id: str
    provider: ProviderData  # Forward reference
    
    @classmethod
    def from_json(cls, json: Dict[str, Any]) -> 'InitSessionResponse':
        return cls(
            session_id=json['sessionId'],
            provider=ProviderData.from_json(json['provider'])
        )


@dataclass
class UpdateSessionResponse:
    message: Optional[str] = None

@dataclass
class StatusUrlResponse:
    message: str
    session: Optional['Session'] = None
    provider_id: Optional[str] = None

    @classmethod
    def from_json(cls, json: Dict[str, Any]) -> 'StatusUrlResponse':
        return cls(
            message=json['message'],
            session=Session.from_json(json['session']) if json.get('session') else None,
            provider_id=json.get('providerId')
        )

class SessionStatus(str, Enum):
    SESSION_INIT = "SESSION_INIT"
    SESSION_STARTED = "SESSION_STARTED"
    USER_INIT_VERIFICATION = "USER_INIT_VERIFICATION"
    USER_STARTED_VERIFICATION = "USER_STARTED_VERIFICATION"
    PROOF_GENERATION_STARTED = "PROOF_GENERATION_STARTED"
    PROOF_GENERATION_SUCCESS = "PROOF_GENERATION_SUCCESS"
    PROOF_GENERATION_FAILED = "PROOF_GENERATION_FAILED"
    PROOF_SUBMITTED = "PROOF_SUBMITTED"
    PROOF_SUBMISSION_FAILED = "PROOF_SUBMISSION_FAILED"
    PROOF_MANUAL_VERIFICATION_SUBMITED = "PROOF_MANUAL_VERIFICATION_SUBMITED"

@dataclass
class TemplateData:
    session_id: str
    provider_id: str
    application_id: str
    signature: str
    timestamp: str
    callback_url: str
    context: str
    parameters: Dict[str, str]
    redirect_url: str
    accept_ai_providers: bool
    sdk_version: str

    @classmethod
    def from_json(cls, json: Dict[str, Any]) -> 'TemplateData':
        return cls(
            session_id=json['sessionId'],
            provider_id=json['providerId'],
            application_id=json['applicationId'],
            signature=json['signature'],
            timestamp=json['timestamp'],
            callback_url=json['callbackUrl'],
            context=json['context'],
            parameters=json['parameters'],
            redirect_url=json['redirectUrl'],
            accept_ai_providers=json['acceptAiProviders'],
            sdk_version=json['sdkVersion']
        )

    def to_json(self) -> Dict[str, Any]:
        return {
            'sessionId': self.session_id,
            'providerId': self.provider_id,
            'applicationId': self.application_id,
            'signature': self.signature,
            'timestamp': self.timestamp,
            'callbackUrl': self.callback_url,
            'context': self.context,
            'parameters': self.parameters,
            'redirectUrl': self.redirect_url,
            'acceptAiProviders': self.accept_ai_providers,
            'sdkVersion': self.sdk_version
        }

@dataclass
class Session:
    id: str
    appId: str
    httpProviderId: List[str]
    sessionId: str
    statusV2: str
    proofs: Optional[List['Proof']] = None

    @classmethod
    def from_json(cls, json: Dict[str, Any]) -> 'Session':
        return cls(
            id=json['id'],
            appId=json['appId'],
            httpProviderId=json['httpProviderId'],
            sessionId=json['sessionId'],
            proofs=[Proof.from_json(p) for p in json['proofs']] if json.get('proofs') else None,
            statusV2=json['statusV2']
        ) 