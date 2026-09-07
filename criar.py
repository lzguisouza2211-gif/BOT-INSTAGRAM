"""
Fluxo completo: gera um post (texto + arte) a partir de uma referência.

Dois modos:

  # Por PRINTS (padrão): coloque prints de posts em prints_ref/ e rode
  python criar.py "tema do seu post"

  # Por TEXTO: cole a referência na linha de comando
  python criar.py --texto "texto da referência" "tema do seu post"

O TEMA é o assunto do SEU post (o print dá a fôrma; o tema dá o recheio).
Quanto mais específico o tema (assunto + ângulo + público), melhor o resultado.

Em ambos os modos usa a voz da marca (config.py) e o visual (slide.html.j2 /
marca_visual.py). Cria uma pasta em posts/ com post.json, legenda.txt e os
slides PNG. Não acessa Instagram nem banco.
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

from config import MARCA
from gerador import (
    analisar_referencia,
    analisar_referencia_imagens,
    gerar_post,
)
from render import render_carrossel

PASTA_PRINTS = Path("prints_ref")
EXTENSOES = (".png", ".jpg", ".jpeg", ".webp")


def _slug(texto: str, limite: int = 40) -> str:
    """Transforma o tema num nome de pasta seguro (sem espaço/acento/símbolo)."""
    from unicodedata import normalize
    sem_acento = normalize("NFKD", texto).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z0-9]+", "-", sem_acento.lower()).strip("-")
    return s[:limite] or "post"


def _finalizar(esqueleto: dict, tema: str):
    """Gera o post a partir do esqueleto, salva os arquivos e renderiza a arte."""
    print("Gerando seu post...")
    post = gerar_post(esqueleto, MARCA, tema)

    slides = post.get("slides", [])
    if not slides:
        print("A IA não devolveu slides. Rode de novo "
              "(o Flash às vezes escorrega no formato JSON).")
        sys.exit(1)

    carimbo = datetime.now().strftime("%Y-%m-%d")
    pasta = Path("posts") / f"{carimbo}_{_slug(tema)}"
    pasta.mkdir(parents=True, exist_ok=True)

    (pasta / "post.json").write_text(
        json.dumps(post, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    legenda = post.get("legenda", "")
    hashtags = " ".join(post.get("hashtags", []))
    (pasta / "legenda.txt").write_text(f"{legenda}\n\n{hashtags}\n", encoding="utf-8")

    print("Renderizando os slides...")
    imagens = render_carrossel(slides, str(pasta))

    print(f"\nPronto! Tudo em: {pasta}/")
    print(f"  - post.json, legenda.txt e {len(imagens)} slides PNG")


def _modo_texto(args: list):
    if len(args) < 2:
        print('Modo texto: python criar.py --texto "referência" "tema"')
        sys.exit(1)
    referencia, tema = args[0], args[1]
    print("Analisando a referência (texto)...")
    esqueleto = analisar_referencia(referencia)
    _finalizar(esqueleto, tema)


def _modo_prints(args: list):
    if len(args) < 1:
        print('Modo prints: python criar.py "tema"  (com prints em prints_ref/)')
        sys.exit(1)
    tema = args[0]

    if not PASTA_PRINTS.exists():
        PASTA_PRINTS.mkdir()
        print(f"Criei a pasta {PASTA_PRINTS}/. Coloque prints de posts lá e rode de novo.")
        sys.exit(0)

    prints = sorted(p for p in PASTA_PRINTS.iterdir() if p.suffix.lower() in EXTENSOES)
    if not prints:
        print(f"Nenhum print em {PASTA_PRINTS}/. Coloque imagens e rode de novo,")
        print('ou use o modo texto: python criar.py --texto "referência" "tema"')
        sys.exit(0)

    print(f"Analisando {len(prints)} print(s) de referência...")
    esqueleto = analisar_referencia_imagens(prints)
    _finalizar(esqueleto, tema)


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)

    if args[0] in ("--texto", "-t"):
        _modo_texto(args[1:])
    else:
        _modo_prints(args)


if __name__ == "__main__":
    main()