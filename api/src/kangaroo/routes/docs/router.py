import re
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from kangaroo.utils import render_doc_markdown

router = APIRouter(prefix="/docs", tags=["docs"])

# Repository root docs/ folder (api/src/kangaroo/routes/docs/router.py -> repo root)
DOCS_DIR = Path(__file__).parents[5] / "docs"
DOC_NAME = re.compile(r"[a-z0-9-]+")


class Doc(BaseModel):
    name: str
    html: str


@router.get("/{name}", response_model=Doc)
def get_doc(name: str) -> Doc:
    """Render a Markdown file from docs/ to HTML. Use 'index' for the docs home."""
    path = DOCS_DIR / f"{name}.md"
    if not DOC_NAME.fullmatch(name) or not path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Page '{name}' not found"
        )
    return Doc(name=name, html=render_doc_markdown(path.read_text(encoding="utf-8")))
