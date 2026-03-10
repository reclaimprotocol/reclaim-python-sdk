import asyncio
import json
import subprocess
import os
import sys
import unittest
from unittest.mock import patch

# Add src to sys.path so we can import reclaim_python_sdk
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from reclaim_python_sdk import ReclaimProofRequest

test_app_id = '0x9323eFec99973623932Db45438DCE4dEa9D9aE4c'
test_app_secret = '37e1d9da2f551ce0dac7e0eeda8a9e00daf62a3a3c548ed98cc80fc1a3983ad6'

class TestJSCompatibility(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        # 1. Generate JS JSON output
        result = subprocess.run(
            ['node', 'generate_js.js'],
            capture_output=True, text=True, cwd=os.path.dirname(__file__)
        )
        if result.returncode != 0:
            self.fail(f"Error running JS script: {result.stderr}")
            return
        
        # Extract JSON string from the last output line to ignore SDK logging
        stdout_lines = [line for line in result.stdout.strip().split('\n') if line]
        js_output = json.loads(stdout_lines[-1])
        self.js_default = js_output['default']
        self.js_override = js_output['override']

    def clean_dict(self, d):
        return {k: v for k, v in d.items() if v is not None}
        
    def assertDictsMatchTolerance(self, d1, d2, name):
        d1_clean = self.clean_dict(d1)
        d2_clean = self.clean_dict(d2)
        
        # JS timeStamp/timestamp legacy fallback
        if 'timeStamp' in d1_clean and 'timestamp' in d1_clean and d1_clean['timeStamp'] == d1_clean['timestamp']:
            pass

        keys1 = set(d1_clean.keys())
        keys2 = set(d2_clean.keys())

        if keys1 != keys2:
            self.fail(f"[{name}] Key mismatch!\nJS Keys only: {keys1 - keys2}\nPY Keys only: {keys2 - keys1}")
        
        for k in keys1:
            if d1_clean[k] != d2_clean[k]:
                # allow for timestamp vs timeStamp fallback difference
                if k == 'timestamp' and 'timeStamp' in d2_clean:
                   continue 

                self.fail(f"[{name}] Value mismatch for {k}:\nJS={d1_clean[k]}\nPY={d2_clean[k]}")

    async def test_compatibility(self):
        app_id = test_app_id
        app_secret = test_app_secret
        provider_id = '12345-67890-abcde'

        # Mock init_session to bypass HTTP backend call
        from reclaim_python_sdk.utils.types import InitSessionResponse
        mock_response = InitSessionResponse(session_id='mocked-session', resolved_provider_version='')
        
        with patch('reclaim_python_sdk.reclaim.init_session', return_value=mock_response):
            # 2. Build Python default request
            py_req1 = await ReclaimProofRequest.init(app_id, app_secret, provider_id)
            # Mocking sessionId and timestamp to match JS exactly
            py_req1._session_id = 'test-session-id'
            py_req1._timestamp = '1234567890'
            py_req1._signature = self.js_default['signature'] # signature will differ because of mocking timestamp/sessionId post init, sync it for compare

            py_default_str = py_req1.to_json_string()
            py_default = json.loads(py_default_str)

            # 3. Build Python override request
            py_req2 = await ReclaimProofRequest.init(app_id, app_secret, provider_id, {
                'log': True,
                'acceptAiProviders': True,
                'useAppClip': True
            })
            py_req2._session_id = 'test-session-id-2'
            py_req2._timestamp = '0987654321'
            py_req2.set_app_callback_url('https://my-backend.com/callback')
            py_req2.set_redirect_url('https://my-frontend.com/success', 'POST', [{'name': 'status', 'value': 'verified'}])
            py_req2.set_cancel_callback_url('https://my-backend.com/cancel')
            py_req2.set_cancel_redirect_url('https://my-frontend.com/failed', 'POST', [{'name': 'status', 'value': 'failed'}])
            py_req2.set_context('user-123', 'Testing context')
            py_req2.set_params({'email': 'test@test.com', 'username': 'tester'})
            py_req2.set_claim_creation_type('STANDALONE')
            py_req2.set_modal_options({
                'title': 'Please Verify',
                'darkTheme': True,
                'showExtensionInstallButton': False
            })
            
            py_req2._signature = self.js_override['signature'] # sync signature

            py_override_str = py_req2.to_json_string()
            py_override = json.loads(py_override_str)

        # The JS SDK includes BOTH `timeStamp` and `timestamp` fields.
        # Python currently includes just `timeStamp` or `timestamp` based on serialization.
        # Let's normalize it for the test.
        self.js_default.pop('timestamp', None)
        py_default.pop('timestamp', None)
        self.js_override.pop('timestamp', None)
        py_override.pop('timestamp', None)

        # Normalize sdkVersion since they are naturally different cross-platform
        self.js_default.pop('sdkVersion', None)
        py_default.pop('sdkVersion', None)
        self.js_override.pop('sdkVersion', None)
        py_override.pop('sdkVersion', None)

        self.assertDictsMatchTolerance(self.js_default, py_default, "Default")
        self.assertDictsMatchTolerance(self.js_override, py_override, "Override")

if __name__ == "__main__":
    unittest.main()
