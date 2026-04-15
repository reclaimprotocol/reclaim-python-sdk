"""
Port of JS SDK: src/utils/__tests__/signature-verification.test.ts
Tests signature verification with dynamically generated attestor keys.
"""
import json
import pytest
from eth_account import Account
from eth_account.messages import encode_defunct
from web3 import Web3

from reclaim_python_sdk import verify_proof, Proof
from reclaim_python_sdk.utils.interfaces import WitnessData
from reclaim_python_sdk.utils.proof_utils import assert_verified_proof
from reclaim_python_sdk.utils.proof_validation_utils import hash_proof_claim_params
from reclaim_python_sdk.utils.errors import ProofNotVerifiedError
from reclaim_python_sdk.witness import create_sign_data_for_claim
from reclaim_python_sdk.utils.interfaces import ProviderClaimData


def _make_claim():
    """Create a structurally sound claim identical to JS test fixture."""
    return ProviderClaimData(
        provider="http",
        parameters=json.dumps({
            "url": "https://example.com",
            "method": "GET",
            "responseMatches": [{"type": "contains", "value": "example"}],
            "responseRedactions": [],
            "body": "",
        }),
        owner="0x2967c5e6b3c4f179699bcc6e45bbe13b2203818e",
        timestampS=1774346626,
        context='{"contextAddress":"0x0","contextMessage":"sample context"}',
        identifier="0x0000000000000000000000000000000000000000000000000000000000000000",
        epoch=1,
    )


def _sign_claim(account, claim_data):
    """Sign claim data the same way the protocol does."""
    sign_data = create_sign_data_for_claim(claim_data)
    message = encode_defunct(text=sign_data)
    signed = account.sign_message(message)
    return "0x" + signed.signature.hex()


@pytest.mark.asyncio
async def test_verify_signature_by_recognized_attestor():
    """JS: 'should successfully verify a signature signed by a recognized attestor using internal function'"""
    attestor = Account.create()
    claim = _make_claim()
    signature = _sign_claim(attestor, claim)

    proof = Proof(
        identifier=claim.identifier,
        claimData=claim,
        witnesses=[{"id": attestor.address, "url": ""}],
        signatures=[signature],
    )
    attestors = [WitnessData(id=attestor.address, url="")]

    # Should complete without raising
    await assert_verified_proof(proof, attestors)


@pytest.mark.asyncio
async def test_forgery_fails_unauthorized_signer():
    """JS: 'should throw ProofNotVerifiedError if signed by an unauthorized key pair'"""
    attestor = Account.create()
    malicious = Account.create()
    claim = _make_claim()
    malicious_sig = _sign_claim(malicious, claim)

    proof = Proof(
        identifier=claim.identifier,
        claimData=claim,
        witnesses=[{"id": malicious.address, "url": ""}],
        signatures=[malicious_sig],
    )
    attestors = [WitnessData(id=attestor.address, url="")]

    with pytest.raises(ProofNotVerifiedError):
        await assert_verified_proof(proof, attestors)


@pytest.mark.asyncio
async def test_tampered_data_fails_after_signing():
    """JS: 'should throw ProofNotVerifiedError if claim payload data changes after signing'"""
    attestor = Account.create()
    claim = _make_claim()
    signature = _sign_claim(attestor, claim)

    # Tamper with parameters after signing
    tampered_params = json.loads(claim.parameters)
    tampered_params["url"] = "https://hacked.com"
    tampered_claim = ProviderClaimData(
        provider=claim.provider,
        parameters=json.dumps(tampered_params),
        owner=claim.owner,
        timestampS=claim.timestampS,
        context=claim.context,
        identifier=claim.identifier,
        epoch=claim.epoch,
    )

    proof = Proof(
        identifier=tampered_claim.identifier,
        claimData=tampered_claim,
        witnesses=[{"id": attestor.address, "url": ""}],
        signatures=[signature],
    )
    attestors = [WitnessData(id=attestor.address, url="")]

    with pytest.raises(ProofNotVerifiedError):
        await assert_verified_proof(proof, attestors)


@pytest.mark.asyncio
async def test_full_verify_proof_with_hash_config():
    """JS: 'should resolve full verifyProof execution successfully via generic interface'

    This test mocks the attestor API by testing assert_verified_proof directly
    and then tests hash validation separately.
    """
    attestor = Account.create()
    claim = _make_claim()
    signature = _sign_claim(attestor, claim)

    proof = Proof(
        identifier=claim.identifier,
        claimData=claim,
        witnesses=[{"id": attestor.address, "url": ""}],
        signatures=[signature],
    )

    # Verify signature passes
    attestors = [WitnessData(id=attestor.address, url="")]
    await assert_verified_proof(proof, attestors)

    # Verify hash computation works
    computed_hashes = hash_proof_claim_params(json.loads(claim.parameters))
    assert len(computed_hashes) >= 1
    assert all(h.startswith("0x") for h in computed_hashes)
