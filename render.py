"""
Motor de template visual — transforma slides estruturados em arte PNG
no padrão visual da marca (definido em marca_visual.py).

Uso:
  python render.py exemplo_slides.json
  python render.py meu_post.json pasta_de_saida

Lê um JSON com uma lista "slides" e gera um PNG por slide (1080x1350,
tamanho de carrossel do Instagram) numa pasta de saída. Não acessa
Instagram nem banco — só lê JSON e escreve PNG local.

Como funciona: pra cada slide, preenche o template slide.html.j2, abre num
navegador headless (Playwright) e tira um "print" da tela. É o mesmo HTML que
você pode abrir no browser pra pré-visualizar antes de instalar qualquer coisa.
"""

import json
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from marca_visual import MARCA_VISUAL

LARGURA, ALTURA = 1080, 1350
AQUI = Path(__file__).parent


def _montar_html(slide: dict, total: int, indice: int) -> str:
    """Preenche o template de um slide e devolve o HTML pronto."""
    env = Environment(loader=FileSystemLoader(str(AQUI)))
    template = env.get_template("slide.html.j2")
    return template.render(
        slide=slide, marca=MARCA_VISUAL, total=total, indice=indice
    )


def render_carrossel(slides: list, pasta_saida: str = "saida") -> list:
    """Gera um PNG por slide e devolve a lista de caminhos criados."""
    # Import tardio: só quem renderiza precisa do Playwright instalado.
    from playwright.sync_api import sync_playwright

    pasta = Path(pasta_saida)
    pasta.mkdir(parents=True, exist_ok=True)

    criados = []
    with sync_playwright() as p:
        navegador = p.chromium.launch()
        pagina = navegador.new_page(viewport={"width": LARGURA, "height": ALTURA})
        for i, slide in enumerate(slides, start=1):
            html = _montar_html(slide, total=len(slides), indice=i)
            pagina.set_content(html, wait_until="networkidle")
            caminho = pasta / f"slide_{i:02d}.png"
            pagina.screenshot(path=str(caminho))
            criados.append(caminho)
        navegador.close()

    return criados


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    arquivo = sys.argv[1]
    pasta_saida = sys.argv[2] if len(sys.argv) > 2 else "saida"

    with open(arquivo, encoding="utf-8") as f:
        dados = json.load(f)

    # Aceita tanto {"slides": [...]} quanto uma lista direta.
    slides = dados["slides"] if isinstance(dados, dict) else dados

    print(f"Gerando {len(slides)} slides...")
    criados = render_carrossel(slides, pasta_saida)
    for c in criados:
        print(f"  ok  {c}")
    print(f"\nPronto! {len(criados)} imagens em: {pasta_saida}/")


if __name__ == "__main__":
    main()