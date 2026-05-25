# app/services/backend/client.py

import httpx

from app.config.settings import (
    settings,
)

from app.config.logging import (
    get_logger,
)


logger = get_logger("backend-client")


# =========================================================
# SHARED ERROR RESPONSE BUILDER
# =========================================================
def _http_error_response(status_code: int, url: str) -> dict:
    """
    Return a structured error dict for HTTP failures.
    401 gets a specific message so token issues are obvious in logs.
    """
    if status_code == 401:
        return {
            "error": "backend_unauthorized",
            "message": (
                "Backend returned 401 Unauthorized. "
                "Check AUTH_TOKEN in .env — it may be expired or missing."
            ),
            "data": [],
        }
    return {
        "error": "backend_http_error",
        "message": f"Backend returned {status_code}",
        "data": [],
    }


def _connect_error_response(base_url: str) -> dict:
    return {
        "error": "backend_unavailable",
        "message": (
            f"Cannot connect to backend at {base_url}. "
            "Please ensure the backend API is running."
        ),
        "data": [],
    }


# =========================================================
# BACKEND CLIENT
# =========================================================
class BackendClient:

    def __init__(self):

        self.base_url = settings.BACKEND_BASE_URL
        self.timeout = 60

    # =====================================================
    # DEFAULT HEADERS
    # =====================================================
    def default_headers(self) -> dict:
        # Re-read from settings on every call so token rotations
        # (e.g. updating .env and restarting) are always picked up.
        # AUTH_TOKEN takes priority over BACKEND_API_KEY.
        token = settings.AUTH_TOKEN or settings.BACKEND_API_KEY

        if not token:
            logger.warning(
                "No auth token configured — "
                "set AUTH_TOKEN or BACKEND_API_KEY in .env"
            )

        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    # =====================================================
    # GET
    # =====================================================
    async def get(
        self,
        endpoint: str,
        params: dict | None = None,
    ):
        url = f"{self.base_url}{endpoint}"
        logger.info("Backend GET request", url=url)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    url,
                    params=params,
                    headers=self.default_headers(),
                )
                response.raise_for_status()
                return response.json()

        except httpx.ConnectError:
            logger.error("Backend unreachable", url=url)
            return _connect_error_response(self.base_url)

        except httpx.HTTPStatusError as e:
            logger.error("Backend HTTP error", url=url, status=e.response.status_code)
            return _http_error_response(e.response.status_code, url)

    # =====================================================
    # POST
    # =====================================================
    async def post(
        self,
        endpoint: str,
        data: dict | list | None = None,
        params: dict | None = None,
    ):
        url = f"{self.base_url}{endpoint}"
        logger.info("Backend POST request", url=url)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    json=data,
                    params=params,
                    headers=self.default_headers(),
                )
                response.raise_for_status()
                return response.json()

        except httpx.ConnectError:
            logger.error("Backend unreachable", url=url)
            return _connect_error_response(self.base_url)

        except httpx.HTTPStatusError as e:
            logger.error("Backend HTTP error", url=url, status=e.response.status_code)
            return _http_error_response(e.response.status_code, url)

    # =====================================================
    # PATCH
    # =====================================================
    async def patch(
        self,
        endpoint: str,
        data: dict | None = None,
        params: dict | None = None,
    ):
        url = f"{self.base_url}{endpoint}"
        logger.info("Backend PATCH request", url=url)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.patch(
                    url,
                    json=data,
                    params=params,
                    headers=self.default_headers(),
                )
                response.raise_for_status()
                return response.json()

        except httpx.ConnectError:
            logger.error("Backend unreachable", url=url)
            return _connect_error_response(self.base_url)

        except httpx.HTTPStatusError as e:
            logger.error("Backend HTTP error", url=url, status=e.response.status_code)
            return _http_error_response(e.response.status_code, url)

    # =====================================================
    # PUT
    # =====================================================
    async def put(
        self,
        endpoint: str,
        data: dict | None = None,
    ):
        url = f"{self.base_url}{endpoint}"
        logger.info("Backend PUT request", url=url)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.put(
                    url,
                    json=data,
                    headers=self.default_headers(),
                )
                response.raise_for_status()
                return response.json()

        except httpx.ConnectError:
            logger.error("Backend unreachable", url=url)
            return _connect_error_response(self.base_url)

        except httpx.HTTPStatusError as e:
            logger.error("Backend HTTP error", url=url, status=e.response.status_code)
            return _http_error_response(e.response.status_code, url)

    # =====================================================
    # DELETE
    # =====================================================
    async def delete(
        self,
        endpoint: str,
        data: dict | None = None,
    ):
        url = f"{self.base_url}{endpoint}"
        logger.info("Backend DELETE request", url=url)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method="DELETE",
                    url=url,
                    json=data,
                    headers=self.default_headers(),
                )
                response.raise_for_status()

                # Some DELETE endpoints return 204 No Content
                if response.status_code == 204:
                    return {"success": True}

                return response.json()

        except httpx.ConnectError:
            logger.error("Backend unreachable", url=url)
            return _connect_error_response(self.base_url)

        except httpx.HTTPStatusError as e:
            logger.error("Backend HTTP error", url=url, status=e.response.status_code)
            return _http_error_response(e.response.status_code, url)


backend_client = BackendClient()
