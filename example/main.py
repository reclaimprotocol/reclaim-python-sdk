import os
from dotenv import load_dotenv
from src.reclaim import ReclaimProofRequest
import asyncio

# Load environment variables from .env file
load_dotenv()


async def main():
    # Retrieve app ID and other details from environment variables
    try:
        app_id = os.getenv("APP_ID")
        app_secret = os.getenv("APP_SECRET")
        provider_id = os.getenv("PROVIDER_ID")

        print(f"App ID: {app_id}")
        print(f"App Secret: {app_secret}")
        print(f"Provider ID: {provider_id}")

        # reclaim_proof_request = await ReclaimProofRequest.init(app_id, app_secret, provider_id, options={'log': True})

        # reclaim_proof_request.add_context('0x00000000000', 'Example context message')

        # reclaim_proof_request.set_redirect_url('https://example.com/redirect')

        # reclaim_proof_request.set_app_callback_url('https://webhook.site/29c6fff0-100c-4e34-8e28-5915f13a6aa4')

        # reclaim_config = reclaim_proof_request.to_json_string()

        reclaim_config_str = '{"applicationId": "0xAFddDF4fBb8F158B52609e237aFfA909D2310bA1", "providerId": "c94476a0-8a75-4563-b70a-bf6124d7c59b", "sessionId": "e7311016-425f-4cf6-98ff-8ca86fab8394", "context": {"contextAddress": "0x00000000000", "contextMessage": "Example context message"}, "requestedProof": {"url": "https://www.kaggle.com/api/i/users.UsersService/GetCurrentUser", "parameters": {"username": ""}}, "appCallbackUrl": "https://webhook.site/29c6fff0-100c-4e34-8e28-5915f13a6aa4", "signature": "0x69b13a12c3c9c4f1569c7d3b2a702658e58fdd0aa28d5845b2668b083600e9440bdb02034c3165e6fcb41326881e30fb9868d30214d74dedeb1099b372d3a8b51b", "redirectUrl": "https://example.com/redirect", "timeStamp": "1732867514506", "options": {"log": true}, "sdkVersion": "1.0.0"}'

        reclaim_proof_request = await ReclaimProofRequest.from_json_string(
            reclaim_config_str
        )

        request_url = await reclaim_proof_request.get_request_url()

        # Start the session
        def on_success(proofs):
            if isinstance(proofs, str):
                # When using a custom callback url
                print('SDK Message:', proofs)
            else:
                # When using default callback
                print('Proof received:', proofs.claim_data.context)

        def on_failure(error):
            print('Verification failed:', error)

        await reclaim_proof_request.start_session(
            on_success=on_success,
            on_error=on_failure
        )

        print(f"Request URL: {request_url}")

    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
