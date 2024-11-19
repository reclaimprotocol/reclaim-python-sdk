import asyncio
from src.reclaim import verify_proof
from src.utils.interfaces import ProviderClaimData, Proof

async def main():
    # Create a proof object with the provided JSON data
    # sample_proof = Proof(
    #     identifier="0x05744d72f0489b0680bfb44812394c2eca627f857b770ee38dcae360096352fa",
    #     signatures=[
    #         "0xeabe4987faea592d0a85938eae1b6391f5e3972e4993f9ade830d89ad17530b30a042ef8f3b5a84c8d7fcbd23c019647a4b7fb17c2a4f1d6c88ce3ddda239aa21c"
    #     ],
    #     claimData=ProviderClaimData(
    #         provider="http",
    #         parameters="{\"additionalClientOptions\":{},\"body\":\"{\\\"includeGroups\\\":false,\\\"includeLogins\\\":false,\\\"includeVerificationStatus\\\":true}\",\"geoLocation\":\"\",\"headers\":{\"Referer\":\"https://www.kaggle.com/\",\"Sec-Fetch-Mode\":\"same-origin\",\"User-Agent\":\"Mozilla/5.0 (Linux; Android 13; M2101K6P Build/TKQ1.221013.002) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/130.0.6723.106 Mobile Safari/537.36\",\"accept\":\"application/json\"},\"method\":\"POST\",\"paramValues\":{\"email\":\"providers@creatoros.co\",\"userName\":\"providerreclaim\"},\"responseMatches\":[{\"invert\":false,\"type\":\"contains\",\"value\":\"\\\"email\\\":\\\"{{email}}\\\"\"},{\"invert\":false,\"type\":\"contains\",\"value\":\"\\\"userName\\\":\\\"{{userName}}\\\"\"}],\"responseRedactions\":[{\"jsonPath\":\"$.email\",\"regex\":\"\\\"email\\\":\\\"(.*)\\\"\",\"xPath\":\"\"},{\"jsonPath\":\"$.userName\",\"regex\":\"\\\"userName\\\":\\\"(.*)\\\"\",\"xPath\":\"\"}],\"url\":\"https://www.kaggle.com/api/i/users.UsersService/GetCurrentUser\"}",
    #         owner="0xab3f277949804480cfcb4dd695938cb630ab4cc2",
    #         timestampS=1731468498,
    #         identifier="0x05744d72f0489b0680bfb44812394c2eca627f857b770ee38dcae360096352fa",
    #         context="{\"contextAddress\":\"0x00000000000\",\"contextMessage\":\"Example context message\",\"extractedParameters\":{\"email\":\"providers@creatoros.co\",\"userName\":\"providerreclaim\"},\"providerHash\":\"0x59f7ca945580a9570e9988a11f5683e9ba95a9445141b34200de4a96f648544a\"}",
    #         epoch=1
    #     ),
    #     witnesses=[
    #         {
    #             "url": "wss://witness.reclaimprotocol.org/ws",
    #             "id": "0x244897572368eadf65bfbc5aec98d8e5443a9072"
    #         }
    #     ],
    #     publicData={}
    # )

    try:
        # Verify the proof
        sample_proof = 'Proof object here'
        is_valid = await verify_proof(sample_proof)
        print(f"Proof verification result: {is_valid}")
    except Exception as e:
        print(f"Error verifying proof: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
