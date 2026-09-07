"""
Identidade VISUAL da marca — cores, fontes, @ do perfil.

Separado do config.py de propósito: lá é a *voz* (como o texto soa),
aqui é a *cara* (como a arte parece). Edite os hex/fontes pra ajustar o
visual do carrossel sem tocar em código.
"""

MARCA_VISUAL = {
    "nome": "NorthCode",
    "arroba": "@northcode",

    # Fundo escuro levemente azulado (não preto puro — foge do clichê).
    "cor_fundo": "#0B111A",
    "cor_fundo_2": "#111C2B",

    # Textos.
    "cor_texto": "#F5F8FC",
    "cor_texto_suave": "#8DA0B8",

    # Destaques da marca (o verde é o principal; o azul entra no gradiente).
    "cor_destaque": "#12E29A",
    "cor_destaque_2": "#2E9BFF",

    # Fonte. Inter vem do Google Fonts no template; cai pra fonte do sistema
    # se estiver offline.
    "fonte": "'Inter', system-ui, -apple-system, sans-serif",
}