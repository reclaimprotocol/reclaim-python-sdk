"""
Port of JS SDK: src/utils/__tests__/witness.test.ts
Tests hash generation, identifier computation, and canonicalization.
"""
import pytest
from json_canonical import canonicalize
from web3 import Web3

from reclaim_python_sdk.witness import get_identifier_from_claim_info
from reclaim_python_sdk.utils.types import ClaimInfo
from reclaim_python_sdk.utils.proof_validation_utils import (
    hash_proof_claim_params,
    get_provider_params_as_canonicalized_string,
)


def _canonical_str(obj):
    result = canonicalize(obj)
    return result.decode("utf-8") if isinstance(result, bytes) else result


# -- hashProofClaimParams tests --

class TestHashProofClaimParams:

    def test_single_hash_no_optional_rules(self):
        """JS: 'should generate a single hash when there are no optional rules'"""
        params = {
            "url": "https://example.com",
            "method": "GET",
            "body": "",
            "responseMatches": [
                {"value": "name", "type": "contains", "invert": False, "isOptional": None}
            ],
            "responseRedactions": [
                {"jsonPath": "$.name", "regex": "name", "xPath": ""}
            ],
        }
        result = hash_proof_claim_params(params)
        assert isinstance(result, list)
        assert len(result) == 1

    def test_optional_combinations_2n_minus_1(self):
        """JS: 'should generate (2^n - 1) possible hashes for n fully optional rule pairs'"""
        params = {
            "url": "https://example.com",
            "method": "GET",
            "body": "",
            "responseMatches": [
                {"value": "name1", "type": "contains", "invert": False, "isOptional": True},
                {"value": "name2", "type": "contains", "invert": False, "isOptional": True},
                {"value": "name3", "type": "contains", "invert": False, "isOptional": True},
            ],
            "responseRedactions": [
                {"jsonPath": "$.name1", "regex": "name1", "xPath": ""},
                {"jsonPath": "$.name2", "regex": "name2", "xPath": ""},
                {"jsonPath": "$.name3", "regex": "name3", "xPath": ""},
            ],
        }
        result = hash_proof_claim_params(params)
        # 3 optional rules => 2^3 - 1 = 7 valid combinations
        assert len(result) == 7
        assert len(set(result)) == 7  # all unique

    def test_mixed_required_and_optional(self):
        """JS: 'should generate 2^n hashes for n optional pairs when there are other required rules'"""
        params = {
            "url": "https://example.com",
            "method": "GET",
            "body": "",
            "responseMatches": [
                {"value": "required1", "type": "contains", "invert": False, "isOptional": None},
                {"value": "optional1", "type": "contains", "invert": False, "isOptional": True},
                {"value": "optional2", "type": "contains", "invert": False, "isOptional": True},
            ],
            "responseRedactions": [
                {"jsonPath": "$.req1", "regex": "req1", "xPath": ""},
                {"jsonPath": "$.opt1", "regex": "opt1", "xPath": ""},
                {"jsonPath": "$.opt2", "regex": "opt2", "xPath": ""},
            ],
        }
        result = hash_proof_claim_params(params)
        # 1 required + 2 optional => 2^2 = 4 combinations
        assert len(result) == 4
        assert len(set(result)) == 4


# -- getIdentifierFromClaimInfo tests --

class TestGetIdentifierFromClaimInfo:

    def test_empty_context(self):
        """JS: 'should generate correct identifier with empty context'"""
        info = ClaimInfo(provider="provider1", parameters="param1", context="")
        result = get_identifier_from_claim_info(info)
        expected_str = "provider1\nparam1\n"
        expected = "0x" + Web3.keccak(text=expected_str).hex().lower()
        assert result == expected

    def test_re_canonicalize_non_empty_context(self):
        """JS: 'should re-canonicalize non-empty context'"""
        info = ClaimInfo(provider="provider1", parameters="param1", context='{"b": 2, "a": 1}')
        result = get_identifier_from_claim_info(info)
        canonical_context = _canonical_str({"b": 2, "a": 1})
        expected_str = f"provider1\nparam1\n{canonical_context}"
        expected = "0x" + Web3.keccak(text=expected_str).hex().lower()
        assert result == expected

    def test_invalid_context_json_raises(self):
        """JS: 'should throw error for invalid context JSON'"""
        info = ClaimInfo(provider="provider1", parameters="param1", context="invalid json")
        with pytest.raises(ValueError, match="unable to parse non-empty context. Must be JSON"):
            get_identifier_from_claim_info(info)


# -- getProviderParamsAsCanonicalizedString tests --

class TestGetProviderParamsAsCanonicalizedString:

    def test_single_string_no_optional(self):
        """JS: 'should return a single canonicalized string when no optional rules'"""
        params = {
            "url": "http://a",
            "method": "GET",
            "body": "",
            "responseMatches": [{"type": "contains", "value": "a", "isOptional": False}],
            "responseRedactions": [{"jsonPath": "b", "regex": "c", "xPath": "d"}],
        }
        result = get_provider_params_as_canonicalized_string(params)
        assert len(result) == 1
        assert isinstance(result[0], str)

        expected = _canonical_str({
            "url": "http://a",
            "method": "GET",
            "body": "",
            "responseMatches": [{"value": "a", "type": "contains"}],
            "responseRedactions": [{"xPath": "d", "jsonPath": "b", "regex": "c"}],
        })
        assert result[0] == expected

    def test_multiple_strings_for_optional_rules(self):
        """JS: 'should return multiple strings for optional rules'"""
        params = {
            "url": "http://a",
            "method": "GET",
            "body": "",
            "responseMatches": [
                {"type": "contains", "value": "a", "isOptional": True},
                {"type": "regex", "value": "b", "isOptional": True},
            ],
            "responseRedactions": [
                {"jsonPath": "b", "regex": "c", "xPath": "d"},
                {"jsonPath": "e", "regex": "f", "xPath": "g"},
            ],
        }
        result = get_provider_params_as_canonicalized_string(params)
        # 2 optional => 2^2 - 1 = 3 combinations
        assert len(result) == 3

    def test_filter_out_missing_required(self):
        """JS: 'should filter out combinations missing required rules'"""
        params = {
            "url": "http://a",
            "method": "GET",
            "body": "",
            "responseMatches": [
                {"type": "contains", "value": "a", "isOptional": False},
                {"type": "regex", "value": "b", "isOptional": True},
            ],
            "responseRedactions": [
                {"jsonPath": "b", "regex": "c", "xPath": "d"},
                {"jsonPath": "e", "regex": "f", "xPath": "g"},
            ],
        }
        result = get_provider_params_as_canonicalized_string(params)
        # Rule 1 required, Rule 2 optional => 2 combinations
        assert len(result) == 2

    def test_undefined_rules_returns_base_object(self):
        """JS: 'should handle undefined rules properly and return base object'"""
        params = {"url": "http://a", "method": "GET", "body": ""}
        result = get_provider_params_as_canonicalized_string(params)
        assert len(result) == 1
        expected = _canonical_str({
            "url": "http://a",
            "method": "GET",
            "body": "",
            "responseMatches": [],
            "responseRedactions": [],
        })
        assert result[0] == expected
