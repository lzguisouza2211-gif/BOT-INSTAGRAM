"""
Fluxo completo: referência + tema  ->  post pronto (texto + arte).

Junta o cérebro (gerador) e o motor visual (render) num comando só, pra você
não rodar os dois na mão nem passar o JSON de um pro outro.

Uso:
  python criar.py "texto da referência" "tema do seu post"
  python criar.py "referência" "tema" minha_pasta

O que ele faz sozinho:
  1. analisa a referência (extrai o esqueleto)
  2. gera o post original seu (slides + legenda + hashtags)
  3. cria uma pasta de saída
  4. salva post.json (dados) e legenda.txt (pra colar no Instagram)
  5. renderiza os slides em PNG

Não acessa Instagram nem banco. Só lê texto e escreve arquivos locais.
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

from config import MARCA
from gerador import analisar_referencia, gerar_post
from render import render_carrossel


def _slug(texto: str, limite: int = 40) -> str:
    """Transforma um texto num nome de pasta seguro (sem espaço/acento/símbolo)."""
    from unicodedata import normalize
    sem_acento = normalize("NFKD", texto).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z0-9]+", "-", sem_acento.lower()).strip("-")
    return s[:limite] or "post"


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    referencia = sys.argv[1]
    tema = sys.argv[2]

    # Pasta de saída: a que você passou, ou uma automática com data + tema.
    if len(sys.argv) > 3:
        pasta = Path(sys.argv[3])
    else:
        carimbo = datetime.now().strftime("%Y-%m-%d")
        pasta = Path("posts") / f"{carimbo}_{_slug(tema)}"

    print("1/3  Analisando referência...")
    esqueleto = analisar_referencia(referencia)

    print("2/3  Gerando seu post...")
    post = gerar_post(esqueleto, MARCA, tema)

    slides = post.get("slides", [])
    if not slides:
        print("A IA não devolveu slides. Rode de novo "
              "(o Flash às vezes escorrega no formato JSON).")
        sys.exit(1)

    pasta.mkdir(parents=True, exist_ok=True)

    # Dados brutos do post (é o que o render lê, e seu histórico).
    (pasta / "post.json").write_text(
        json.dumps(post, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Legenda + hashtags num txt fácil de copiar pro Instagram.
    legenda = post.get("legenda", "")
    hashtags = " ".join(post.get("hashtags", []))
    (pasta / "legenda.txt").write_text(
        f"{legenda}\n\n{hashtags}\n", encoding="utf-8"
    )

    print("3/3  Renderizando os slides...")
    imagens = render_carrossel(slides, str(pasta))

    print(f"\nPronto! Tudo em: {pasta}/")
    print("  - post.json    (dados do post)")
    print("  - legenda.txt  (legenda + hashtags pra colar no Instagram)")
    print(f"  - {len(imagens)} slides PNG")


if __name__ == "__main__":
    main()