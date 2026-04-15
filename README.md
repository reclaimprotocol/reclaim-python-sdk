# Reclaim Protocol Python SDK

Generate and verify Reclaim Protocol proofs from Python.

## Install

```bash
pip install reclaim-python-sdk
```

## Prerequisites

Get your credentials from the [Reclaim Developer Portal](https://dev.reclaimprotocol.org/):

- `APP_ID`
- `APP_SECRET`
- `PROVIDER_ID`

## Quick Start

### 1. Generate a proof request

```python
import asyncio
from reclaim_python_sdk import ReclaimProofRequest

async def main():
    proof_request = await ReclaimProofRequest.init(
        app_id="YOUR_APP_ID",
        app_secret="YOUR_APP_SECRET",
        provider_id="YOUR_PROVIDER_ID",
    )

    # Set the URL where proofs will be sent
    proof_request.set_app_callback_url("https://your-backend.com/receive-proofs")

    # URL to show as QR code / deep link to the user
    request_url = await proof_request.get_request_url()
    print(request_url)

asyncio.run(main())
```

#### Optional configuration

```python
# Add contextual data bound to the proof
proof_request.add_context("0x0", "login for example.com")

# Pre-fill known parameters
proof_request.set_params({"email": "user@example.com"})

# Redirect the user after verification
proof_request.set_redirect_url("https://your-app.com/success")

# Export/import the request (e.g., send to another service)
config = proof_request.to_json_string()
restored = await ReclaimProofRequest.from_json_string(config)
```

### 2. Receive and verify proofs

Any web framework works. Here's Flask:

```python
from flask import Flask, request, jsonify
from reclaim_python_sdk import verify_proof, Proof

app = Flask(__name__)

@app.post("/receive-proofs")
async def receive_proofs():
    proof = Proof.from_json(request.json)
    result = await verify_proof(proof, {"providerId": "YOUR_PROVIDER_ID"})

    if not result.is_verified:
        return jsonify({"error": str(result.error)}), 400

    return jsonify({
        "extracted_parameters": result.data[0].extracted_parameters,
    })
```

> `verify_proof` accepts a single proof OR a list of proofs:
> ```python
> await verify_proof(proof, config)      # single
> await verify_proof([p1, p2, p3], config)  # multiple
> ```

## `verify_proof` Config Options

### 1. By provider ID + version (recommended)

Pins verification to a specific provider version. Only `providerId` is required — `providerVersion` and `allowedTags` are optional (pass `[]` for empty tags):

```python
await verify_proof(proof, {
    "providerId": "YOUR_PROVIDER_ID",
    "providerVersion": "1.0.0",  # optional but recommended
    "allowedTags": ["ai"],        # optional, can be []
})
```

### 2. By provider ID only

Fetches the latest expected hashes from the Reclaim backend:

```python
await verify_proof(proof, {"providerId": "YOUR_PROVIDER_ID"})
```

### 3. By known hashes (no network calls)

Supply the expected hashes directly — no call to the Reclaim backend:

```python
await verify_proof(proof, {"hashes": ["0x1abc2def3456..."]})
```

### 4. Skip content validation

Only checks attestor signatures — does NOT validate the proof content:

```python
await verify_proof(proof, {"dangerouslyDisableContentValidation": True})
```

### Result shape

`verify_proof` always returns a result with:

| Field | Description |
|---|---|
| `is_verified` | `True` / `False` |
| `error` | `Exception` if failed, `None` if passed |
| `data` | List of `TrustedData` (context + extracted parameters) |
| `public_data` | Deduplicated public data from proofs |

## Testing

```bash
pip install pytest pytest-asyncio
pytest tests/
```

## Links

- [Documentation](https://docs.reclaimprotocol.org/)
- [Developer Portal](https://dev.reclaimprotocol.org/)
- [Security Policy](https://github.com/reclaimprotocol/.github/blob/main/SECURITY.md)
- [License](https://github.com/reclaimprotocol/.github/blob/main/LICENSE)

## Security

Never commit your `APP_SECRET` or expose it in client-side code.
