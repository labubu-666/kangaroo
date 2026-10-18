from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.responses import (
    JSONResponse,
    PlainTextResponse,
    RedirectResponse,
    StreamingResponse,
)
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException
from starlette.middleware.sessions import SessionMiddleware

from kangaroo.errors import (
    ConflictError,
    InvalidFilterError,
    InvalidReferenceError,
    InvalidTemplateError,
    NotFoundError,
)
from kangaroo.routes import api_v1_router
from kangaroo.routes.auth import router as auth_router
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
            if (
                exc.status_code == status.HTTP_404_NOT_FOUND
                and not path.startswith("assets/")
                and path not in ("index.html", "")
            ):
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


app.add_middleware(SessionMiddleware, secret_key=settings.session_secret_key)
app.include_router(auth_router)
app.include_router(api_v1_router, prefix="/api/v1")


def _error_handler(status_code: int):
    def handler(_request: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(status_code=status_code, content={"detail": str(exc)})

    return handler


ERROR_STATUS_CODES: dict[type[ValueError], int] = {
    NotFoundError: status.HTTP_404_NOT_FOUND,
    ConflictError: status.HTTP_409_CONFLICT,
    InvalidReferenceError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    InvalidFilterError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    InvalidTemplateError: status.HTTP_400_BAD_REQUEST,
    RunnerUnavailableError: status.HTTP_503_SERVICE_UNAVAILABLE,
}
for error_type, status_code in ERROR_STATUS_CODES.items():
    app.add_exception_handler(error_type, _error_handler(status_code))


# Web UI serving
# ENV=development: proxies /web to Vite dev server (http://localhost:5173/web)
# ENV=production (default): serves built dist/ folder statically
WEB_DIR = Path(__file__).parent.parent.parent.parent / "web"

if settings.env.lower() == "development":
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
        except httpx.ConnectError:
            return PlainTextResponse(
                "Vite dev server is not running on http://localhost:5173. "
                "Start it with `npm run dev` in web/.",
                status_code=502,
            )
        except httpx.HTTPError:
            return await _fetch_from_vite("http://localhost:5173/web/index.html")
else:
    dist_dir = WEB_DIR / "dist"
    if dist_dir.exists():
        app.mount(
            "/web", SPAStaticFiles(directory=str(dist_dir), html=True), name="web"
        )
