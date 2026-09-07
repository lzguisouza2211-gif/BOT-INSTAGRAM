"""
CLI de baixo nível pra testar o gerador, etapa por etapa.

Uso:
  python cli.py analisar "texto do post de referência aqui"
  python cli.py gerar "texto de referência" "tema do seu post"

- "analisar" só mostra o esqueleto extraído da referência.
- "gerar" faz o fluxo completo: analisa a referência e já gera o seu post
  original em cima dela, usando a voz definida em config.py.
"""

import json
import sys

from config import MARCA
from gerador import analisar_referencia, gerar_post


def _mostrar(titulo, dado):
    print(f"\n=== {titulo} ===")
    print(json.dumps(dado, ensure_ascii=False, indent=2))


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    comando = sys.argv[1]

    if comando == "analisar":
        referencia = sys.argv[2]
        esqueleto = analisar_referencia(referencia)
        _mostrar("ESQUELETO DA REFERÊNCIA", esqueleto)

    elif comando == "gerar":
        if len(sys.argv) < 4:
            print('Faltou o tema. Uso: python cli.py gerar "referência" "tema"')
            sys.exit(1)
        referencia = sys.argv[2]
        tema = sys.argv[3]

        print("Analisando referência...")
        esqueleto = analisar_referencia(referencia)
        _mostrar("ESQUELETO DA REFERÊNCIA", esqueleto)

        print("\nGerando seu post original...")
        post = gerar_post(esqueleto, MARCA, tema)
        _mostrar("POST GERADO", post)

        salvar = input("\nDeseja salvar em um arquivo? (caminho ou Enter para pular): ").strip()
        if salvar:
            with open(salvar, "w", encoding="utf-8") as f:
                json.dump(post, f, ensure_ascii=False, indent=2)
            print(f"Salvo em: {salvar}")

    else:
        print(f"Comando desconhecido: {comando}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
