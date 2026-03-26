import os
from pathlib import Path
import socket
import sqlite3
from typing import List

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "app.db"


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS forms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT,
                email TEXT NOT NULL,
                service_type TEXT
            )
            """
        )
        # Migração simples se a tabela já existir sem as novas colunas
        cursor.execute("PRAGMA table_info(forms)")
        existing_cols = {row[1] for row in cursor.fetchall()}
        if "phone" not in existing_cols:
            cursor.execute("ALTER TABLE forms ADD COLUMN phone TEXT")
        if "service_type" not in existing_cols:
            cursor.execute("ALTER TABLE forms ADD COLUMN service_type TEXT")
        conn.commit()


init_db()

app = FastAPI()

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    carousel_dir = BASE_DIR / "static" / "carrossel"
    carousel_images: List[str] = []
    if carousel_dir.exists():
        for img_path in sorted(carousel_dir.iterdir()):
            if img_path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
                carousel_images.append(f"carrossel/{img_path.name}")

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "carousel_images": carousel_images,
        },
    )


@app.get("/form", response_class=HTMLResponse)
async def form_get(request: Request):
    return templates.TemplateResponse("form.html", {"request": request})


@app.post("/form")
async def form_post(
    name: str = Form(...),
    phone: str = Form(...),
    email: str = Form(...),
    service_type: str = Form(...),
):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO forms (name, phone, email, service_type) VALUES (?, ?, ?, ?)",
            (name, phone, email, service_type),
        )
        conn.commit()

    return RedirectResponse(url="/", status_code=303)


@app.get("/health", response_class=HTMLResponse)
async def health() -> HTMLResponse:
    return HTMLResponse("ok")


def _try_bind_port(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((host, port))
            return True
        except OSError:
            return False


def _find_free_port(host: str = "127.0.0.1", start: int = 8765, attempts: int = 50) -> int:
    """Primeira porta livre a partir de `start`.

    Padrão 8765 (não 8001): em alguns PCs outro programa usa 8001 e o navegador recebe
    “invalid response” mesmo com uvicorn em outro lugar — evitar 8001 como padrão.
    """
    for port in range(start, start + attempts):
        if _try_bind_port(host, port):
            return port
    raise RuntimeError(f"Nenhuma porta livre entre {start} e {start + attempts - 1}")


def _resolve_dev_port() -> int:
    """PORT ou CMC_PORT força a porta; senão usa a primeira livre a partir de 8765."""
    raw = (os.environ.get("PORT") or os.environ.get("CMC_PORT") or "").strip()
    if raw.isdigit():
        p = int(raw)
        if _try_bind_port("127.0.0.1", p):
            return p
    return _find_free_port()


def run_dev() -> None:
    """Único jeito correto de subir o servidor local: escolhe porta livre (não fixa 8001)."""
    import uvicorn

    port = _resolve_dev_port()
    print("\n" + "=" * 50)
    print("  Abra esta URL com http:// (não https://):")
    print(f"  http://127.0.0.1:{port}/")
    print(f"  http://localhost:{port}/")
    print("=" * 50 + "\n")
    uvicorn.run("main:app", host="127.0.0.1", port=port, reload=True)


if __name__ == "__main__":
    run_dev()
