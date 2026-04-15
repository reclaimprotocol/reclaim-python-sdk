# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] — 2025-04-15

> **This release is published under a new PyPI name: `reclaimprotocol-python-sdk`.**
> Versions ≤ 1.0.3 are available as [`reclaim-python-sdk`](https://pypi.org/project/reclaim-python-sdk/) (no longer maintained).
>
> The import name remains `reclaim_python_sdk` — `from reclaim_python_sdk import ...` still works.

### Breaking changes

- `verify_proof(proof)` now requires a `config` argument: `verify_proof(proof, config)`.
  It returns a structured `VerifyProofResult` instead of a `bool`.
  The old signature is preserved as `verify_proof_deprecated(proof)` for backward compatibility.
  See [UPGRADING.md](./UPGRADING.md) for migration steps.

### Added

- New `verify_proof(proof, config)` API mirroring the [JS SDK's `verifyProof`](https://github.com/reclaimprotocol/reclaim-js-sdk).
- Three verification config modes:
  - **By provider ID** (recommended): `{"providerId": "...", "providerVersion": "1.0.0"}`
  - **By known hashes**: `{"hashes": ["0x..."]}`
  - **Skip content validation**: `{"dangerouslyDisableContentValidation": True}`
- New config dataclasses: `ValidationConfigWithHash`, `ValidationConfigWithProviderInformation`, `ValidationConfigWithDisabledValidation`.
- New result types: `VerifyProofResult`, `VerifyProofResultSuccess`, `VerifyProofResultFailure`, `TrustedData`.
- New error classes: `ProofNotValidatedError`, `ProviderConfigFetchError`, `UnknownProofsNotValidatedError`, `InvalidRequestSpecError`.
- Support for verifying a list of proofs: `verify_proof([p1, p2, p3], config)`.
- Template parameter substitution in provider configs (`generateSpecsFromRequestSpecTemplate` equivalent).
- Extra-proofs security check: rejects proofs that don't match any expected hash.
- Full test suite (30 tests) mirroring the JS SDK tests, runnable via `pytest`.

### Fixed

- **Security**: `create_sign_data_for_claim` now recomputes the identifier from `provider + parameters + context` instead of trusting the pre-stored `identifier` field, so tampering with context is detected.
- **Security**: `get_identifier_from_claim_info` now canonicalizes the context JSON before hashing (matches JS SDK), ensuring consistent identifiers across key orders.
- `hash_proof_claim_params` now returns `0x`-prefixed hashes (matches JS SDK output format).
- `HASH_MATCH_MULTIPLE_DEFAULT` changed from `False` to `True` to match JS SDK default.
- `requests.post` calls in `session_utils.py` now include `timeout=30` to prevent indefinite hangs.

### Changed

- Attestor list is now fetched from `{BACKEND_BASE_URL}/api/attestors` (previously used beacon/witness fetching via smart contract).
- `assert_verified_proof` now requires at least one attestor signature to match (previously required all witness signatures).

### Removed

- `asyncio` removed from `install_requires` — it's a stdlib module, not a pip package.

## [1.0.3] and earlier

Published as [`reclaim-python-sdk`](https://pypi.org/project/reclaim-python-sdk/). See that package's history for prior versions.

[2.0.0]: https://github.com/reclaimprotocol/reclaim-python-sdk/releases/tag/v2.0.0
