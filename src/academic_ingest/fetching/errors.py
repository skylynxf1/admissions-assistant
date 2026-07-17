class FetchError(RuntimeError):
    """Base class for bounded acquisition failures."""


class UnsafeSourceError(FetchError, ValueError):
    """Raised before a request can reach an unsafe or out-of-scope source."""


class ResponseTooLargeError(FetchError):
    """Raised when a response crosses the configured byte limit."""


class UnsupportedContentTypeError(FetchError):
    """Raised for response types the ingestion service cannot safely parse."""
