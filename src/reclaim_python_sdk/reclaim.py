import json
import time
import warnings
from json_canonical import canonicalize
from sha3 import keccak_256
from typing import Dict, List, Optional, Any, Union
from eth_account import Account
from eth_account.messages import encode_defunct
from .utils.interfaces import (
    Proof,
    Context,
    ProviderClaimData,
)
from .utils.types import ClaimInfo, SignedClaim, SessionStatus, StartSessionParams

from .utils.constants import DEFAULT_RECLAIM_CALLBACK_URL, DEFAULT_RECLAIM_STATUS_URL

from .utils.session_utils import init_session, update_session, fetch_status_url
from .utils.proof_utils import create_link_with_template_data
from .utils.validation_utils import validate_parameters, validate_signature



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
    ConvertToJsonStringError,
    InvalidParamError,
)

from .utils.proof_utils import assert_valid_signed_claim, get_attestors

from .witness import get_identifier_from_claim_info

from .utils.logger import LogLevel, Logger


logger = Logger()

_reclaim_python_sdk_version = '2.0.0'


async def verify_proof(proof: Union[Proof, List[Proof]]) -> bool:
    """
    Verifies one or more Reclaim proofs by validating signatures and witness information

    Args:
        proof (Union[Proof, List[Proof]]): A single proof object or list of proof objects to verify

    Returns:
        bool: Returns True if all proofs are valid, False otherwise

    Raises:
        SignatureNotFoundError: When proof has no signatures
        ProofNotVerifiedError: When identifier mismatch occurs

    Example:
        >>> is_valid = await verify_proof(proof)
        >>> are_all_valid = await verify_proof([proof1, proof2, proof3])
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
        attestors = await get_attestors()

        claim_data: ProviderClaimData = proof.claimData
        signed_claim = SignedClaim(
            claim=claim_data,
            signatures=[
                bytes.fromhex(sig.replace("0x", "")) for sig in proof.signatures
            ],
        )

        assert_valid_signed_claim(signed_claim, attestors)

    except Exception as e:
        logger.info(f"Error verifying proof: {str(e)}")
        return False

    return True


def transform_for_onchain(proof: Proof) -> Dict[str, Any]:
    """
    Transforms a Reclaim proof into a format suitable for on-chain verification

    Args:
        proof (Proof): The proof object to transform

    Returns:
        Dict[str, Any]: Object containing claimInfo and signedClaim formatted for blockchain contracts

    Example:
        >>> onchain_data = transform_for_onchain(proof)
        >>> claim_info = onchain_data['claimInfo']
        >>> signed_claim = onchain_data['signedClaim']
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
    _resolved_provider_version: Optional[str]

    _session_id: Optional[str]
    _context: Union[Context, Dict[str, Any]]
    
    _json_proof_response: bool

    _signature: Optional[str]
    _app_callback_url: Optional[str]
    _redirect_url: Optional[str]
    _redirect_url_options: Optional[Dict[str, Any]]
    _cancel_callback_url: Optional[str]
    _cancel_redirect_url: Optional[str]
    _cancel_redirect_url_options: Optional[Dict[str, Any]]
    _modal_options: Optional[Dict[str, Any]]
    _claim_creation_type: Optional[str]
    
    _parameters: Optional[Dict[str, str]]
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
        self._timestamp = str(int(time.time() * 1000))

        self._session_id = ""
        self._context = Context(contextAddress="0x0", contextMessage="sample context")
        self._app_callback_url = ""
        self._parameters = {}
        self._signature = ""
        self._redirect_url = ""
        self._redirect_url_options = None
        self._cancel_callback_url = ""
        self._cancel_redirect_url = ""
        self._cancel_redirect_url_options = None
        self._options = {"useAppClip": True, "useBrowserExtension": True}
        if options:
            self._options.update(options)
        self._sdk_version = f"python-{_reclaim_python_sdk_version}"
        self._json_proof_response = False
        self._resolved_provider_version = ""
        self._modal_options = None
        self._claim_creation_type = "createClaim"

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
        """
        Initializes a new Reclaim proof request instance with automatic signature generation and session creation

        Args:
            application_id (str): Your Reclaim application ID
            app_secret (str): Your application secret key for signing requests
            provider_id (str): The ID of the provider to use for proof generation
            options (Optional[Dict[str, Any]]): Optional configuration options for the proof request

        Returns:
            ReclaimProofRequest: A fully initialized proof request instance

        Raises:
            InitError: When initialization fails due to invalid parameters or session creation errors

        Example:
            >>> proof_request = await ReclaimProofRequest.init(
            ...     'your-app-id',
            ...     'your-app-secret',
            ...     'provider-id',
            ...     {'log': True, 'acceptAiProviders': True}
            ... )
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
            logger.info(f"Initializing session for provider: {provider_id}, applicationId: {application_id}, timestamp: {instance._timestamp}, signature: {signature}")
            
            # if providerVersion is present in options, use it, send None otherwise
            session_data = await init_session(
                provider_id, application_id, instance._timestamp, signature, options.get("provider_version") if options else None
            )
            
            instance._session_id = session_data.session_id
            instance._resolved_provider_version = session_data.resolved_provider_version


            return instance

        except Exception as e:
            logger.info(f"Error initializing ReclaimProofRequest: {str(e)}")
            raise InitError("Failed to initialize ReclaimProofRequest") from e

    def get_app_callback_url(self) -> str:
        """
        Returns the currently configured app callback URL

        If no custom callback URL was set via set_app_callback_url(), this returns the default
        Reclaim service callback URL with the current session ID.

        Returns:
            str: The callback URL where proofs will be submitted

        Raises:
            GetAppCallbackUrlError: When unable to retrieve the callback URL

        Example:
            >>> callback_url = proof_request.get_app_callback_url()
            >>> print('Proofs will be sent to:', callback_url)
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
        """
        Returns the status URL for monitoring the current session

        This URL can be used to check the status of the proof request session.

        Returns:
            str: The status monitoring URL for the current session

        Raises:
            GetStatusUrlError: When unable to retrieve the status URL

        Example:
            >>> status_url = proof_request.get_status_url()
            >>> # Use this URL to poll for session status updates
        """
        try:
            if not self._session_id:
                raise SessionNotStartedError("Session ID not set")

            return f"{DEFAULT_RECLAIM_STATUS_URL}{self._session_id}"

        except Exception as e:
            logger.info(f"Error getting status url: {str(e)}")
            raise GetStatusUrlError("Error getting status url") from e

    def set_app_callback_url(self, url: str, json_proof_response: bool = False) -> None:
        """
        Sets a custom callback URL where proofs will be submitted

        By default, proofs are sent to the Reclaim service. Use this method to receive
        proofs directly on your own backend infrastructure.

        Args:
            url (str): The URL where proofs should be submitted via HTTP POST
            json_proof_response (bool, optional): If True, sends proof as JSON. If False, sends as URL-encoded form data. Defaults to False.

        Raises:
            SetAppCallbackUrlError: When the URL is invalid or malformed

        Example:
            >>> proof_request.set_app_callback_url('https://api.yourdomain.com/reclaim/callback')
        """
        try:
            # TODO: Add URL validation
            self._app_callback_url = url
            self._json_proof_response = json_proof_response
        except Exception as e:
            logger.info(f"Error setting app callback url: {str(e)}")
            raise SetAppCallbackUrlError("Error setting app callback url") from e

    def set_redirect_url(self, url: str, method: str = 'GET', body: Optional[List[Dict[str, str]]] = None) -> None:
        """
        Sets a custom redirect URL where users will be sent after successful verification

        This URL can optionally include HTTP method and body parameters if you need
        to perform a POST request (e.g., submitting a form) upon successful verification.

        Args:
            url (str): The URL to redirect the user to
            method (str, optional): The HTTP method to use (e.g., 'GET' or 'POST'). Defaults to 'GET'.
            body (Optional[List[Dict[str, str]]], optional): Webhook or form body parameters for POST requests. Defaults to None.

        Raises:
            SetRedirectUrlError: When the URL is invalid or malformed

        Example:
            >>> proof_request.set_redirect_url('https://yourdomain.com/success')
            >>> # Or with POST data
            >>> proof_request.set_redirect_url(
            ...     'https://yourdomain.com/webhook',
            ...     'POST',
            ...     [{'key': 'status', 'value': 'verified'}]
            ... )
        """
        try:
            # TODO: Add URL validation
            self._redirect_url = url
            self._redirect_url_options = {"method": method, "body": body} if body else {"method": method}
        except Exception as e:
            logger.info(f"Error setting redirect url: {str(e)}")
            raise SetRedirectUrlError("Error setting redirect url") from e

    def set_cancel_callback_url(self, url: str) -> None:
        """
        Sets a custom callback URL where abortion errors during verification will be submitted

        This allows you to be notified on your backend if a user cancels the verification
        or if an unrecoverable error occurs.

        Args:
            url (str): The URL where errors should be submitted via HTTP POST
        
        Example:
            >>> proof_request.set_cancel_callback_url('https://api.yourdomain.com/reclaim/cancel')
        """
        try:
            self._cancel_callback_url = url
        except Exception as e:
            logger.info(f"Error setting cancel callback url: {str(e)}")
            raise Exception("Error setting cancel callback url") from e

    def set_cancel_redirect_url(self, url: str, method: str = 'GET', body: Optional[List[Dict[str, str]]] = None) -> None:
        """
        Sets a custom redirect URL where users will be sent after a verification failure or cancellation

        This URL can optionally include HTTP method and body parameters if you need
        to perform a POST request (e.g., submitting a form) upon failure.

        Args:
            url (str): The URL to redirect the user to
            method (str, optional): The HTTP method to use (e.g., 'GET' or 'POST'). Defaults to 'GET'.
            body (Optional[List[Dict[str, str]]], optional): Optional form body parameters for POST requests. Defaults to None.
        
        Example:
            >>> proof_request.set_cancel_redirect_url('https://yourdomain.com/failed')
        """
        try:
            self._cancel_redirect_url = url
            self._cancel_redirect_url_options = {"method": method, "body": body} if body else {"method": method}
        except Exception as e:
            logger.info(f"Error setting cancel redirect url: {str(e)}")
            raise Exception("Error setting cancel redirect url") from e

    def set_claim_creation_type(self, claim_creation_type: str) -> None:
        """
        Sets the claim creation type for the proof request

        Args:
            claim_creation_type (str): The type of claim creation ('STANDALONE', etc.)
        """
        self._claim_creation_type = claim_creation_type

    def set_modal_options(self, options: Dict[str, Any]) -> None:
        """
        Sets custom options for the QR code modal display

        This allows customizing the appearance and behavior of the verification modal,
        such as changing the theme, adding a custom title, or modifying the extension URL.

        Note: To use modal, please use js-sdk in your website.

        Args:
            options (Dict[str, Any]): Modal configuration options

        Example:
            >>> proof_request.set_modal_options({
            ...     'title': 'Verify Your Identity',
            ...     'darkTheme': True,
            ...     'showExtensionInstallButton': True
            ... })
        """
        self._modal_options = options

    def set_json_context(self, context: Dict[str, Any]) -> None:
        """
        Sets additional context data to be stored with the claim

        Args:
            context (Dict[str, Any]): Additional data you want to store
            
        Raises:
            AddContextError: When context cannot be added
        """
        try:
            self._context = context
        except Exception as e:
            logger.info(f"Error setting json context: {str(e)}")
            raise AddContextError("Error setting context") from e

    def set_context(self, address: str, message: str) -> None:
        """
        Sets additional context data to be stored with the claim (address and message)

        Context provides additional metadata that will be cryptographically bound to the proof.
        This is useful for tying proofs back to specific users or sessions in your application.

        Args:
            address (str): Context address
            message (str): Context message

        Raises:
            AddContextError: When context cannot be added
            InvalidParamError: When required parameters are missing

        Example:
            >>> proof_request.set_context('user-123', 'Account Verification Profile')
        """
        try:
            if not address or not message:
                raise InvalidParamError("Address and message are required")
            self._context = Context(contextAddress=address, contextMessage=message)
        except Exception as e:
            logger.info(f"Error setting context: {str(e)}")
            raise AddContextError("Error setting context") from e

    def get_cancel_callback_url(self) -> str:
        """
        Returns the currently configured cancel callback URL

        If no custom cancel callback URL was set via set_cancel_callback_url(), this returns the default
        Reclaim service cancel callback URL with the current session ID.

        Returns:
            str: The cancel callback URL where errors will be submitted
        
        Raises:
            GetAppCallbackUrlError: When unable to retrieve the cancel callback URL

        Example:
            >>> callback_url = proof_request.get_cancel_callback_url()
            >>> print('Errors will be sent to:', callback_url)
        """
        try:
            if not self._session_id:
                raise SessionNotStartedError("Session ID not set")
            # Using DEFAULT_RECLAIM_STATUS_URL or DEFAULT_RECLAIM_CALLBACK_URL equivalent logic here, 
            # as python sdk relies on a hardcoded callback url mostly, but we'll return self._cancel_callback_url
            from .utils.constants import BACKEND_BASE_URL
            DEFAULT_RECLAIM_CANCEL_CALLBACK_URL = f'{BACKEND_BASE_URL}/api/sdk/cancel-callback?callbackId='
            return self._cancel_callback_url or f"{DEFAULT_RECLAIM_CANCEL_CALLBACK_URL}{self._session_id}"
        except Exception as e:
            logger.info(f"Error getting cancel callback url: {str(e)}")
            raise GetAppCallbackUrlError("Error getting cancel callback url") from e

    def get_session_id(self) -> str:
        """
        Returns the session ID associated with this proof request

        The session ID is automatically generated during initialization and uniquely
        identifies this proof request session.

        Returns:
            str: The session ID string
        
        Raises:
            SessionNotStartedError: When session ID is not set

        Example:
            >>> session_id = proof_request.get_session_id()
            >>> print('Session ID:', session_id)
        """
        if not self._session_id:
            raise SessionNotStartedError("SessionId is not set")
        return self._session_id
    
    def get_json_proof_response(self) -> bool:
        """
        Returns whether proofs will be submitted as JSON format

        Returns:
            bool: True if proofs are sent as application/json, False for application/x-www-form-urlencoded

        Example:
            >>> is_json = proof_request.get_json_proof_response()
            >>> print('JSON format:', is_json)
        """
        return self._json_proof_response

    async def start_session(self, params: StartSessionParams) -> None:
        """
        Starts the proof request session and monitors for proof submission
        
        This method begins polling the session status to detect when
        a proof has been generated and submitted. It handles both default Reclaim callbacks
        and custom callback URLs.

        For default callbacks: Verifies proofs automatically and passes them to onSuccess
        For custom callbacks: Monitors submission status and notifies via onSuccess when complete.

        Args:
            params (StartSessionParams): Contains on_success and on_error callbacks.
            
        Raises:
            SessionNotStartedError: When session ID is not defined
            ProofNotVerifiedError: When proof verification fails (default callback only)
            ProofSubmissionFailedError: When proof submission fails (custom callback only)
            ProviderFailedError: When proof generation fails with timeout

        Example:
            >>> async def handle_success(proof):
            ...     print('Proof received:', proof)
            >>> async def handle_error(error):
            ...     print('Error:', error)
            >>> await proof_request.start_session(StartSessionParams(
            ...     on_success=handle_success,
            ...     on_error=handle_error
            ... ))
        """
        if not self._session_id:
            message = "Session can't be started due to undefined value of sessionId"
            logger.info(message)
            raise SessionNotStartedError(message)

        logger.info('Starting session')
        session_update_polling_interval = 3
        
        from .utils.errors import ProviderFailedError, ErrorDuringVerificationError, ProofSubmissionFailedError
        
        # In JS: setInterval. Here we use an asyncio background task polling.
        async def _poll_session():
            while True:
                try:
                    status_url_response = await fetch_status_url(self._session_id)
                    if not status_url_response.session:
                        await asyncio.sleep(session_update_polling_interval)
                        continue

                    status_v2 = status_url_response.session.statusV2

                    if status_v2 == SessionStatus.PROOF_GENERATION_FAILED:
                        # ignoring complicated timeout logic for python since we just poll endlessly
                        await asyncio.sleep(session_update_polling_interval)
                        continue
                        
                    if status_v2 in [SessionStatus.PROOF_SUBMISSION_FAILED, "ERROR_SUBMITTED", "ERROR_SUBMISSION_FAILED"]:
                        raise ErrorDuringVerificationError()

                    is_default_callback_url = self.get_app_callback_url() == f"{DEFAULT_RECLAIM_CALLBACK_URL}{self._session_id}"

                    if is_default_callback_url:
                        if status_url_response.session.proofs and len(status_url_response.session.proofs) > 0:
                            proofs = status_url_response.session.proofs
                            if self._claim_creation_type == "STANDALONE":
                                verified = await verify_proof(proofs)
                                if not verified:
                                    logger.info(f"Proofs not verified: {proofs}")
                                    raise ProofNotVerifiedError()
                            
                            if len(proofs) == 1:
                                params.on_success(proofs[0])
                            else:
                                params.on_success(proofs)
                            break
                    else:
                        if status_v2 == SessionStatus.PROOF_SUBMISSION_FAILED:
                            raise ProofSubmissionFailedError()
                        if status_v2 in [SessionStatus.PROOF_SUBMITTED, "AI_PROOF_SUBMITTED"]:
                            if params.on_success:
                                params.on_success([])
                            break

                except Exception as e:
                    if params.on_error:
                        params.on_error(e)
                    break
                await asyncio.sleep(session_update_polling_interval)
        
        # Start background polling task and return immediately (or wait depending on design? In python we'll use create_task)
        asyncio.create_task(_poll_session())

    def add_context(self, address: str, message: str) -> None:
        """
        Adds context to the proof request (Deprecated: use set_context instead)

        Args:
            address (str): Context address
            message (str): Context message

        Raises:
            AddContextError: When context cannot be added
        """
        warnings.warn(
            "add_context is deprecated and will be removed in a future version. "
            "Please use set_context(address, message) instead.",
            DeprecationWarning,
            stacklevel=2
        )
        self.set_context(address, message)

    def set_callback_url(self, url: str) -> None:
        """
        Sets the callback URL (Deprecated: use set_app_callback_url instead)

        Args:
            url (str): The callback URL
        """
        warnings.warn(
            "set_callback_url is deprecated and will be removed in a future version. "
            "Please use set_app_callback_url(url) instead.",
            DeprecationWarning,
            stacklevel=2
        )
        self.set_app_callback_url(url=url)

    def set_params(self, params: Dict[str, str]) -> None:
        """
        Sets the parameters for the proof request

        Parameters are used to configure specific aspects of the proof generation,
        such as specifying which data fields to extract or verifying specific conditions.

        Args:
            params (Dict[str, str]): Dictionary of key-value pairs representing the parameters

        Raises:
            SetParamsError: When parameters are invalid or cannot be set

        Example:
            >>> proof_request.set_params({
            ...     'email': 'test@example.com',
            ...     'username': 'johndoe'
            ... })
        """
        try:
            validate_parameters(params)
            self._parameters.update(params)
        except Exception as e:
            logger.info(f"Error Setting Params: {str(e)}")
            raise SetParamsError("Error setting params") from e

    def to_json_string(self) -> str:
        """
        Exports the Reclaim proof verification request as a JSON string

        This serialized format can be sent to the frontend to recreate this request using
        ReclaimProofRequest.from_json_string() or any InApp SDK's startVerificationFromJson()
        method to initiate the verification journey.

        Returns:
            str: JSON string representation of the proof request.

        Example:
            >>> json_string = proof_request.to_json_string()
            >>> # Send to frontend or store for later use
            >>> # Can be reconstructed with: ReclaimProofRequest.from_json_string(json_string)
        """
        try:
            # Create the full dictionary
            context_data = self._context.to_json() if hasattr(self._context, 'to_json') else self._context

            data = {
                "applicationId": self._application_id,
                "providerId": self._provider_id,
                "sessionId": self._session_id,
                "context": context_data,
                "parameters": self._parameters,
                "signature": self._signature,
                "timeStamp": self._timestamp,
                "options": self._options,
                "sdkVersion": self._sdk_version,
                "jsonProofResponse": self._json_proof_response,
                "resolvedProviderVersion": self._resolved_provider_version or "",
                "claimCreationType": self._claim_creation_type
            }

            # Only include optional variables if they are set
            if self._app_callback_url:
                data["appCallbackUrl"] = self._app_callback_url
            if self._redirect_url:
                data["redirectUrl"] = self._redirect_url
            if self._redirect_url_options:
                data["redirectUrlOptions"] = self._redirect_url_options
            if self._cancel_callback_url:
                data["cancelCallbackUrl"] = self._cancel_callback_url
            if self._cancel_redirect_url:
                data["cancelRedirectUrl"] = self._cancel_redirect_url
            if self._cancel_redirect_url_options:
                data["cancelRedirectUrlOptions"] = self._cancel_redirect_url_options
            if self._modal_options:
                data["modalOptions"] = self._modal_options

            return json.dumps(data)
        except Exception as e:
            logger.info(f"Error converting to json string: {str(e)}")
            raise ConvertToJsonStringError("Error converting to json string") from e

    @classmethod
    async def from_json_string(cls, json_string: str) -> "ReclaimProofRequest":
        """
        Creates a ReclaimProofRequest instance from a JSON string representation

        This method deserializes a previously exported proof request (via to_json_string) and reconstructs
        the instance with all its properties. Useful for recreating requests on the frontend or across different contexts.

        Args:
            json_string (str): JSON string containing the serialized proof request data

        Returns:
            ReclaimProofRequest: Reconstructed proof request instance

        Raises:
            InvalidParamError: When JSON string is invalid or contains invalid parameters

        Example:
            >>> json_string = proof_request.to_json_string()
            >>> reconstructed = await ReclaimProofRequest.from_json_string(json_string)
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
            
            if data.get("parameters"):
                validate_parameters(data["parameters"])

            # Set properties
            instance._session_id = data["sessionId"]            # Support both Context object or raw dictionary (for set_json_context)
            if "context" in data:
                ctx_data = data["context"]
                if isinstance(ctx_data, dict) and "contextAddress" in ctx_data and "contextMessage" in ctx_data:
                    instance._context = Context.from_json(ctx_data)
                else:
                    instance._context = ctx_data
            else:
                instance._context = Context(contextAddress="0x0", contextMessage="sample context")
            instance._app_callback_url = data.get("appCallbackUrl")
            instance._sdk_version = data["sdkVersion"]
            instance._redirect_url = data.get("redirectUrl")
            instance._redirect_url_options = data.get("redirectUrlOptions")
            instance._cancel_callback_url = data.get("cancelCallbackUrl")
            instance._cancel_redirect_url = data.get("cancelRedirectUrl")
            instance._cancel_redirect_url_options = data.get("cancelRedirectUrlOptions")
            instance._signature = data["signature"]
            # prefer timestamp over timeStamp for backward compatibility
            instance._timestamp = data.get("timestamp", data.get("timeStamp"))
            instance._parameters = data.get("parameters")
            instance._json_proof_response = data.get("jsonProofResponse", False)
            instance._resolved_provider_version = data.get("resolvedProviderVersion", "")
            instance._modal_options = data.get("modalOptions")
            instance._claim_creation_type = data.get("claimCreationType", "STANDALONE")

            return instance

        except Exception as e:
            logger.info(f"Failed to parse JSON string: {str(e)}")
            raise InvalidParamError("Invalid JSON string provided")

    async def get_request_url(self) -> str:
        """
        Generates and returns the request URL for proof verification

        This URL can be shared with users to initiate the proof generation process.
        The URL format varies based on device type (if running in a context where app clips/instant apps make sense)

        Returns:
            str: The generated request URL
        
        Raises:
            SignatureNotFoundError: When signature is not set
            GetRequestUrlError: When request URL generation fails

        Example:
            >>> request_url = await proof_request.get_request_url()
            >>> # Share this URL with users or display as QR code
        """
        logger.info("Creating Request Url")
        if not self._signature:
            raise SignatureNotFoundError("Signature is not set.")

        try:
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
                "context": json.dumps(self._context.to_json()) if isinstance(self._context, Context) else json.dumps(self._context),
                "parameters": self._parameters,
                "redirectUrl": self._redirect_url or "",
                "redirectUrlOptions": self._redirect_url_options,
                "cancelCallbackUrl": self._cancel_callback_url or "",
                "cancelRedirectUrl": self._cancel_redirect_url or "",
                "cancelRedirectUrlOptions": self._cancel_redirect_url_options,
                "acceptAiProviders": self._options.get("acceptAiProviders", False),
                "sdkVersion": self._sdk_version or "",
                "jsonProofResponse": self._json_proof_response,
                "resolvedProviderVersion": self._resolved_provider_version or ""
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

    # Add other private helper methods as needed
