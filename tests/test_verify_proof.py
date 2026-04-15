"""
Port of JS SDK: src/__tests__/verify_proof.test.ts
Tests verify_proof end-to-end with real proof data.
(TEE tests excluded — intentionally not ported to Python SDK)
"""
import copy
import json
import pytest

from reclaim_python_sdk import verify_proof, Proof
from reclaim_python_sdk.reclaim import _get_public_data_from_proofs


# -- verifyProof tests --

@pytest.mark.asyncio
async def test_verifies_proof_signature_and_returns_extracted_data(proof_data):
    """JS: 'verifies proof signature and returns extracted data'"""
    proof = Proof.from_json(proof_data)
    result = await verify_proof(proof, {"dangerouslyDisableContentValidation": True})

    assert result.is_verified is True
    assert result.error is None
    assert len(result.data) == 1
    assert result.data[0].extracted_parameters == {
        "DYNAMIC_GEO": "IN",
        "username": "srivatsanqb",
    }


@pytest.mark.asyncio
async def test_returns_error_when_signature_verification_fails(proof_data):
    """JS: 'returns error object when signature verification fails'"""
    data = copy.deepcopy(proof_data)
    data["signatures"] = [
        "0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ff"
    ]
    proof = Proof.from_json(data)
    result = await verify_proof(proof, {"dangerouslyDisableContentValidation": True})

    assert result.is_verified is False
    assert isinstance(result.error, Exception)
    assert result.data == []


@pytest.mark.asyncio
async def test_returns_error_when_proof_data_is_tampered(proof_data):
    """JS: 'returns error when proof data is tampered (signature mismatch)'"""
    data = copy.deepcopy(proof_data)
    data["claimData"]["timestampS"] = data["claimData"]["timestampS"] + 3600
    proof = Proof.from_json(data)
    result = await verify_proof(proof, {"dangerouslyDisableContentValidation": True})

    assert result.is_verified is False
    assert isinstance(result.error, Exception)
    assert result.data == []


# -- getPublicDataFromProofs tests --

def test_returns_empty_array_if_no_public_data(proof_data):
    """JS: 'returns empty array if no publicData is present'"""
    proof1 = Proof.from_json(proof_data)
    proof2 = Proof.from_json(copy.deepcopy(proof_data))
    proof1.publicData = None
    proof2.publicData = None

    result = _get_public_data_from_proofs([proof1, proof2])
    assert result == []


def test_extracts_public_data_correctly(proof_data):
    """JS: 'extracts publicData correctly'"""
    proof = Proof.from_json(proof_data)
    proof.publicData = {"user": "test1"}

    result = _get_public_data_from_proofs([proof])
    assert result == [{"user": "test1"}]


def test_deduplicates_identical_public_data(proof_data):
    """JS: 'deduplicates identical publicData'"""
    proof1 = Proof.from_json(proof_data)
    proof2 = Proof.from_json(copy.deepcopy(proof_data))
    proof1.publicData = {"user": "test", "score": "100"}
    proof2.publicData = {"score": "100", "user": "test"}

    result = _get_public_data_from_proofs([proof1, proof2])
    assert len(result) == 1
    assert result[0] == {"user": "test", "score": "100"}


def test_returns_multiple_distinct_public_data(proof_data):
    """JS: 'returns multiple distinct publicData objects'"""
    proof1 = Proof.from_json(proof_data)
    proof2 = Proof.from_json(copy.deepcopy(proof_data))
    proof1.publicData = {"user": "test1"}
    proof2.publicData = {"user": "test2"}

    result = _get_public_data_from_proofs([proof1, proof2])
    assert len(result) == 2
    assert result == [{"user": "test1"}, {"user": "test2"}]
