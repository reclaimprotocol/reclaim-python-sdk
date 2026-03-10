const { ReclaimProofRequest } = require('@reclaimprotocol/js-sdk');

// Mock fetch globally to prevent InitSessionError and Application not found
global.fetch = async (...args) => {
    return {
        ok: true,
        status: 200,
        json: async () => ({ sessionId: 'mocked-session', providerId: '123' }),
        text: async () => '{"sessionId": "mocked-session", "providerId": "123"}'
    };
};

const test_app_id = '0x9323eFec99973623932Db45438DCE4dEa9D9aE4c'
const test_app_secret = '37e1d9da2f551ce0dac7e0eeda8a9e00daf62a3a3c548ed98cc80fc1a3983ad6'

async function main() {
    const appId = test_app_id;
    const appSecret = test_app_secret;
    const providerId = '12345-67890-abcde';

    // 1. Override Nothing
    const req1 = await ReclaimProofRequest.init(appId, appSecret, providerId);
    // Overriding session ID and timestamp to make comparisons deterministic
    req1.sessionId = 'test-session-id';
    req1.timeStamp = '1234567890';
    const json1 = req1.toJsonString();

    // 2. Override Everything
    const req2 = await ReclaimProofRequest.init(appId, appSecret, providerId, { log: true, acceptAiProviders: true, useAppClip: true });
    req2.sessionId = 'test-session-id-2';
    req2.timeStamp = '0987654321';
    req2.setAppCallbackUrl('https://my-backend.com/callback');
    req2.setRedirectUrl('https://my-frontend.com/success', 'POST', [{ name: 'status', value: 'verified' }]);
    req2.setCancelCallbackUrl('https://my-backend.com/cancel');
    req2.setCancelRedirectUrl('https://my-frontend.com/failed', 'POST', [{ name: 'status', value: 'failed' }]);
    req2.setContext('user-123', 'Testing context');
    req2.setParams({ email: 'test@test.com', username: 'tester' });
    req2.setClaimCreationType('STANDALONE');
    req2.setModalOptions({
        title: 'Please Verify',
        darkTheme: true,
        showExtensionInstallButton: false
    });

    const json2 = req2.toJsonString();

    console.log(JSON.stringify({ default: JSON.parse(json1), override: JSON.parse(json2) }));
}

main().catch(console.error);
