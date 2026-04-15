from .reclaim import ReclaimProofRequest, verify_proof, verify_proof_deprecated
from .utils.interfaces import Proof
from .utils.types import (
    VerificationConfig,
    VerifyProofResult,
    VerifyProofResultSuccess,
    VerifyProofResultFailure,
    TrustedData,
    ValidationConfigWithHash,
    ValidationConfigWithProviderInformation,
    ValidationConfigWithDisabledValidation,
    HashRequirement,
)

__all__ = [
    "ReclaimProofRequest",
    "verify_proof",
    "verify_proof_deprecated",
    "Proof",
    "VerificationConfig",
    "VerifyProofResult",
    "VerifyProofResultSuccess",
    "VerifyProofResultFailure",
    "TrustedData",
    "ValidationConfigWithHash",
    "ValidationConfigWithProviderInformation",
    "ValidationConfigWithDisabledValidation",
    "HashRequirement",
]
