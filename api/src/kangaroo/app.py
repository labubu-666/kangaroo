from pathlib import Path
from typing import Annotated, Any
from urllib.parse import quote

from fastapi import Depends, FastAPI, Request, status
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import (
    HTMLResponse,
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
from kangaroo.routes.auth import require_user
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
    docs_url=None,
    openapi_url=None,
    redoc_url=None,
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# API docs are served only to logged-in users, so the endpoint list isn't public.
@app.get("/api/v1/openapi.json", include_in_schema=False)
def openapi_schema(_user: Annotated[dict[str, Any], Depends(require_user)]) -> dict:
    return app.openapi()


@app.get("/api/v1/docs", include_in_schema=False)
def swagger_docs(
    _user: Annotated[dict[str, Any], Depends(require_user)],
) -> HTMLResponse:
    return get_swagger_ui_html(
        openapi_url="/api/v1/openapi.json",
        title=f"{app.title} - Swagger UI",
    )


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/web/")


# Send logged-out browsers to login before any web UI page loads. Added before
# SessionMiddleware so that SessionMiddleware (the outer layer) fills the session first.
@app.middleware("http")
async def require_login_for_web(request: Request, call_next):
    path = request.url.path
    is_web = path == "/web" or path.startswith("/web/")
    if is_web and request.method in ("GET", "HEAD") and not request.session.get("user"):
        target = path + (f"?{request.url.query}" if request.url.query else "")
        return RedirectResponse(url=f"/login?next={quote(target, safe='')}")
    return await call_next(request)


app.add_middleware(SessionMiddleware, secret_key=settings.session_secret_key)
app.include_router(auth_router)
app.include_router(api_v1_router, prefix="/api/v1")


def _error_handler(status_code: int):
    def handler(_request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=status_code, content={"detail": str(exc)})

    return handler


ERROR_STATUS_CODES: dict[type[Exception], int] = {
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
