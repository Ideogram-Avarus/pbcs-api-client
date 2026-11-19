

class PbcsError(Exception):
    """Base exception for PBCS client errors."""


class PbcsAuthenticationError(PbcsError):
    """Authentication or authorization failed."""


class PbcsRequestError(PbcsError):
    """An HTTP request or API response failed."""