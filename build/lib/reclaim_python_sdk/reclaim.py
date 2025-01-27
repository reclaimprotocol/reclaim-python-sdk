import asyncio
import json
import time
from json_canonical import canonicalize
from sha3 import keccak_256
from typing import Dict, List, Optional, Any, Union, Callable, AsyncIterator
from eth_account import Account
from eth_account.messages import encode_defunct
from web3 import Web3
from .utils.interfaces import (
    Proof,
    Context,
    ProviderClaimData,
    ProviderData,
    RequestedProof,
)
from .utils.types import ClaimInfo, SignedClaim, SessionStatus

from .utils.constants import DEFAULT_RECLAIM_CALLBACK_URL, DEFAULT_RECLAIM_STATUS_URL

from .utils.session_utils import init_session, update_session
from .utils.proof_utils import generate_requested_proof, get_filled_parameters, create_link_with_template_data
from .utils.validation_utils import validate_signature



from .utils.errors import (
    GetRequestUrlError,
    InitError,
    SetSignatureError,
    SignatureGeneratingError,
    SignatureNotFoundError,
    ProofNotVerifiedError,
    SessionNotStartedError,
    GetAppCallbackUrlError,
    GetStatusUrlError,
    SetAppCallbackUrlError,
    SetRedirectUrlError,
    AddContextError,
    SetParamsError,
    NoProviderParamsError,
    GetRequestedProofError,
    BuildProofRequestError,
    ConvertToJsonStringError,
    InvalidParamError,
    AvailableParamsError,
)

from .utils.proof_utils import assert_valid_signed_claim, get_witnesses_for_claim

from .witness import get_identifier_from_claim_info

from .utils.logger import LogLevel, Logger

from asyncio import Task

logger = Logger()


async def verify_proof(proof: Union[Proof, List[Proof]]) -> bool:
    """
    Verify a proof or array of proofs by checking signatures and witness data

    Args:
        proof (Union[Proof, List[Proof]]): Single proof object or list of proof objects to verify

    Returns:
        bool: True if all proofs are valid, False if any proof is invalid

    Raises:
        SignatureNotFoundError: If no signatures are present in a proof
    """
    # Handle array of proofs recursively
    logger.info(f"Verifying proof: {proof}")
    if isinstance(proof, list):
        for single_proof in proof:
            if not await verify_proof(single_proof):
                return False
        return True

    # Handle single proof (existing logic)
    if not proof.signatures:
        raise SignatureNotFoundError("No signatures")

    try:
        # Check if witness array exists and first element is manual-verify
        witnesses = []
        if proof.witnesses and proof.witnesses[0].get("url") == "manual-verify":
            witnesses.append(proof.witnesses[0]["id"])
        else:
            witnesses = await get_witnesses_for_claim(
                proof.claimData.epoch, proof.identifier, proof.claimData.timestampS
            )

        claim_data = ClaimInfo(
            parameters=proof.claimData.parameters,
            provider=proof.claimData.provider,
            context=proof.claimData.context,
        )

        calculated_identifier = get_identifier_from_claim_info(claim_data)

        # Remove quotes from identifier for comparison
        proof.identifier = proof.identifier.replace('"', "")

        # Check if identifiers match
        if calculated_identifier != proof.identifier:
            raise ProofNotVerifiedError("Identifier Mismatch")

        claim_data: ProviderClaimData = proof.claimData
        signed_claim = SignedClaim(
            claim=claim_data,
            signatures=[
                bytes.fromhex(sig.replace("0x", "")) for sig in proof.signatures
            ],
        )

        assert_valid_signed_claim(signed_claim, witnesses)

    except Exception as e:
        logger.info(f"Error verifying proof: {str(e)}")
        return False

    return True


def transform_for_onchain(proof: Proof) -> Dict[str, Any]:
    """
    Transform proof data into onchain format

    Args:
        proof (Proof): The proof to transform

    Returns:
        Dict[str, Any]: Transformed proof data for onchain use
    """
    claim_info = {
        "context": proof.claimData.context,
        "parameters": proof.claimData.parameters,
        "provider": proof.claimData.provider,
    }

    claim = {
        "epoch": proof.claimData.epoch,
        "identifier": proof.claimData.identifier,
        "owner": proof.claimData.owner,
        "timestampS": proof.claimData.timestampS,
    }

    signed_claim = {"claim": claim, "signatures": proof.signatures}

    return {"claimInfo": claim_info, "signedClaim": signed_claim}


class ReclaimProofRequest:
    """Class to handle Reclaim proof requests"""

    _application_id: str
    _provider_id: str
    _options: Optional[Dict[str, Any]]
    _timestamp: str

    _session_id: Optional[str]
    _context: Context

    _signature: Optional[str]
    _app_callback_url: Optional[str]
    _json_proof_response: Optional[bool]
    _redirect_url: Optional[str]
    _requested_proof: Optional[RequestedProof]
    _sdk_version: Optional[str]

    def __init__(
        self,
        application_id: str,
        provider_id: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize ReclaimProofRequest

        Args:
            application_id (str): Application ID
            provider_id (str): Provider ID
            options (Optional[Dict[str, Any]]): Optional configuration
        """
        self._application_id = application_id
        self._provider_id = provider_id
        self._options = options
        self._timestamp = str(int(time.time() * 1000))

        self._session_id = None
        self._context = Context(contextAddress="0x0", contextMessage="sample-context")

        self._signature = None
        self._app_callback_url = None
        self._json_proof_response = None
        self._redirect_url = None
        self._requested_proof = None
        self._sdk_version = "python-0.1.5"

        if options and options.get("log"):
            Logger.set_log_level(LogLevel.INFO)
        else:
            Logger.set_log_level(LogLevel.SILENT)

        logger.info(f"Initializing client with applicationId: {application_id}")

    @classmethod
    async def init(
        cls,
        application_id: str,
        app_secret: str,
        provider_id: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> "ReclaimProofRequest":
        """Initialize a new ReclaimProofRequest instance

        Args:
            application_id (str): Application ID
            app_secret (str): Application secret for signing
            provider_id (str): Provider ID
            options (Optional[Dict[str, Any]]): Optional configuration

        Returns:
            ReclaimProofRequest: Initialized instance

        Raises:
            InitError: If initialization fails
        """
        try:
            # Validate parameters
            if not all([application_id, app_secret, provider_id]):
                raise InvalidParamError("Required parameters missing")

            instance = cls(application_id, provider_id, options)

            # Generate and set signature
            signature = await instance._generate_signature(app_secret)
            instance._set_signature(signature)

            # Initialize session
            session_data = await init_session(
                provider_id, application_id, instance._timestamp, signature
            )
            instance._session_id = session_data.session_id

            # Build proof request
            await instance._build_proof_request(session_data.provider)

            return instance

        except Exception as e:
            logger.info(f"Error initializing ReclaimProofRequest: {str(e)}")
            raise InitError("Failed to initialize ReclaimProofRequest") from e

    def get_app_callback_url(self) -> str:
        """Get the callback URL for the application

        Returns:
            str: Callback URL

        Raises:
            GetAppCallbackUrlError: If URL cannot be generated
        """
        try:
            if not self._session_id:
                raise SessionNotStartedError("Session ID not set")

            return (
                self._app_callback_url
                or f"{DEFAULT_RECLAIM_CALLBACK_URL}{self._session_id}"
            )

        except Exception as e:
            logger.info(f"Error getting app callback url: {str(e)}")
            raise GetAppCallbackUrlError("Error getting app callback url") from e

    def get_status_url(self) -> str:
        """Get the status URL for checking proof status

        Returns:
            str: Status URL

        Raises:
            GetStatusUrlError: If URL cannot be generated
        """
        try:
            if not self._session_id:
                raise SessionNotStartedError("Session ID not set")

            return f"{DEFAULT_RECLAIM_STATUS_URL}{self._session_id}"

        except Exception as e:
            logger.info(f"Error getting status url: {str(e)}")
            raise GetStatusUrlError("Error getting status url") from e

    def set_app_callback_url(self, url: str, json_proof_response: bool = False) -> None:
        """Set custom callback URL

        Args:
            url (str): Callback URL to set

        Raises:
            SetAppCallbackUrlError: If URL cannot be set
        """
        try:
            # TODO: Add URL validation
            self._app_callback_url = url
            self._json_proof_response = bool(json_proof_response)
        except Exception as e:
            logger.info(f"Error setting app callback url: {str(e)}")
            raise SetAppCallbackUrlError("Error setting app callback url") from e

    def set_redirect_url(self, url: str) -> None:
        """Set redirect URL

        Args:
            url (str): URL to redirect to

        Raises:
            SetRedirectUrlError: If URL cannot be set
        """
        try:
            # TODO: Add URL validation
            self._redirect_url = url
        except Exception as e:
            logger.info(f"Error setting redirect url: {str(e)}")
            raise SetRedirectUrlError("Error setting redirect url") from e

    def add_context(self, address: str, message: str) -> None:
        """Add context to the proof request

        Args:
            address (str): Context address
            message (str): Context message

        Raises:
            AddContextError: If context cannot be added
        """
        try:
            if not address or not message:
                raise InvalidParamError("Address and message are required")

            self._context = Context(contextAddress=address, contextMessage=message)
        except Exception as e:
            logger.info(f"Error adding context: {str(e)}")
            raise AddContextError("Error adding context") from e

    def set_params(self, params: Dict[str, str]) -> None:
        """Set parameters for the proof request

        Args:
            params (Dict[str, str]): Parameters to set

        Raises:
            SetParamsError: If parameters cannot be set
            NoProviderParamsError: If no provider parameters are available
        """
        try:
            requested_proof = self._get_requested_proof()
            if not requested_proof:
                raise BuildProofRequestError("Requested proof is not present.")

            current_params = self._available_params()
            if not current_params:
                raise NoProviderParamsError("No params present in the provider config.")

            params_to_set = list(params.keys())
            for param in params_to_set:
                if param not in current_params:
                    raise InvalidParamError(
                        f"Cannot set parameter {param} for provider {self._provider_id}. "
                        f"Available parameters: {current_params}"
                    )
                if not isinstance(params[param], str):
                    raise InvalidParamError(
                        f"Cannot set parameter {param} for provider {self._provider_id}. "
                        "Value must be a string."
                    )

            # dict has no attribute parameters error fix
            if isinstance(self._requested_proof, dict):
                self._requested_proof['parameters'].update(params)
            else:
                self._requested_proof.parameters.update(params)
            
        except Exception as e:
            logger.info(f"Error Setting Params: {str(e)}")
            raise SetParamsError("Error setting params") from e

    def to_json_string(self) -> str:
        """Convert the proof request to JSON string

        Returns:
            str: JSON string representation

        Raises:
            InvalidParamError: If conversion to JSON string fails
        """
        try:
            # Create the full dictionary

            logger.info(f"Requested proof: {self._requested_proof}")
            data = {
                "applicationId": self._application_id,
                "providerId": self._provider_id,
                "sessionId": self._session_id,
                "context": self._context.to_json(),
                "requestedProof": (
                    self._get_requested_proof() if self._requested_proof else None
                ),
                "appCallbackUrl": self._app_callback_url,
                "signature": self._signature,
                "redirectUrl": self._redirect_url,
                "timeStamp": self._timestamp,
                "options": self._options,
                "sdkVersion": self._sdk_version,
                "jsonProofResponse": self._json_proof_response,
            }

            return json.dumps(data)
        except Exception as e:
            logger.info(f"Error converting to json string: {str(e)}")
            raise ConvertToJsonStringError("Error converting to json string") from e

    async def from_json_string(cls, json_string: str) -> "ReclaimProofRequest":
        """Create ReclaimProofRequest instance from JSON string

        Args:
            json_string (str): JSON string to parse

        Returns:
            ReclaimProofRequest: New instance

        Raises:
            InvalidParamError: If JSON string is invalid
        """
        try:
            data = json.loads(json_string)

            # Validate required fields
            required_fields = [
                "applicationId",
                "providerId",
                "signature",
                "sessionId",
                "sdkVersion",
                "timeStamp",
            ]
            for field in required_fields:
                if not data.get(field):
                    raise InvalidParamError(f"Missing required field: {field}")

            # Create instance
            instance = cls(
                data["applicationId"], data["providerId"], data.get("options")
            )

            # Set properties
            instance._session_id = data["sessionId"]
            instance._context = Context.from_json(data["context"])
            instance._requested_proof = (
                data["requestedProof"] if data["requestedProof"] else None
            )
            instance._app_callback_url = data.get("appCallbackUrl")
            instance._sdk_version = data["sdkVersion"]
            instance._redirect_url = data.get("redirectUrl")
            instance._signature = data["signature"]
            instance._timestamp = data["timeStamp"]

            logger.info(f"Requested proof: {instance._requested_proof}")

            return instance

        except Exception as e:
            logger.info(f"Failed to parse JSON string: {str(e)}")
            raise InvalidParamError("Invalid JSON string provided")

    async def get_request_url(self) -> str:
        """Get the URL for making the proof request

        Returns:
            str: Request URL

        Raises:
            GetRequestUrlError: If URL cannot be generated
        """
        logger.info("Creating Request Url")
        if not self._signature:
            raise SignatureNotFoundError("Signature is not set.")

        try:
            requested_proof = self._get_requested_proof()
            validate_signature(
                self._provider_id,
                self._signature,
                self._application_id,
                self._timestamp,
            )

            template_data = {
                "sessionId": self._session_id,
                "providerId": self._provider_id,
                "applicationId": self._application_id,
                "signature": self._signature,
                "timestamp": self._timestamp,
                "callbackUrl": self.get_app_callback_url(),
                "context": json.dumps(self._context.to_json()),
                "parameters": get_filled_parameters(requested_proof),
                "redirectUrl": self._redirect_url or "",
                "acceptAiProviders": self._options.get("acceptAiProviders", False),
                "sdkVersion": self._sdk_version or "",
                "jsonProofResponse": self._json_proof_response,
            }

            await update_session(self._session_id, SessionStatus.SESSION_STARTED)

            if self._options.get("useAppClip"):
                from urllib.parse import quote

                template = quote(json.dumps(template_data))
                template = template.replace("(", "%28").replace(")", "%29")

                import platform

                if platform.system() != "Darwin":  # Not iOS
                    url = (
                        f"https://share.reclaimprotocol.org/verify/?template={template}"
                    )
                    logger.info(f"Instant App Url created successfully: {url}")
                    return url
                else:
                    url = f"https://appclip.apple.com/id?p=org.reclaimprotocol.app.clip&template={template}"
                    logger.info(f"App Clip Url created successfully: {url}")
                    return url
            else:
                link = await create_link_with_template_data(template_data)
                logger.info(f"Request Url created successfully: {link}")
                return link

        except Exception as e:
            logger.info(f"Error creating Request Url: {str(e)}")
            raise GetRequestUrlError("Error creating request URL") from e

    # Private helper methods
    def _set_signature(self, signature: str) -> None:
        """Set the signature

        Args:
            signature (str): Signature to set

        Raises:
            SetSignatureError: If signature cannot be set
        """
        try:
            if not signature:
                raise InvalidParamError("Signature is required")
            self._signature = signature
            logger.info(
                f"Signature set successfully for application ID: {self._application_id}"
            )
        except Exception as e:
            logger.info(f"Error setting signature: {str(e)}")
            raise SetSignatureError("Error setting signature") from e

    async def _build_proof_request(self, provider: ProviderData) -> RequestedProof:
        """Build the proof request

        Args:
            provider (ProviderData): Provider data

        Returns:
            RequestedProof: Built proof request

        Raises:
            BuildProofRequestError: If request cannot be built
        """
        try:
            self._requested_proof = generate_requested_proof(provider)
            return self._requested_proof
        except Exception as e:
            logger.info(str(e))
            raise BuildProofRequestError(
                "Something went wrong while generating proof request"
            ) from e

    def _get_requested_proof(self) -> RequestedProof:
        """Get the requested proof

        Returns:
            RequestedProof: The requested proof

        Raises:
            GetRequestedProofError: If proof cannot be retrieved
        """
        try:
            if not self._requested_proof:
                raise BuildProofRequestError(
                    "RequestedProof is not present in the instance."
                )
            return self._requested_proof
        except Exception as e:
            logger.info(f"Error fetching requested proof: {str(e)}")
            raise GetRequestedProofError("Error fetching requested proof") from e

    async def _generate_signature(self, app_secret: str) -> str:
        """Generate signature using app secret

        Args:
            app_secret (str): Application secret for signing

        Returns:
            str: Generated signature

        Raises:
            SignatureGeneratingError: If signature generation fails
        """
        try:
            # Create canonical data same as Dart version
            canonical_data = canonicalize(
                {
                    "providerId": self._provider_id,
                    "timestamp": self._timestamp,
                }
            )

            message_hash = keccak_256(canonical_data).hexdigest()
            account = Account.from_key(app_secret)
            message_hash_bytes = bytes.fromhex(message_hash)
            message = encode_defunct(message_hash_bytes)
            signed_message = account.sign_message(message)
            signature = signed_message.signature.hex()

            return "0x" + signature

        except Exception as e:
            logger.info(f"Error generating signature: {str(e)}")
            raise SignatureGeneratingError(
                f"Error generating signature for applicationSecret: {app_secret}"
            ) from e

    def _available_params(self) -> List[str]:
        """Get available parameters for the provider

        Returns:
            List[str]: List of available parameter names

        Raises:
            AvailableParamsError: If parameters cannot be retrieved
        """
        try:
            requested_proof = self._get_requested_proof()
            
            # Initialize empty set for available parameters
            available_params = set()
            
            # Handle both dictionary and object types
            parameters = (
                requested_proof['parameters'] 
                if isinstance(requested_proof, dict) 
                else requested_proof.parameters
            )
            
            url = (
                requested_proof['url']
                if isinstance(requested_proof, dict)
                else requested_proof.url
            )
            
            if parameters:
                available_params.update(parameters.keys())

            # Add URL parameters
            if url:
                import re
                url_params = re.findall(r"{{(.*?)}}", url)
                available_params.update(url_params)
            

            return list(available_params)

        except Exception as e:
            logger.info(f"Error fetching available params: {str(e)}")
            raise AvailableParamsError("Error fetching available params") from e

    # Add other private helper methods as needed
