# Upgrading Guide

## Upgrading from `reclaim-python-sdk` 1.x to `reclaimprotocol-python-sdk` 2.0.0

### 1. Update your install

```bash
pip uninstall reclaim-python-sdk
pip install reclaimprotocol-python-sdk
```

### 2. Imports stay the same

Your existing imports still work — the Python module name did not change:

```python
from reclaim_python_sdk import ReclaimProofRequest, verify_proof, Proof
```

### 3. `verify_proof` — breaking change

The signature and return type changed.

#### Before (v1.x)

```python
is_verified: bool = await verify_proof(proof)

if is_verified:
    ...
```

#### After (v2.0.0)

```python
result = await verify_proof(proof, {"providerId": "YOUR_PROVIDER_ID"})

if result.is_verified:
    username = result.data[0].extracted_parameters["username"]
    ...
else:
    print(f"Invalid: {result.error}")
```

#### Quick migration — keep the old behavior

If you want the old behavior temporarily:

```python
from reclaim_python_sdk import verify_proof_deprecated

is_verified: bool = await verify_proof_deprecated(proof)
```

`verify_proof_deprecated` is kept for backward compatibility, but new code should use `verify_proof(proof, config)`.

### 4. Pick a verification config

| Scenario | Config |
|---|---|
| Normal backend verification (recommended) | `{"providerId": "...", "providerVersion": "1.0.0"}` |
| Offline / pre-computed hash | `{"hashes": ["0x..."]}` |
| Only verify signatures (skip content check) | `{"dangerouslyDisableContentValidation": True}` |

See [README.md](./README.md#verify_proof-config-options) for details.

### 5. Return value changes

| Before (v1.x) | After (v2.0.0) |
|---|---|
| `bool` (True/False) | `VerifyProofResult` object |
| — | `.is_verified` (bool) |
| — | `.error` (Exception or None) |
| — | `.data[i].extracted_parameters` (dict) |
| — | `.data[i].context` (dict) |
| — | `.public_data` (list) |

### 6. Why the change?

The new API matches the [JS SDK's `verifyProof`](https://github.com/reclaimprotocol/reclaim-js-sdk). This makes it:

- **Safer** — explicit config forces you to think about what you're validating.
- **Richer** — you get extracted data, context, and error details, not just a bool.
- **Cross-language consistent** — same behavior and semantics as the JS SDK.
