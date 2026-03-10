<div>
    <div>
        <img src="https://raw.githubusercontent.com/reclaimprotocol/.github/main/assets/banners/Python-SDK.png"  />
    </div>
</div>

# Reclaim Protocol Python SDK Integration Guide

This guide will walk you through integrating the Reclaim Protocol Python SDK into your application. We'll explore how to configure provider requests securely on your Python backend, export configurations to your frontend, and verify cryptographic proofs natively.

[Official documentation](https://docs.reclaimprotocol.org/)

## Prerequisites

Before we begin, make sure you have:

1. An application ID from Reclaim Protocol.
2. An application secret from Reclaim Protocol.
3. A provider ID for the specific service you want to verify.

You can obtain these details from the [Reclaim Developer Portal](https://dev.reclaimprotocol.org/).

## Step 1: Installation

You can install this package via pip:

```bash
pip install reclaim-python-sdk
```

## Step 2: Basic Usage

Here's a simple example of how to use the SDK in a basic Python script:

```python
import asyncio
from reclaim_python_sdk import ReclaimProofRequest

async def main():
    APP_ID = "YOUR_APPLICATION_ID_HERE"
    APP_SECRET = "YOUR_APPLICATION_SECRET_HERE"
    PROVIDER_ID = "YOUR_PROVIDER_ID_HERE"

    reclaim_proof_request = await ReclaimProofRequest.init(APP_ID, APP_SECRET, PROVIDER_ID)
    
    request_url = await reclaim_proof_request.get_request_url()
    print("Let users scan this as QR code or open this URL to start the verification process:", request_url)

    # Get the status URL to poll for completion
    status_url = reclaim_proof_request.get_status_url()
    print("Status URL:", status_url)

if __name__ == "__main__":
    asyncio.run(main())
```

## Step 3: Understanding the code

Let's break down what's happening in this code:

1. We initialize the Reclaim SDK with your application ID, secret, and provider ID. 

2. We generate a request URL using `get_request_url()`. This URL is used to create the QR code or link the user needs to visit.

3. We get the status URL using `get_status_url()`. This URL can be used to check the status of the claim process programmatically or poll for completion.

## Step 4: Streamlined Flow with JS SDK Frontend

> **Note**: The automated `triggerReclaimFlow()` method that handles verification platform detection (browser extensions, App Clips, QR Codes) natively is **only supported from the `@reclaimprotocol/js-sdk` on the frontend**. 

However, you can configure all options securely on your Python backend, export the configuration, and pass it to your frontend JavaScript application to trigger the flow seamlessly! You can even customize these options on frontend.

### Exporting from Python Backend:

```python
# Configure request securely on Python backend
proof_request = await ReclaimProofRequest.init(APP_ID, APP_SECRET, PROVIDER_ID, {
    "useBrowserExtension": True,
    "log": True
})

# Securely set up webhook endpoints that verify completions directly
proof_request.set_app_callback_url('https://api.your-backend.com/callback')
proof_request.set_cancel_callback_url('https://api.your-backend.com/cancel-callback')

# Export JSON to send back to the frontend browser
config_json = proof_request.to_json_string()
return {"config": config_json}
```

### Importing and Triggering on JS Frontend:

```javascript
import { ReclaimProofRequest } from "@reclaimprotocol/js-sdk";

// Receive config_json from your Python API
const proofRequest = await ReclaimProofRequest.fromJsonString(config_json);

// Trigger the verification flow automatically targeting extensions, mobile apps, or fallback QR codes
await proofRequest.triggerReclaimFlow();
```


## Understanding the Claim Process

1. **Creating a Request**: When you call `init()`, the SDK generates a unique request for verification targeting the specific Provider.

2. **Request URL**: The payload instructions. When evaluated by the frontend or scanned via QR code, it initiates the verification workflow.

3. **Status URL**: This URL can be used to check the status of the claim process manually if polling over REST.

4. **Verification**: When using a custom callback url (recommended for backends), the generated proof is pushed directly via HTTP rather than polling.

## Advanced Configuration

The Reclaim Python SDK offers advanced configuration parity matching 1-to-1 with the JS SDK:

1. **Adding Context**:
   You can add context to your proof request, which can be useful for providing additional information tied to the generated proof:

   ```python
   proof_request.set_context("0x00000000000", "Example context message")
   
   # Or using dictionary mapping
   proof_request.set_json_context({"userId": 12345, "intent": "KYC"})
   ```

2. **Setting Parameters**:
   If your provider requires specific parameters to be injected:

   ```python
   proof_request.set_params({ "email": "test@example.com", "userName": "testUser" })
   ```

3. **Custom Redirect URL**:
   Set a custom URL to redirect users after the verification process.

   ```python
   proof_request.set_redirect_url("https://example.com/redirect")
   ```

   Redirection with method and body payload (*Note: form POST redirection is only actively supported when handled by the In-Browser JS SDK frontend*):

   ```python
   proof_request.set_redirect_url(
     "https://example.com/redirect",
     "POST",
     [{"name": "status", "value": "success"}]
   )
   ```

4. **Custom Cancel Redirect URL**:
   Set a custom URL to redirect users on a cancellation which aborts the verification process.
  
   ```python
   proof_request.set_cancel_redirect_url("https://example.com/error-redirect")
   ```

5. **Custom Callback URL**:
   For production applications, it's recommended to handle proofs on your backend:

   Set a custom callback URL for your app which allows you to receive proofs and status updates securely on your backend webhook:
   
   **Note**: When a custom callback URL is set, proofs are sent to the custom URL *instead* of polling directly.

   ```python
   proof_request.set_app_callback_url("https://api.example.com/callback")
   ```

6. **Custom Error Callback URL**:
   Set a custom cancel callback URL for your app which allows you to receive user or provider-initiated cancellations on your callback URL:

   ```python
   proof_request.set_cancel_callback_url("https://api.example.com/error-callback")
   ```

7. **Modal Customization for Desktop Users (Frontend applied)**:
   Customize the appearance and behavior of the QR code modal shown to desktop users when using the JS SDK frontend:

   ```python
   proof_request.set_modal_options({
     "title": "Verify Your Account",
     "description": "Scan the QR code with your mobile device or install our browser extension",
     "darkTheme": False,
     "extensionUrl": "https://chrome.google.com/webstore/detail/reclaim"
   })
   ```

8. **Browser Extension Configuration (Frontend applied)**:
   Configure browser extension behavior:

   ```python
   proof_request = await ReclaimProofRequest.init(APP_ID, APP_SECRET, PROVIDER_ID, {
     "useBrowserExtension": True, 
     "extensionID": "custom-extension-id",
     "useAppClip": True,
     "log": True
   })
   ```

9. **Custom Share Page and App Clip URLs**:
   You can customize the share page and app clip URLs for your app:

   ```python
   proof_request = await ReclaimProofRequest.init(APP_ID, APP_SECRET, PROVIDER_ID, {
     "customSharePageUrl": "https://your-custom-domain.com/verify",
     "customAppClipUrl": "https://appclip.apple.com/id?p=your.custom.app.clip"
   })
   ```

10. **Exporting and Importing SDK Configuration**:
   You can export the entire Reclaim SDK configuration as a JSON string and use it to initialize the SDK with the exact same configuration on a different service or language (like the JS SDK frontend):

   ```python
   # Export to JSON
   config_json = proof_request.to_json_string()
   print('Exportable config:', config_json)
   
   # Import from JSON
   imported_request = await ReclaimProofRequest.from_json_string(config_json)
   request_url = await imported_request.get_request_url()
   ```

11. **Utility Methods**:
    Additional utility methods for managing your proof requests:

    ```python
    # Get the current session ID
    session_id = proof_request.get_session_id()
    ```

12. **Control auto-submission of proofs**:
    Whether the verification client should automatically submit necessary proofs once they are generated. If set to false, the user must manually click a button to submit. Defaults to True.

    ```python
    proof_request = await ReclaimProofRequest.init(APP_ID, APP_SECRET, PROVIDER_ID, {
      "canAutoSubmit": True
    })
    ```

13. **Add additional metadata for verification client**:
    Additional metadata to pass to the verification client. 

    ```python
    proof_request = await ReclaimProofRequest.init(APP_ID, APP_SECRET, PROVIDER_ID, {
      "metadata": { "theme": "dark" }
    })
    ```

14. **Set preferred locale for verification client**:
    An identifier used to select a user's language and formatting preferences.

    ```python
    proof_request = await ReclaimProofRequest.init(APP_ID, APP_SECRET, PROVIDER_ID, {
      "preferredLocale": "en-US"
    })
    ```

## Complete Example

Here's a more complete example showing various features:

```python
from reclaim_python_sdk import ReclaimProofRequest
import asyncio
import qrcode

async def main():
    # Initialize SDK
    proof_request = await ReclaimProofRequest.init(
        app_id='YOUR_APP_ID',
        app_secret='YOUR_APP_SECRET',
        provider_id='YOUR_PROVIDER_ID'
    )

    # Configure the request
    proof_request.add_context('0x00000000000', 'Example context')
    proof_request.set_params({'email': 'test@example.com'})
    proof_request.set_redirect_url('https://example.com/redirect')
    proof_request.set_app_callback_url('https://example.com/callback')

    # Get request URL
    request_url = await proof_request.get_request_url()


if __name__ == "__main__":
    asyncio.run(main())
```

## Handling Proofs on Your Backend

For production applications, it's highly recommended to handle proofs and cancellations securely on your backend server by utilizing webhook callbacks.

1. Set a callback URL:
   ```python
   proof_request.set_app_callback_url("https://your-backend.com/receive-proofs")
   ```

2. Set a cancel callback URL:
   ```python
   proof_request.set_cancel_callback_url("https://your-backend.com/receive-cancel")
   ```

> [!TIP]
> **Best Practice:** When using `set_app_callback_url` and/or `set_cancel_callback_url`, your backend receives the proof or cancellation details directly via a POST request from the Reclaim Protocol infrastructure. We recommend your backend then notifies your frontend (e.g. via WebSockets, SSE, or polling) to handle the appropriate success/failure action natively.

## Proof Verification

1. Create an endpoint on your backend to receive proofs:

   ```python
    from flask import Flask, request, jsonify
    from reclaim_python_sdk import ReclaimProofRequest, verify_proof, Proof
    import json

    app = Flask(__name__)

    @app.route('/receive-proofs', methods=['POST'])
    async def receive_proofs():
        proof_payload = request.get_json(silent=True)
        if not proof_payload:
            return jsonify({'status': 'error', 'message': 'Invalid JSON payload'}), 400

        is_verified = await handle_proof_webhook(proof_payload)
        print(f"Verified: {is_verified}")

        if not is_verified:
            return jsonify({'status': 'error', 'verified': is_verified}), 403

        return jsonify({'status': 'success', 'verified': is_verified}), 200
   ```

2. The SDK provides a `verify_proof` function to mathematically verify proofs received on your backend to ensure tampering hasn't occurred:

```python
from reclaim_python_sdk import verify_proof, Proof

# Inside your webhook / receive-proofs endpoint
async def handle_proof_webhook(proof_json_request):
    proof = Proof.from_json(proof_json_request)
    
    try:
      # Verify a single proof or array of proofs
    is_valid = await verify_proof(proof)
    
    if is_valid:
        print("Proof is valid and was signed by Reclaim Protocol attestors!")
        return True
    else:
        print("Proof is invalid or signatures failed verification.")
        return False
    except Exception as e:
        print(f"Error verifying proof: {e}")
        return False
```

The `verify_proof` function:
- Accepts either a single proof or a list of proofs
- Returns a boolean indicating if the proof(s) are valid
- Verifies signatures against the dynamic Reclaim Protocol global attestors
- Checks witness integrity and claim data

## Error Handling

When interacting locally or manually listening via `start_session`, exceptions may arise:

- `InitError`: SDK initialization failed
- `InvalidParamError`: Invalid parameters provided
- `ConvertToJsonStringError`: Failed serializing object representation

## Next Steps

Explore the [Reclaim Protocol documentation](https://docs.reclaimprotocol.org/) for more advanced features and best practices for integrating the SDK into your production applications.

Happy coding with Reclaim Protocol!

## Contributing to Our Project

We welcome contributions to our project! If you find any issues or have suggestions for improvements, please open an issue or submit a pull request.

### Setting up build and deployment tools

Install via pip:

```bash
python -m pip install --upgrade build twine
```

## Security Note

Always keep your Application Secret secure. Never expose it in client-side code or public repositories.

## Code of Conduct

Please read and follow our [Code of Conduct](https://github.com/reclaimprotocol/.github/blob/main/Code-of-Conduct.md) to ensure a positive and inclusive environment for all contributors.

## Security

If you discover any security-related issues, please refer to our [Security Policy](https://github.com/reclaimprotocol/.github/blob/main/SECURITY.md) for information on how to responsibly disclose vulnerabilities.

## Contributor License Agreement

Before contributing to this project, please read and sign our [Contributor License Agreement (CLA)](https://github.com/reclaimprotocol/.github/blob/main/CLA.md).

## Indie Hackers

For Indie Hackers: [Check out our guidelines and potential grant opportunities](https://github.com/reclaimprotocol/.github/blob/main/Indie-Hackers.md)

## License

This project is licensed under a [custom license](https://github.com/reclaimprotocol/.github/blob/main/LICENSE). By contributing to this project, you agree that your contributions will be licensed under its terms.

Thank you for your contributions!
