"""Thin HTTP client for the HubSpot API: owns auth headers and rate limiting."""
import time
from dataclasses import dataclass
from typing import Any, Protocol

import requests


@dataclass
class HubSpotResponse:
    """Represent a response received from the HubSpot API."""

    status_code: int
    data: dict[str, Any]
    text: str

    @property
    def ok(self) -> bool:
        """Return whether the request was successful."""
        return self.status_code in (200, 201)


class HttpClient(Protocol):
    """Abstraction repositories depend on, so they never touch `requests` directly."""

    def get(self, path: str) -> HubSpotResponse:
        """Send a GET request to the specified API path."""
        ...  # pylint: disable=unnecessary-ellipsis

    def post(self, path: str, payload: dict[str, Any]) -> HubSpotResponse:
        """Send a POST request with the provided payload."""
        ...  # pylint: disable=unnecessary-ellipsis


class HubSpotClient:
    """Send authenticated HTTP requests to the HubSpot API."""

    def __init__(self, base_url: str, token: str, rate_limit_delay: float = 0.15):
        """
        Initialize the client with API connection settings.
        
        Args:
            base_url: Base URL of the HubSpot API.
            token: Access token used for authentication.
            rate_limit_delay: Delay between API requests in seconds.
        """

        self._base_url = base_url.rstrip("/")
        self._rate_limit_delay = rate_limit_delay
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        })

    def get(self, path: str) -> HubSpotResponse:
        """Send a GET request to the HubSpot API."""
        return self._request("GET", path)

    def post(
        self,
        path: str,
        payload: dict[str, Any]
    ) -> HubSpotResponse:
        """Send a POST request to the HubSpot API."""
        return self._request("POST", path, payload)

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None
    ) -> HubSpotResponse:
        """Send an HTTP request and convert the response."""
        response = self._session.request(method, f"{self._base_url}{path}", json=payload)
        time.sleep(self._rate_limit_delay)
        try:
            data = response.json()
        except ValueError:
            data = {}
        return HubSpotResponse(status_code=response.status_code, data=data, text=response.text)
