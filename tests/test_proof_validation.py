"""
Port of JS SDK: src/utils/__tests__/proof-validation.test.ts
Tests hash-based content validation with real and mock proof data.
"""
import pytest

from reclaim_python_sdk import Proof
from reclaim_python_sdk.utils.types import HashRequirement, ValidationConfigWithHash
from reclaim_python_sdk.utils.proof_validation_utils import (
    assert_validate_proof,
    assert_valid_proofs_by_hash,
)
from reclaim_python_sdk.utils.errors import ProofNotValidatedError


# The real proof's computed hash (from JS test: kaggle proof)
REAL_PROOF_HASH = "0x4c20776ae89ab7eead49e4e393f4e07348a4d85e21869201aa6eea6e2bc07f5b"

# The valid provider hash config that matches the real proof
VALID_HASH_CONFIG = ValidationConfigWithHash(
    hashes=[
        HashRequirement(
            value=REAL_PROOF_HASH,
        )
    ]
)

# Invalid provider config — different jsonPath causes different hash
INVALID_HASH_CONFIG_JSONPATH = ValidationConfigWithHash(
    hashes=[
        HashRequirement(
            value="0xdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
        )
    ]
)


@pytest.mark.asyncio
async def test_valid_proof_passes_hash_validation(kaggle_proof_data):
    """JS: 'should validate proofs correctly' (with matching hash config)"""
    proof = Proof.from_json(kaggle_proof_data)
    # Should not raise
    await assert_validate_proof([proof], VALID_HASH_CONFIG)


@pytest.mark.asyncio
async def test_invalid_hash_fails_validation(kaggle_proof_data):
    """JS: 'should validate invalid proofs and return false' (hash mismatch)"""
    proof = Proof.from_json(kaggle_proof_data)
    with pytest.raises((ProofNotValidatedError, Exception)):
        await assert_validate_proof([proof], INVALID_HASH_CONFIG_JSONPATH)


# -- Array Values and Multiple Proofs Configurations --

class TestArrayValuesAndMultipleProofs:
    """JS: 'Array Values and Multiple Proofs Configurations'"""

    @pytest.mark.asyncio
    async def test_proof_hash_intersects_with_expected_array(self, kaggle_proof_data):
        """JS: 'should validate proof successfully if proof hash intersects with expected hash array'"""
        proof = Proof.from_json(kaggle_proof_data)
        config = ValidationConfigWithHash(
            hashes=[
                HashRequirement(
                    value=[
                        REAL_PROOF_HASH,
                        "0xfakehash1234567890abcdef1234567890abcdef1234567890abcdef12345678",
                    ]
                )
            ]
        )
        await assert_validate_proof([proof], config)

    @pytest.mark.asyncio
    async def test_duplicated_proofs_allowed_when_multiple_true(self, kaggle_proof_data):
        """JS: 'should accept duplicated proofs of the same hash when multiple is true'"""
        proof = Proof.from_json(kaggle_proof_data)
        config = ValidationConfigWithHash(
            hashes=[HashRequirement(value=REAL_PROOF_HASH, multiple=True)]
        )
        await assert_validate_proof([proof, proof], config)

    @pytest.mark.asyncio
    async def test_duplicated_proofs_rejected_when_multiple_false(self, kaggle_proof_data):
        """JS: 'should reject duplicated proofs of the same hash when multiple is false'"""
        proof = Proof.from_json(kaggle_proof_data)
        config = ValidationConfigWithHash(
            hashes=[HashRequirement(value=REAL_PROOF_HASH, multiple=False)]
        )
        with pytest.raises(ProofNotValidatedError, match="not allowed to appear more than once"):
            await assert_validate_proof([proof, proof], config)

    @pytest.mark.asyncio
    async def test_duplicated_proofs_allowed_when_multiple_omitted(self, kaggle_proof_data):
        """JS: 'should accept duplicated proofs of the same hash when multiple option is omitted (defaults to true)'"""
        proof = Proof.from_json(kaggle_proof_data)
        config = ValidationConfigWithHash(
            hashes=[HashRequirement(value=REAL_PROOF_HASH)]  # multiple omitted
        )
        await assert_validate_proof([proof, proof], config)

    @pytest.mark.asyncio
    async def test_missing_proof_rejected_when_required_omitted(self, kaggle_proof_data):
        """JS: 'should reject validation when a proof is missing and required option is omitted (defaults to true)'"""
        proof = Proof.from_json(kaggle_proof_data)
        config = ValidationConfigWithHash(
            hashes=[
                HashRequirement(
                    value="0xMISSINGHASH1234567890abcdef1234567890abcdef1234567890abcdef123"
                )
            ]
        )
        with pytest.raises(ProofNotValidatedError, match="was not found"):
            await assert_validate_proof([proof], config)

    @pytest.mark.asyncio
    async def test_missing_proof_rejected_when_required_true(self, kaggle_proof_data):
        """JS: 'should reject validation when a required proof is missing (required is true)'"""
        proof = Proof.from_json(kaggle_proof_data)
        config = ValidationConfigWithHash(
            hashes=[
                HashRequirement(
                    value="0xMISSINGHASH1234567890abcdef1234567890abcdef1234567890abcdef123",
                    required=True,
                )
            ]
        )
        with pytest.raises(ProofNotValidatedError, match="was not found"):
            await assert_validate_proof([proof], config)

    @pytest.mark.asyncio
    async def test_optional_missing_proof_accepted(self, kaggle_proof_data):
        """JS: 'should accept validation when an optional proof is missing (required is false)'"""
        proof = Proof.from_json(kaggle_proof_data)
        config = ValidationConfigWithHash(
            hashes=[
                HashRequirement(value=REAL_PROOF_HASH),
                HashRequirement(
                    value="0xMISSINGHASH1234567890abcdef1234567890abcdef1234567890abcdef123",
                    required=False,
                ),
            ]
        )
        await assert_validate_proof([proof], config)
