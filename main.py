from pathlib import Path
import sqlite3
from typing import List

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "app.db"


def init_db() -> None:
    """Cria/atualiza o SQLite local (`app.db`). Todo envio do formulário de conversão é persistido aqui primeiro."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS forms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT,
                email TEXT NOT NULL,
                service_type TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
            )
            """
        )
        cursor.execute("PRAGMA table_info(forms)")
        existing_cols = {row[1] for row in cursor.fetchall()}
        if "phone" not in existing_cols:
            cursor.execute("ALTER TABLE forms ADD COLUMN phone TEXT")
        if "service_type" not in existing_cols:
            cursor.execute("ALTER TABLE forms ADD COLUMN service_type TEXT")
        if "created_at" not in existing_cols:
            cursor.execute(
                "ALTER TABLE forms ADD COLUMN created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))"
            )
        conn.commit()


init_db()

app = FastAPI()

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


def _list_static_images(subdir: str) -> List[str]:
    out: List[str] = []
    d = BASE_DIR / "static" / subdir
    if not d.is_dir():
        return out
    exts = {".jpg", ".jpeg", ".png", ".webp", ".svg"}
    for p in sorted(d.iterdir()):
        if p.is_file() and p.suffix.lower() in exts:
            out.append(f"{subdir}/{p.name}")
    return out


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    carousel_images = _list_static_images("carrossel")
    clientes_logos = _list_static_images("clientes")

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "carousel_images": carousel_images,
            "clientes_logos": clientes_logos,
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
    # Persistência principal: sempre gravar no SQLite antes de qualquer outra ação futura (e-mail, CRM, etc.)
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO forms (name, phone, email, service_type, created_at)
            VALUES (?, ?, ?, ?, datetime('now', 'localtime'))
            """,
            (name.strip(), phone.strip(), email.strip(), service_type),
        )
        conn.commit()

    return RedirectResponse(url="/", status_code=303)


@app.get("/health", response_class=HTMLResponse)
async def health() -> HTMLResponse:
    return HTMLResponse("ok")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)
