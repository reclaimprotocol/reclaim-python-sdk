import pytest


@pytest.fixture
def proof_data():
    """The same proof fixture used in JS SDK verify_proof.test.ts"""
    return {
        "identifier": "0xbb5c63656a650276728d3cb9ce3f90361223c7814fd94f6582b682dfc96e4ba8",
        "claimData": {
            "provider": "http",
            "parameters": '{"additionalClientOptions":{"popcornApiUrl":"https://popcorn-cluster-aws-us-east-2.popcorn.reclaimprotocol.org"},"body":"{\\"includeGroups\\":false,\\"includeLogins\\":false,\\"includeVerificationStatus\\":true}","geoLocation":"{{DYNAMIC_GEO}}","headers":{"Accept":"application/json","Accept-Language":"en-US,en;q=0.9","Sec-Ch-Ua":"\\"Not-A.Brand\\";v=\\"24\\", \\"Chromium\\";v=\\"146\\"","Sec-Ch-Ua-Mobile":"?0","Sec-Fetch-Mode":"same-origin","Sec-Fetch-Site":"same-origin","User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"},"method":"POST","paramValues":{"DYNAMIC_GEO":"IN","username":"srivatsanqb"},"proxySessionId":"1ab031c2ef","responseMatches":[{"type":"contains","value":"\\"userName\\":\\"{{username}}\\""}],"responseRedactions":[{"jsonPath":"$.userName","regex":"\\"userName\\":\\"(.*)\\"","xPath":""}],"url":"https://www.kaggle.com/api/i/users.UsersService/GetCurrentUser"}',
            "owner": "0x9c3dcb81fe10f6e494bfaa0220ea0ba7bcf3ad94",
            "timestampS": 1774346626,
            "context": '{"attestationNonce":"0xdf1cd84efbeded8c07d0fcdccc4883e74ecf5ed65eaf023d2aa1aafd75611f6c04eb1f633396ecbcc4f6fe9fc11c25586a4dac3a99deb40c44ae5cf49cebae6d1b","attestationNonceData":{"applicationId":"0xd116D518eacea61C7af9760E5d8D1b720a0CE8D5","sessionId":"1ab031c2ef","timestamp":"1774346557104"},"contextAddress":"0x0","contextMessage":"sample context","extractedParameters":{"DYNAMIC_GEO":"IN","username":"srivatsanqb"},"providerHash":"0x4c20776ae89ab7eead49e4e393f4e07348a4d85e21869201aa6eea6e2bc07f5b","reclaimSessionId":"1ab031c2ef"}',
            "identifier": "0xbb5c63656a650276728d3cb9ce3f90361223c7814fd94f6582b682dfc96e4ba8",
            "epoch": 1,
        },
        "witnesses": [
            {
                "id": "0x244897572368eadf65bfbc5aec98d8e5443a9072",
                "url": "wss://attestor.reclaimprotocol.org:444/ws",
            }
        ],
        "signatures": [
            "0x379b164165e005d75be4ec7854d745d68ad56d738a08da3a4c30eb071948bf5d0c7262bb8c46189e0cadb583dbb00917b73fbdbf74b5914eb69774ce97196a911c"
        ],
    }


@pytest.fixture
def kaggle_proof_data():
    """The proof fixture used in JS SDK proof-validation.test.ts"""
    return {
        "identifier": "0x51c192777d45010e9318c0e1eb2fefc0bc5a444f59e3d3e5a11e9a3d1b98e10c",
        "claimData": {
            "provider": "http",
            "parameters": '{"additionalClientOptions":{},"body":"{\\"includeGroups\\":false,\\"includeLogins\\":false,\\"includeVerificationStatus\\":true}","geoLocation":"{{DYNAMIC_GEO}}","headers":{"Accept":"application/json","Accept-Language":"en-US,en;q=0.9","Sec-Ch-Ua":"\\"Chromium\\";v=\\"145\\", \\"Not:A-Brand\\";v=\\"99\\"","Sec-Ch-Ua-Mobile":"?0","Sec-Fetch-Mode":"same-origin","Sec-Fetch-Site":"same-origin","User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"},"method":"POST","paramValues":{"DYNAMIC_GEO":"IN","username":"mushaheedsyed"},"proxySessionId":"8e825912c9","responseMatches":[{"type":"contains","value":"\\"userName\\":\\"{{username}}\\""}],"responseRedactions":[{"jsonPath":"$.userName","regex":"\\"userName\\":\\"(.*)\\"","xPath":""}],"url":"https://www.kaggle.com/api/i/users.UsersService/GetCurrentUser"}',
            "owner": "0x2967c5e6b3c4f179699bcc6e45bbe13b2203818e",
            "timestampS": 1773163350,
            "context": '{"contextAddress":"0x0","contextMessage":"sample context","extractedParameters":{"DYNAMIC_GEO":"IN","username":"mushaheedsyed"},"providerHash":"0x4c20776ae89ab7eead49e4e393f4e07348a4d85e21869201aa6eea6e2bc07f5b"}',
            "identifier": "0x51c192777d45010e9318c0e1eb2fefc0bc5a444f59e3d3e5a11e9a3d1b98e10c",
            "epoch": 1,
        },
        "witnesses": [
            {
                "id": "0x244897572368eadf65bfbc5aec98d8e5443a9072",
                "url": "wss://attestor.reclaimprotocol.org:444/ws",
            }
        ],
        "signatures": [
            "0x561d209c999536ad0c6b5834bb5416963a3d61b3045e621d99ba5e0a07aa1a7b0707a4e8f4a218c5dd13f9e470d3c7023b7ddeda5463069eb08c231dbb0ab63c1b"
        ],
    }
