import json
import requests
import asyncio
from .errors import InitSessionError, UpdateSessionError, StatusUrlError
from .types import InitSessionResponse, Session, UpdateSessionResponse, StatusUrlResponse, ProviderData
from .validation_utils import validate_function_params
from .constants import BACKEND_BASE_URL, DEFAULT_RECLAIM_STATUS_URL
from .logger import logger

async def init_session(provider_id: str, app_id: str, timestamp: str, signature: str) -> InitSessionResponse:
    logger.info(f'Initializing session for providerId: {provider_id}, appId: {app_id}')
    try:
        response = requests.post(
            f'{BACKEND_BASE_URL}/api/sdk/init-session/',
            headers={'Content-Type': 'application/json'},
            data=json.dumps({
                'providerId': provider_id,
                'appId': app_id,
                'timestamp': timestamp,
                'signature': signature,
            })
        )

        res = response.json()

        if response.status_code != 201:
            logger.info(f'Session initialization failed: {res.get("message", "Unknown error")}')
            raise InitSessionError(res.get('message', f'Error initializing session with providerId: {provider_id}'))
        
        return InitSessionResponse.from_json(res)
    except Exception as err:
        logger.info({
            'message': 'Failed to initialize session',
            'providerId': provider_id,
            'appId': app_id,
            'timestamp': timestamp,
            'error': str(err),
        })
        raise

async def update_session(session_id, status):
    logger.info(f'Updating session status for sessionId: {session_id}, new status: {status}')
    validate_function_params([
        {'input': session_id, 'param_name': 'sessionId', 'is_string': True}
    ], 'update_session')

    try:
        response = requests.post(
            f'{BACKEND_BASE_URL}/api/sdk/update/session/',
            headers={'Content-Type': 'application/json'},
            data=json.dumps({'sessionId': session_id, 'status': status})
        )

        res = response.json()

        if response.status_code != 200:
            error_message = f'Error updating session with sessionId: {session_id}. Status Code: {response.status_code}'
            logger.info(f'{error_message}\n{res}')
            raise UpdateSessionError(error_message)

        logger.info(f'Session status updated successfully for sessionId: {session_id}')
        return UpdateSessionResponse(message=res['message'])
    except Exception as err:
        error_message = f'Failed to update session with sessionId: {session_id}'
        logger.info(f'{error_message}\n{str(err)}')
        raise UpdateSessionError(f'Error updating session with sessionId: {session_id}')

async def fetch_status_url(session_id: str) -> StatusUrlResponse:
    try:
        validate_function_params([
            {'input': session_id, 'param_name': 'sessionId', 'is_string': True}
        ], 'fetch_status_url')

        response = requests.get(
            f'{DEFAULT_RECLAIM_STATUS_URL}{session_id}',
            headers={'Content-Type': 'application/json'}
        )

        res = response.json()
        
        
        if response.status_code != 200:
            logger.info(f'Error fetching status URL for sessionId: {session_id}. Status Code: {response.status_code}')
            raise StatusUrlError(f'Error fetching status URL for sessionId: {session_id}')

        return StatusUrlResponse.from_json(res)
    except Exception as err:
        logger.info(f'Failed to fetch status URL for sessionId: {session_id}')
        raise StatusUrlError(f'Error fetching status URL for sessionId: {session_id}')
