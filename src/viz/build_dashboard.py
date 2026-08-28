"""
PULSO - Empacotamento do dashboard
==================================
Injeta o payload de dados no template e gera duas saidas a partir da MESMA
fonte, para evitar divergencia entre elas:

  dashboard/index.html      documento completo, publicavel no GitHub Pages
  dashboard/artifact.html   fragmento sem <html>/<head>/<body>, para publicacao
                            como pagina hospedada

Os dados viajam embutidos num bloco <script type="application/json">, o que
mantem o painel funcional offline e sem servidor - requisito pratico para a
demonstracao do video pitch.
"""

from __future__ import annotations

import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
DASH = BASE / "dashboard"

TITULO = "PULSO"
DESCRICAO = ("Painel de acesso hospitalar do SUS no estado de Sao Paulo - "
             "Equipe Vital Analytics, Challenge Oracle + FIAP 2026.")


def construir() -> None:
    template = (DASH / "_template.html").read_text(encoding="utf-8")
    dados = (DASH / "dados.json").read_text(encoding="utf-8")

    # Protege o payload contra fechamento prematuro da tag <script>.
    dados_seguro = dados.replace("</", "<\\/")
    pagina = template.replace("__DADOS__", dados_seguro)

    (DASH / "artifact.html").write_text(pagina, encoding="utf-8")

    documento = (
        "<!doctype html>\n"
        '<html lang="pt-BR">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f'<meta name="description" content="{DESCRICAO}">\n'
        '<meta name="color-scheme" content="light dark">\n'
        f"{pagina}\n"
        "</html>\n"
    )
    # O template ja traz <title>, <link> e <style> no topo e o markup em
    # seguida; o navegador reposiciona head/body corretamente.
    (DASH / "index.html").write_text(documento, encoding="utf-8")

    for nome in ("index.html", "artifact.html"):
        kb = (DASH / nome).stat().st_size / 1024
        print(f"  -> dashboard/{nome}: {kb:.0f} KB")


if __name__ == "__main__":
    construir()
