# Adding the converted constants from Dart
BACKEND_BASE_URL = 'https://api.reclaimprotocol.org'
DEFAULT_RECLAIM_CALLBACK_URL = f'{BACKEND_BASE_URL}/api/sdk/callback?callbackId='
DEFAULT_RECLAIM_STATUS_URL = f'{BACKEND_BASE_URL}/api/sdk/session/'
RECLAIM_SHARE_URL = 'https://share.reclaimprotocol.org/verifier/?template='
DEFAULT_ATTESTORS_URL = f'{BACKEND_BASE_URL}/api/attestors'


def get_provider_configs_url(provider_id: str, version: str = '', allowed_tags: str = ''):
    return f'{BACKEND_BASE_URL}/api/providers/{provider_id}/configs?versionNumber={version}&allowedTags={allowed_tags}'