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

        reclaim_proof_request = await ReclaimProofRequest.init(app_id, app_secret, provider_id, options={'log': True})

        reclaim_proof_request.add_context('0x00000000000', 'Example context message')

        reclaim_proof_request.set_redirect_url('https://example.com/redirect')

        reclaim_proof_request.set_app_callback_url('https://webhook.site/29c6fff0-100c-4e34-8e28-5915f13a6aa4')

        request_url = await reclaim_proof_request.get_request_url()
        print(f"Request URL: {request_url}")



    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
