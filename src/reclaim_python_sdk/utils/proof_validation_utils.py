import httpx
import json
import logging
from typing import Dict, Any, List, Optional, Union

from json_canonical import canonicalize
from web3 import Web3

from .constants import get_provider_configs_url
from .errors import (
    ProofNotValidatedError,
    ProviderConfigFetchError,
    UnknownProofsNotValidatedError,
    InvalidRequestSpecError,
)
from .interfaces import Proof
from .types import (
    HashRequirement,
    ValidationConfigWithHash,
    ValidationConfigWithProviderInformation,
    ValidationConfigWithDisabledValidation,
    VerificationConfig,
)

logger = logging.getLogger(__name__)

# Matches JS SDK defaults
HASH_REQUIRED_DEFAULT = True
HASH_MATCH_MULTIPLE_DEFAULT = True

ALLOWED_HTTP_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}


def is_http_provider_claim_params(params: Any) -> bool:
    if not isinstance(params, dict):
        return False
    return (
        isinstance(params.get("url"), str)
        and isinstance(params.get("method"), str)
        and params["method"] in ALLOWED_HTTP_METHODS
        and (params.get("body") is None or isinstance(params.get("body"), str))
        and isinstance(params.get("responseMatches"), list)
        and len(params["responseMatches"]) > 0
        and isinstance(params.get("responseRedactions"), list)
    )


def get_http_provider_claim_params_from_proof(proof: Proof) -> Dict[str, Any]:
    try:
        claim_params = json.loads(proof.claimData.parameters)
        if is_http_provider_claim_params(claim_params):
            return claim_params
    except (json.JSONDecodeError, TypeError):
        pass
    raise ProofNotValidatedError("Proof has no HTTP provider params to hash")


def _canonicalize_to_str(obj: Any) -> str:
    result = canonicalize(obj)
    return result.decode("utf-8") if isinstance(result, bytes) else result


def get_provider_params_as_canonicalized_string(params: Dict[str, Any]) -> List[str]:
    """
    Generates 2^N canonicalized permutations for optional rules using bitmask.
    Mirrors JS SDK's getProviderParamsAsCanonicalizedString.
    """
    response_matches = params.get("responseMatches") or []
    response_redactions = params.get("responseRedactions") or []
    pairs_count = len(response_matches)
    valid_strings: List[str] = []

    total_combinations = 1 << pairs_count

    for i in range(total_combinations):
        is_valid = True
        included_count = 0

        current_matches = []
        current_redactions = []

        for j in range(pairs_count):
            is_included = (i & (1 << j)) != 0
            match = response_matches[j] if j < len(response_matches) else None
            redaction = response_redactions[j] if j < len(response_redactions) else None

            if is_included:
                if match:
                    entry = {
                        "type": match.get("type", "contains"),
                        "value": match.get("value", ""),
                    }
                    if match.get("invert"):
                        entry["invert"] = True
                    current_matches.append(entry)
                if redaction:
                    entry = {
                        "jsonPath": redaction.get("jsonPath", ""),
                        "regex": redaction.get("regex", ""),
                        "xPath": redaction.get("xPath", ""),
                    }
                    if redaction.get("hash"):
                        entry["hash"] = redaction["hash"]
                    current_redactions.append(entry)
                included_count += 1
            else:
                if match and not match.get("isOptional"):
                    is_valid = False
                    break

        if is_valid and included_count > 0:
            filtered_params = {
                "body": params.get("body", ""),
                "method": params.get("method", "GET"),
                "responseMatches": current_matches,
                "responseRedactions": current_redactions,
                "url": params.get("url", ""),
            }
            valid_strings.append(_canonicalize_to_str(filtered_params))

    if not valid_strings:
        filtered_params = {
            "body": params.get("body", ""),
            "method": params.get("method", "GET"),
            "responseMatches": [],
            "responseRedactions": [],
            "url": params.get("url", ""),
        }
        valid_strings.append(_canonicalize_to_str(filtered_params))

    return valid_strings


def hash_proof_claim_params(params: Dict[str, Any]) -> List[str]:
    """
    Computes keccak256 hash(es) of canonicalized claim params.
    Mirrors JS SDK's hashProofClaimParams.
    """
    serialized_list = get_provider_params_as_canonicalized_string(params)
    return [
        '0x' + Web3.keccak(text=s).hex().lower()
        for s in serialized_list
    ]


def assert_valid_proofs_by_hash(
    proofs: List[Proof],
    hashes: List[HashRequirement],
) -> None:
    """
    Validates that proofs match expected hash requirements.
    Mirrors JS SDK's assertValidProofsByHash.
    """
    if not hashes:
        raise ProofNotValidatedError("No proof hash was provided for validation")

    # Build map of proof index -> computed hashes
    unvalidated: Dict[int, List[str]] = {}
    for i, proof in enumerate(proofs):
        claim_params = get_http_provider_claim_params_from_proof(proof)
        computed = hash_proof_claim_params(claim_params)
        unvalidated[i] = [h.lower().strip() for h in computed]

    for hash_req in hashes:
        found = False
        expected_values = hash_req.value if isinstance(hash_req.value, list) else [hash_req.value]
        expected_hashes = [h.lower().strip() for h in expected_values]
        is_required = hash_req.required if hash_req.required is not None else HASH_REQUIRED_DEFAULT
        can_match_multiple = hash_req.multiple if hash_req.multiple is not None else HASH_MATCH_MULTIPLE_DEFAULT

        to_remove = []
        for idx, proof_hashes in unvalidated.items():
            intersection = [eh for eh in expected_hashes if eh in proof_hashes]
            if intersection:
                to_remove.append(idx)
                if not found:
                    found = True
                elif not can_match_multiple:
                    expected_str = expected_hashes[0] if len(expected_hashes) == 1 else f"[{', '.join(expected_hashes)}]"
                    raise ProofNotValidatedError(
                        f"Proof by hash '{expected_str}' is not allowed to appear more than once"
                    )

        for idx in to_remove:
            del unvalidated[idx]

        if not found and is_required:
            expected_str = expected_hashes[0] if len(expected_hashes) == 1 else f"[{', '.join(expected_hashes)}]"
            raise ProofNotValidatedError(
                f"Proof by required hash '{expected_str}' was not found"
            )

    # Security check: reject extra proofs that couldn't be validated
    if unvalidated:
        contact_support = "Please contact Reclaim Protocol Support team or mail us at support@reclaimprotocol.org."
        unvalidated_hashes_str = [
            h[0] if len(h) == 1 else f"[{', '.join(h)}]"
            for h in unvalidated.values()
        ]
        raise UnknownProofsNotValidatedError(
            f"Extra {len(unvalidated)} proof(s) by hashes {', '.join(unvalidated_hashes_str)} "
            f"was found but could not be validated and indicates a security risk. {contact_support}"
        )


async def fetch_provider_configs(
    provider_id: str,
    version: Optional[str] = None,
    allowed_tags: Optional[List[str]] = None,
) -> Dict[str, Any]:
    url = get_provider_configs_url(
        provider_id,
        version=version or "",
        allowed_tags=",".join(allowed_tags) if allowed_tags else "",
    )
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers={"Content-Type": "application/json"})
        if response.status_code != 200:
            raise ProviderConfigFetchError(
                f"Failed to fetch provider configs: {response.status_code}"
            )
        return response.json()


def _hash_request_spec(request_spec: Dict[str, Any]) -> HashRequirement:
    """Computes hash requirement from a request spec."""
    params = {**request_spec}
    body_sniff = request_spec.get("bodySniff")
    if body_sniff and isinstance(body_sniff, dict) and body_sniff.get("enabled"):
        params["body"] = body_sniff.get("template", "")
    else:
        params["body"] = ""

    hashes = hash_proof_claim_params(params)
    return HashRequirement(
        value=hashes if len(hashes) > 1 else hashes[0],
        required=request_spec.get("required", True),
        multiple=request_spec.get("multiple", False),
    )


# --- Template parameter support (mirrors JS SDK providerUtils.ts) ---

def _take_pairs_where_value_is_array(
    obj: Optional[Dict[str, str]],
) -> Dict[str, List[str]]:
    """Extract entries whose values are JSON arrays."""
    if not obj:
        return {}
    pairs: Dict[str, List[str]] = {}
    for key, value in obj.items():
        if isinstance(value, list) and value:
            pairs[key] = value
        else:
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list) and parsed:
                    pairs[key] = parsed
            except (json.JSONDecodeError, TypeError):
                pass
    return pairs


def _take_template_parameters_from_proofs(
    proofs: Optional[List[Proof]],
) -> Dict[str, List[str]]:
    """Extract template parameters from proof contexts."""
    if not proofs:
        return {}
    merged: Dict[str, str] = {}
    for proof in proofs:
        try:
            ctx = json.loads(proof.claimData.context)
            extracted = ctx.get("extractedParameters", {})
            if isinstance(extracted, dict):
                merged.update(extracted)
        except (json.JSONDecodeError, TypeError):
            pass
    return _take_pairs_where_value_is_array(merged)


def _generate_specs_from_request_spec_template(
    templates: List[Dict[str, Any]],
    template_parameters: Dict[str, List[str]],
) -> List[Dict[str, Any]]:
    """
    Generates request specs from templates by substituting template parameters.
    Mirrors JS SDK's generateSpecsFromRequestSpecTemplate.
    """
    if not templates:
        return []

    generated: List[Dict[str, Any]] = []

    for template in templates:
        template_vars = template.get("templateParams") or []
        if not template_vars:
            generated.append(template)
            continue

        pair_match = [
            (key, values)
            for key, values in template_parameters.items()
            if key in template_vars and values
        ]
        if len(pair_match) != len(template_vars):
            raise InvalidRequestSpecError(
                "Not all template variables are present for template"
            )

        pair_length = len(pair_match[0][1])
        if not all(len(v) == pair_length for _, v in pair_match):
            raise InvalidRequestSpecError(
                "Not all template variables have same length for template"
            )

        def _var_template(key: str) -> str:
            return f"${{{key}}}"

        for i in range(pair_length):
            current_params = {key: values[i] for key, values in pair_match}

            # Deep copy matches and redactions
            spec = {**template}
            spec["responseMatches"] = [
                {**m} for m in (template.get("responseMatches") or [])
            ]
            spec["responseRedactions"] = [
                {**r} for r in (template.get("responseRedactions") or [])
            ]

            for match in spec["responseMatches"]:
                for key, value in current_params.items():
                    match["value"] = match["value"].replace(_var_template(key), value)

            for redaction in spec["responseRedactions"]:
                for key, value in current_params.items():
                    redaction["jsonPath"] = redaction.get("jsonPath", "").replace(
                        _var_template(key), value
                    )
                    redaction["xPath"] = redaction.get("xPath", "").replace(
                        _var_template(key), value
                    )
                    redaction["regex"] = redaction.get("regex", "").replace(
                        _var_template(key), value
                    )

            generated.append(spec)

    return generated


async def fetch_provider_hash_requirements_by(
    provider_id: str,
    provider_version: Optional[str] = None,
    allowed_tags: Optional[List[str]] = None,
    proofs: Optional[List[Proof]] = None,
) -> List[ValidationConfigWithHash]:
    """
    Fetches provider configs and computes hash requirements.
    Mirrors JS SDK's fetchProviderHashRequirementsBy.
    """
    result = await fetch_provider_configs(provider_id, provider_version, allowed_tags)

    try:
        provider_configs = result.get("providers", [])
        if not provider_configs:
            raise ProviderConfigFetchError(
                f"No provider configs found for providerId: {provider_id}"
            )

        template_params = _take_template_parameters_from_proofs(proofs)
        hash_requirements_list: List[ValidationConfigWithHash] = []

        for config in provider_configs:
            request_data = config.get("requestData", [])
            allowed_injected = config.get("allowedInjectedRequestData", [])
            generated_injected = _generate_specs_from_request_spec_template(
                allowed_injected, template_params
            )
            all_requests = request_data + generated_injected
            hashes = [_hash_request_spec(req) for req in all_requests]
            hash_requirements_list.append(ValidationConfigWithHash(hashes=hashes))

        return hash_requirements_list
    except (ProviderConfigFetchError, InvalidRequestSpecError):
        raise
    except Exception as e:
        raise ProviderConfigFetchError(
            f"Error fetching provider hash requirements for providerId: {provider_id}"
        )


async def assert_validate_proof(
    proofs: List[Proof],
    config: VerificationConfig,
) -> None:
    """
    Validates proof content against the provided configuration.
    Mirrors JS SDK's assertValidateProof.
    """
    if isinstance(config, ValidationConfigWithDisabledValidation):
        if config.dangerously_disable_content_validation:
            logger.warning("Validation skipped because it was disabled during proof verification")
            return

    if isinstance(config, ValidationConfigWithProviderInformation):
        if not config.provider_id or not isinstance(config.provider_id, str):
            raise ProofNotValidatedError("Provider id is required for proof validation")
        if config.provider_version and not isinstance(config.provider_version, str):
            raise ProofNotValidatedError("Provider version must be a string")

        hash_configs = await fetch_provider_hash_requirements_by(
            config.provider_id,
            config.provider_version,
            config.allowed_tags,
            proofs,
        )
        if not hash_configs:
            raise ProofNotValidatedError(
                "Could not find any provider information for the given provider id and version"
            )
        if len(hash_configs) != 1:
            last_error = None
            for hc in hash_configs:
                try:
                    return await assert_validate_proof(proofs, hc)
                except Exception as e:
                    last_error = e
            raise ProofNotValidatedError("Could not validate proof", last_error)
        else:
            return await assert_validate_proof(proofs, hash_configs[0])

    if isinstance(config, ValidationConfigWithHash):
        effective_hashes: List[HashRequirement] = []
        for h in config.hashes:
            if isinstance(h, str):
                effective_hashes.append(HashRequirement(value=h))
            else:
                effective_hashes.append(h)
        assert_valid_proofs_by_hash(proofs, effective_hashes)
        return

    raise ProofNotValidatedError("Invalid verification configuration")
