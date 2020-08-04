from typing import Any, Dict, Union

import aiohttp


class EsyLinkException(Exception):
    """Base exception class for EsyLink cog."""


class UserError(EsyLinkException):
    """Exception that's thrown for user errors."""


class HTTPException(EsyLinkException):
    """Exception that's thrown when an HTTP request operation fails.

    Attributes
    ----------
    response: aiohttp.ClientResponse
        The response of the failed HTTP request.
    status: int
        The status code of the HTTP request.
    data: Union[Dict[str, Any], str]
        Raw response data.
    """

    def __init__(
        self, response: aiohttp.ClientResponse, data: Union[Dict[str, Any], str]
    ) -> None:
        self.response = response
        self.status = response.status
        self.data = data
        super().__init__(
            f"{self.response.reason} (status code: {self.status}) | data: {self.response.request_info}"
        )
