from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException

from kangaroo.errors import (
    ConflictError,
    InvalidFilterError,
    InvalidReferenceError,
    InvalidTemplateError,
    NotFoundError,
)
from kangaroo.routes import api_v1_router
from kangaroo.runners import RunnerUnavailableError
from kangaroo.settings import settings


class SPAStaticFiles(StaticFiles):
    """Serve index.html for unknown paths to support SPA client-side routing.

    When a file is not found, returns index.html so client-side routing can
    handle the route. This allows browser reloads and direct URL access to work
    for client routes.
    """

    async def get_response(self, path, scope):
        """Get response, falling back to index.html for 404s."""
        try:
            return await super().get_response(path, scope)
        except HTTPException as exc:
            # Check if this is a 404 and the path is not an asset
            if (
                exc.status_code == status.HTTP_404_NOT_FOUND
                and not path.startswith("assets/")
                and path not in ("index.html", "")
            ):
                # Fall back to index.html for unknown paths
                return await super().get_response("index.html", scope)
            raise


app = FastAPI(
    docs_url="/api/v1/docs",
    openapi_url="/api/v1/openapi.json",
    redoc_url=None,
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/web/")


app.include_router(api_v1_router, prefix="/api/v1")


def _error_handler(status_code: int):
    def handler(_request: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(status_code=status_code, content={"detail": str(exc)})

    return handler


app.add_exception_handler(NotFoundError, _error_handler(status.HTTP_404_NOT_FOUND))
app.add_exception_handler(ConflictError, _error_handler(status.HTTP_409_CONFLICT))
app.add_exception_handler(
    InvalidReferenceError, _error_handler(status.HTTP_422_UNPROCESSABLE_CONTENT)
)
app.add_exception_handler(
    InvalidFilterError, _error_handler(status.HTTP_422_UNPROCESSABLE_CONTENT)
)
app.add_exception_handler(
    InvalidTemplateError, _error_handler(status.HTTP_400_BAD_REQUEST)
)
app.add_exception_handler(
    RunnerUnavailableError, _error_handler(status.HTTP_503_SERVICE_UNAVAILABLE)
)


# Web UI serving
# ENV=development: proxies /web to Vite dev server (http://localhost:5173/web)
# ENV=production (default): serves built dist/ folder statically
WEB_DIR = Path(__file__).parent.parent.parent.parent / "web"

if settings.env.lower() == "development":
    # Dev mode: proxy to Vite dev server
    import httpx

    # httpx decodes the body, so these headers no longer describe what we send.
    SKIPPED_PROXY_HEADERS = {
        "content-encoding",
        "content-length",
        "transfer-encoding",
        "connection",
    }

    def _proxy_headers(response: httpx.Response) -> dict[str, str]:
        return {
            k: v
            for k, v in response.headers.items()
            if k.lower() not in SKIPPED_PROXY_HEADERS
        }

    async def _fetch_from_vite(url: str) -> StreamingResponse:
        """Fetch a URL from the Vite dev server and relay it to the client."""
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
        return StreamingResponse(
            iter([response.content]),
            status_code=response.status_code,
            headers=_proxy_headers(response),
        )

    @app.api_route("/web/{path_name:path}", methods=["GET", "HEAD"])
    async def proxy_to_vite(path_name: str, request: Request):
        """Proxy requests to Vite dev server at localhost:5173."""
        vite_url = f"http://localhost:5173/web/{path_name}"
        if request.url.query:
            # Keep query strings such as ?tsr-split=component for code splitting.
            vite_url = f"{vite_url}?{request.url.query}"
        try:
            return await _fetch_from_vite(vite_url)
        except httpx.HTTPError:
            # Fall back to index.html for SPA routing
            return await _fetch_from_vite("http://localhost:5173/web/index.html")
else:
    # Production mode: serve built dist folder
    dist_dir = WEB_DIR / "dist"
    if dist_dir.exists():
        app.mount(
            "/web", SPAStaticFiles(directory=str(dist_dir), html=True), name="web"
        )
