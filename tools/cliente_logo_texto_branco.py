"""
Converte texto preto/cinza neutro em branco em logos PNG, mantendo ícones coloridos.
Heurística: pixels com saturação HSV baixa = tipografia/cinza; pixels cromáticos = ícone.
"""
from __future__ import annotations

import colorsys
from pathlib import Path

from PIL import Image

# Ajuste fino: abaixo disso = tratado como cinza/preto (texto)
SAT_MAX = 0.18
# Branco puro / quase branco (ex.: letras brancas dentro do ícone) — não tocar
VAL_KEEP_MIN = 0.97


def pixel_para_branco(r: int, g: int, b: int, a: int) -> tuple[int, int, int, int] | None:
    if a < 35:
        return None
    r_, g_, b_ = r / 255.0, g / 255.0, b / 255.0
    _h, s, v = colorsys.rgb_to_hsv(r_, g_, b_)
    if v >= VAL_KEEP_MIN:
        return None
    if s >= SAT_MAX:
        return None
    return (255, 255, 255, a)


def processar(arquivo: Path) -> int:
    im = Image.open(arquivo).convert("RGBA")
    px = im.load()
    w, h = im.size
    alterados = 0
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            novo = pixel_para_branco(r, g, b, a)
            if novo is not None and (r, g, b, a) != novo:
                px[x, y] = novo
                alterados += 1
    im.save(arquivo, optimize=True)
    return alterados


def main() -> None:
    base = Path(__file__).resolve().parent.parent / "static" / "clientes"
    alvos = [
        "quinto-andar.png",
        "endress-hauser.png",
        "sociedade-brasileira-de-patologia.png",
    ]
    for nome in alvos:
        p = base / nome
        if not p.is_file():
            print(f"[skip] nao encontrado: {p}")
            continue
        n = processar(p)
        print(f"[ok] {nome}: {n} pixels -> branco")


if __name__ == "__main__":
    main()
