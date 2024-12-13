# Reclaim Protocol Python SDK Integration Guide

This guide will walk you through integrating the Reclaim Protocol Python SDK into your application. We'll create a simple Python application that demonstrates how to use the SDK to generate proofs and verify claims.

## Prerequisites

Before we begin, make sure you have:

1. An application ID from Reclaim Protocol.
2. An application secret from Reclaim Protocol.
3. A provider ID for the specific service you want to verify.

You can obtain these details from the [Reclaim Developer Portal](https://dev.reclaimprotocol.org/).

## Step 1: Installation

You can install this package directly from GitHub using pip:

```bash
pip install reclaim-python-sdk
```

## Step 2: Basic Usage

Here's a simple example of how to use the SDK:

```python
from reclaim_sdk import ReclaimProofRequest
import asyncio

async def main():
    # Initialize the SDK
    APP_ID = 'YOUR_APPLICATION_ID_HERE'
    APP_SECRET = 'YOUR_APPLICATION_SECRET_HERE'
    PROVIDER_ID = 'YOUR_PROVIDER_ID_HERE'

    proof_request = await ReclaimProofRequest.init(
        app_id=APP_ID,
        app_secret=APP_SECRET,
        provider_id=PROVIDER_ID
    )

    # Get the request URL (for QR code generation)
    request_url = await proof_request.get_request_url()
    print(f"Request URL: {request_url}")

    # Get the status URL
    status_url = proof_request.get_status_url()
    print(f"Status URL: {status_url}")


if __name__ == "__main__":
    asyncio.run(main())
```

## Understanding the Code

Let's break down what's happening in this code:

1. We initialize the Reclaim SDK with your application ID, secret, and provider ID.

2. We generate a request URL using `get_request_url()`. This URL can be used to create a QR code.

3. We get the status URL using `get_status_url()`. This URL can be used to check the status of the claim process.


## Advanced Configuration

The Reclaim Python SDK offers several advanced options to customize your integration:

1. **Adding Context**:

   ```python
   proof_request.add_context('0x00000000000', 'Example context message')
   ```

2. **Setting Parameters**:

   ```python
   proof_request.set_params({
       'email': 'test@example.com',
       'userName': 'testUser'
   })
   ```

3. **Custom Redirect URL**:

   ```python
   proof_request.set_redirect_url('https://example.com/redirect')
   ```

4. **Custom Callback URL**:

   ```python
   proof_request.set_app_callback_url('https://example.com/callback')
   ```

5. **Exporting and Importing SDK Configuration**:

   ```python
   # Export configuration
   config_json = proof_request.to_json_string()
   print('Exportable config:', config_json)
   
   # Import configuration
   imported_request = ReclaimProofRequest.from_json_string(config_json)
   request_url = await imported_request.get_request_url()
   ```

## Complete Example

Here's a more complete example showing various features:

```python
from reclaim_sdk import ReclaimProofRequest
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

For production applications, it's recommended to handle proofs on your backend:

1. Set a callback URL:

   ```python
   proof_request.set_callback_url('https://your-backend.com/receive-proofs')
   ```

2. Create an endpoint on your backend to receive proofs:

   ```python
   from flask import Flask, request
   
   app = Flask(__name__)
   
   @app.route('/receive-proofs', methods=['POST'])
   def receive_proofs():
       proofs = request.json
       # Process the proofs
       return {'status': 'success'}
   ```

## Next Steps

Explore the [Reclaim Protocol documentation](https://docs.reclaimprotocol.org/) for more advanced features and best practices for integrating the SDK into your production applications.

Happy coding with Reclaim Protocol!

## Contributing to Our Project

We welcome contributions to our project! If you find any issues or have suggestions for improvements, please open an issue or submit a pull request.

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
