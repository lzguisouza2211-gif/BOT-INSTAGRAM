"""
Aprende a VOZ da marca a partir de prints do perfil do Instagram.

Coloque prints do perfil (bio, grade de posts, legendas visíveis) na pasta
prints_perfil/ e rode:

    python aprender_marca.py

A IA lê os prints, extrai a identidade da marca (nome, nicho, voz, público,
valores, o que evitar) e mostra a proposta na tela. Se você aprovar, ela
reescreve o config.py: a marca nova entra ATIVA e a anterior fica logo abaixo,
COMENTADA — nada é apagado.

Roda uma vez (ou quando a marca mudar), não faz parte do fluxo de cada post.
Só a VOZ é extraída aqui; as cores (marca_visual.py) você ajusta na mão.
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

from gerador import _chamar_modelo_com_imagens, _parse_json

PASTA_PRINTS = Path("prints_perfil")
CONFIG = Path("config.py")
EXTENSOES = (".png", ".jpg", ".jpeg", ".webp")


def _dict_para_python(marca: dict) -> str:
    """Converte o dict da marca em código Python formatado (MARCA = {...})."""
    def aspas(x):
        return '"' + str(x).replace('"', '\\"') + '"'

    linhas = ["MARCA = {"]
    for chave, valor in marca.items():
        if isinstance(valor, list):
            itens = ", ".join(aspas(x) for x in valor)
            linhas.append(f'    "{chave}": [{itens}],')
        else:
            linhas.append(f'    "{chave}": {aspas(valor)},')
    linhas.append("}")
    return "\n".join(linhas) + "\n"


def _reescrever_config(nova_marca: dict):
    """Coloca a nova MARCA ativa em cima e comenta a anterior. Não apaga nada."""
    conteudo = CONFIG.read_text(encoding="utf-8")
    achou = re.search(r"^MARCA\s*=", conteudo, re.M)

    if achou:
        cabecalho = conteudo[:achou.start()]
        bloco_antigo = conteudo[achou.start():]
    else:
        cabecalho, bloco_antigo = conteudo, ""

    data = datetime.now().strftime("%Y-%m-%d %H:%M")
    partes = [cabecalho.rstrip() + "\n\n", _dict_para_python(nova_marca)]

    if bloco_antigo.strip():
        comentado = "\n".join(
            ("# " + linha) if linha.strip() else "#"
            for linha in bloco_antigo.splitlines()
        )
        partes.append(f"\n\n# --- marca anterior (comentada em {data}) ---\n")
        partes.append(comentado + "\n")

    CONFIG.write_text("".join(partes), encoding="utf-8")


def main():
    if not PASTA_PRINTS.exists():
        PASTA_PRINTS.mkdir()
        print(f"Criei a pasta {PASTA_PRINTS}/. Coloque os prints do perfil lá e rode de novo.")
        sys.exit(0)

    prints = sorted(p for p in PASTA_PRINTS.iterdir() if p.suffix.lower() in EXTENSOES)
    if not prints:
        print(f"Nenhum print em {PASTA_PRINTS}/. "
              f"Coloque imagens ({', '.join(EXTENSOES)}) e rode de novo.")
        sys.exit(0)

    print(f"Lendo {len(prints)} print(s) do perfil...")

    prompt = """Você está vendo prints do perfil de Instagram de uma marca (bio,
grade de posts, legendas visíveis). Extraia a IDENTIDADE da marca pra alimentar
um gerador de conteúdo.

Devolva SOMENTE um JSON válido, sem cercas de markdown, com estas chaves:
- "nome": nome da marca
- "nicho": nicho/segmento em uma frase
- "voz": como a marca fala (tom, estilo), em uma frase
- "publico": público-alvo, em uma frase
- "valores": lista de 3 a 5 valores/pilares
- "evitar": lista de 2 a 4 coisas que a marca deve evitar no conteúdo

Se algo não der pra inferir dos prints, use um valor curto e razoável."""

    bruto = _chamar_modelo_com_imagens(prompt, prints, max_tokens=1024)

    try:
        nova = _parse_json(bruto)
    except Exception:
        print("A IA não devolveu um JSON válido. Rode de novo.")
        print("Resposta crua:\n", bruto)
        sys.exit(1)

    print("\n=== MARCA EXTRAÍDA DOS PRINTS ===")
    print(json.dumps(nova, ensure_ascii=False, indent=2))

    resp = input(
        "\nGravar essa marca no config.py? (a atual será comentada) (s/n): "
    ).strip().lower()
    if resp not in ("s", "sim"):
        print("Cancelado. Nada foi alterado.")
        sys.exit(0)

    _reescrever_config(nova)
    print("Pronto! config.py atualizado (marca anterior preservada, comentada).")


if __name__ == "__main__":
    main()