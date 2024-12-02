class ReclaimError(Exception):
    """Base class for all Reclaim exceptions"""
    def __init__(self, message: str = None, inner_error: Exception = None):
        super().__init__(message)
        self.message = message
        self.inner_error = inner_error
        if inner_error:
            self.__cause__ = inner_error
    
    def __str__(self):
        """Override string representation to match Dart version"""
        if self.inner_error:
            return f'{self.__class__.__name__}: {self.message}\nCaused by: {str(self.inner_error)}'
        return f'{self.__class__.__name__}: {self.message}'

class TimeoutError(ReclaimError):
    """Raised when an operation times out"""
    pass

class ProofNotVerifiedError(ReclaimError):
    """Raised when proof verification fails"""
    pass

class SessionNotStartedError(ReclaimError):
    """Raised when trying to access a session that hasn't been started"""
    pass

class ProviderNotFoundError(ReclaimError):
    """Raised when a specified provider is not found"""
    pass

class BuildProofRequestError(ReclaimError):
    """Raised when there's an error building a proof request"""
    pass

class SignatureGeneratingError(ReclaimError):
    """Raised when there's an error generating a signature"""
    pass

class SignatureNotFoundError(ReclaimError):
    """Raised when a required signature is not found"""
    pass

class InvalidSignatureError(ReclaimError):
    """Raised when a signature is invalid"""
    pass

class UpdateSessionError(ReclaimError):
    """Raised when there's an error updating a session"""
    pass

class InitSessionError(ReclaimError):
    """Raised when there's an error initializing a session"""
    pass

class ProviderFailedError(ReclaimError):
    """Raised when a provider operation fails"""
    pass

class InvalidParamError(ReclaimError):
    """Raised when invalid parameters are provided"""
    pass

class ApplicationError(ReclaimError):
    """Raised when there's a general application error"""
    pass

class InitError(ReclaimError):
    """Raised when initialization fails"""
    pass

class AvailableParamsError(ReclaimError):
    """Raised when there's an error with available parameters"""
    pass

class BackendServerError(ReclaimError):
    """Raised when there's a backend server error"""
    pass

class GetStatusUrlError(ReclaimError):
    """Raised when there's an error getting the status URL"""
    pass

class NoProviderParamsError(ReclaimError):
    """Raised when provider parameters are missing"""
    pass

class SetParamsError(ReclaimError):
    """Raised when there's an error setting parameters"""
    pass

class AddContextError(ReclaimError):
    """Raised when there's an error adding context"""
    pass

class SetSignatureError(ReclaimError):
    """Raised when there's an error setting a signature"""
    pass

class GetAppCallbackUrlError(ReclaimError):
    """Raised when there's an error getting the app callback URL"""
    pass

class GetRequestUrlError(ReclaimError):
    """Raised when there's an error getting the request URL"""
    pass


class SetAppCallbackUrlError(ReclaimError):
    """Raised when there's an error setting the app callback URL"""
    pass

class SetRedirectUrlError(ReclaimError):
    """Raised when there's an error setting the redirect URL"""
    pass

class GetRequestedProofError(ReclaimError):
    """Raised when there's an error getting the requested proof"""
    pass

class ConvertToJsonStringError(ReclaimError):
    """Raised when there's an error converting to JSON string"""
    pass
