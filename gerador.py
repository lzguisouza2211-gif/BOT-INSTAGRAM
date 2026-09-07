"""
Gerador de posts — o cérebro do pipeline.

Duas etapas SEPARADAS, de propósito, pra você testar cada uma isolada:
  1. analisar_referencia(texto)          -> extrai o "esqueleto" da referência
  2. gerar_post(esqueleto, marca, tema)  -> cria um post ORIGINAL seu em cima do esqueleto

Nenhuma das duas acessa Instagram nem banco de dados. Só recebem texto,
conversam com o modelo de IA e devolvem dict. Roda 100% local.

>>> Motor de IA trocável <<<
Quem fala com o modelo é UM ponto só: a função _chamar_modelo(). Ela roteia
pro provedor escolhido no .env (PROVEDOR=gemini | claude). Trocar de motor é
mudar uma linha no .env — o resto do pipeline nem percebe.
"""

import base64
import json
import os
import re
import time

from dotenv import load_dotenv

# Carrega o .env (chaves e escolha de provedor). Chaves NUNCA vão no código.
load_dotenv()

# Qual motor usar: "gemini" (grátis pra testar) ou "claude".
PROVEDOR = os.getenv("PROVEDOR", "gemini").lower()

# Modelos configuráveis por .env, um pra cada provedor.
MODELO_GEMINI = os.getenv("MODELO_GEMINI", "gemini-2.5-flash")
MODELO_CLAUDE = os.getenv("MODELO_CLAUDE", "claude-sonnet-5")

# Clients criados sob demanda (lazy): só nasce o do provedor que você escolheu,
# então não precisa ter chave dos dois pra rodar.
_client_gemini = None
_client_claude = None


# ------------------------------------------------------------------
#  ETAPAS DO CÉREBRO (não mudam quando você troca de motor)
# ------------------------------------------------------------------

def analisar_referencia(texto_referencia: str) -> dict:
    """
    Recebe o texto de um post de referência e devolve o esqueleto:
    formato, gancho, estrutura, tom, tema e CTA.

    Descreve a *forma*, não o conteúdo. Retorna um dict.
    """
    prompt = f"""Você é um analista de conteúdo pra Instagram.

Abaixo está o texto de um post de referência. Extraia o ESQUELETO dele — a
estrutura e a fórmula que fizeram ele funcionar — SEM copiar o conteúdo
específico. Pense como engenheiro reverso de formato, não como alguém que vai
reescrever o post.

Devolva SOMENTE um JSON válido, sem cercas de markdown, com estas chaves:
- "formato": tipo de post (carrossel, post único, reels, etc.)
- "gancho": que tipo de gancho abre o post (pergunta, número, promessa, polêmica...)
- "estrutura": lista dos passos de como o conteúdo se organiza
- "tom": registro de voz (informal, técnico, motivacional...)
- "tema": o assunto/nicho geral (não o conteúdo exato)
- "cta": qual a chamada pra ação, se houver

POST DE REFERÊNCIA:
\"\"\"
{texto_referencia}
\"\"\""""

    return _parse_json(_chamar_modelo(prompt, max_tokens=1024))


def analisar_referencia_imagens(caminhos_imagens: list) -> dict:
    """
    Igual a analisar_referencia, mas lê PRINTS de posts (imagens) em vez de texto.
    Extrai o esqueleto — inclusive lendo a legenda embutida na arte da imagem.
    """
    prompt = """Você está vendo prints de posts de Instagram usados como referência.
Extraia o ESQUELETO deles — a estrutura e a fórmula que fazem funcionar — SEM
copiar o conteúdo específico. Leia também o texto que estiver DENTRO das imagens
(legendas embutidas na arte).

Devolva SOMENTE um JSON válido, sem cercas de markdown, com estas chaves:
- "formato": tipo de post (carrossel, post único, reels, etc.)
- "gancho": que tipo de gancho abre o post (pergunta, número, promessa, polêmica...)
- "estrutura": lista dos passos de como o conteúdo se organiza
- "tom": registro de voz (informal, técnico, motivacional...)
- "tema": o assunto/nicho geral (não o conteúdo exato)
- "cta": qual a chamada pra ação, se houver"""

    return _parse_json(_chamar_modelo_com_imagens(prompt, caminhos_imagens, max_tokens=1024))


def gerar_post(esqueleto: dict, marca: dict, tema_do_post: str) -> dict:
    """
    Recebe o esqueleto de uma referência + a config da SUA marca + o tema que
    você quer abordar, e gera um post ORIGINAL seu seguindo aquela fórmula.

    Retorna dict com:
      - "slides": lista de slides estruturados (já no formato que o render.py lê)
      - "legenda": a legenda pro Instagram (texto embaixo da imagem)
      - "hashtags": lista de hashtags
    """
    prompt = f"""Você é o redator de conteúdo da marca descrita abaixo.

Use o ESQUELETO como fôrma estrutural (o formato/fórmula que funciona), mas gere
conteúdo 100% ORIGINAL sobre o tema pedido, na voz da marca. Não reescreva nem
parafraseie nenhum post existente — só siga a *estrutura*.

ESQUELETO (a fôrma a seguir):
{json.dumps(esqueleto, ensure_ascii=False, indent=2)}

MARCA (sua voz e identidade):
{json.dumps(marca, ensure_ascii=False, indent=2)}

TEMA DESTE POST:
{tema_do_post}

Monte o post como um CARROSSEL, quebrado em slides. Os tipos de slide são:

- capa: abre o post. Campos: "tipo":"capa", "destaque" (um número ou palavra
  curta e forte pro texto gigante — ex "3", "5", "PARE"; omita se não fizer
  sentido), "titulo" (a chamada da capa).
- item: cada ponto da lista (um erro, uma dica, um passo...). Campos:
  "tipo":"item", "rotulo" (selo curto — ex "Erro 1", "Dica 2", "Passo 3"),
  "titulo" (a manchete do item), "texto" (1 a 3 frases explicando).
- fechamento: a virada/solução/conclusão. Campos: "tipo":"fechamento",
  "titulo", "texto".
- cta: o último slide. Campos: "tipo":"cta", "titulo", "acoes" (lista de
  objetos {{"icone": um emoji, "texto": a ação — ex salvar, comentar}}).

Regras:
- A quantidade de "item" segue o ESQUELETO (se a fôrma tem 3 pontos, 3 itens).
- Adapte os rótulos ao tema (erros, dicas, passos, mitos...), não force "Erro".
- Textos curtos e diretos: precisam caber numa tela de celular.

Devolva SOMENTE um JSON válido, sem cercas de markdown, com estas chaves:
- "slides": a lista de slides na ordem (capa, itens, fechamento, cta)
- "legenda": a legenda do post pro Instagram, SEM marcações de slide, pronta pra publicar
- "hashtags": lista de hashtags relevantes"""

    return _parse_json(_chamar_modelo(prompt, max_tokens=2048))


# ------------------------------------------------------------------
#  MOTOR DE IA TROCÁVEL (o único ponto que sabe qual provedor é)
# ------------------------------------------------------------------

def _chamar_modelo(prompt: str, max_tokens: int) -> str:
    """Manda o prompt pro provedor escolhido e devolve o texto puro."""
    if PROVEDOR == "gemini":
        return _chamar_gemini(prompt)
    if PROVEDOR == "claude":
        return _chamar_claude(prompt, max_tokens)
    raise ValueError(
        f"PROVEDOR desconhecido: '{PROVEDOR}'. Use 'gemini' ou 'claude' no .env."
    )


def _com_retry(funcao, tentativas: int = 4):
    """
    Executa `funcao` e, se o servidor estiver sobrecarregado (503) ou pedir
    pra desacelerar (429), espera e tenta de novo — 2s, 4s, 8s...

    Só faz retry em erro temporário de servidor. Erro de nome de modelo (404),
    chave inválida (401/403) e afins estouram na hora, sem insistir à toa.
    """
    for tentativa in range(1, tentativas + 1):
        try:
            return funcao()
        except Exception as erro:
            texto = str(erro).lower()
            temporario = any(s in texto for s in ("503", "unavailable", "overloaded",
                                                  "429", "high demand", "rate limit"))
            if not temporario or tentativa == tentativas:
                raise
            espera = 2 ** tentativa  # 2, 4, 8 segundos
            print(f"   servidor ocupado, tentando de novo em {espera}s "
                  f"(tentativa {tentativa}/{tentativas - 1})...")
            time.sleep(espera)


def _chamar_gemini(prompt: str) -> str:
    global _client_gemini
    if _client_gemini is None:
        from google import genai  # lê GEMINI_API_KEY do ambiente automaticamente
        _client_gemini = genai.Client()

    def _chamada():
        resposta = _client_gemini.models.generate_content(
            model=MODELO_GEMINI,
            contents=prompt,
        )
        return (resposta.text or "").strip()

    return _com_retry(_chamada)


def _chamar_claude(prompt: str, max_tokens: int) -> str:
    global _client_claude
    if _client_claude is None:
        from anthropic import Anthropic  # lê ANTHROPIC_API_KEY do ambiente
        _client_claude = Anthropic()

    def _chamada():
        resposta = _client_claude.messages.create(
            model=MODELO_CLAUDE,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(b.text for b in resposta.content if b.type == "text").strip()

    return _com_retry(_chamada)


# ------------------------------------------------------------------
#  CHAMADA COM IMAGENS (multimodal — pra ler prints)
# ------------------------------------------------------------------

_MIMES = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp"}


def _ler_imagens(caminhos: list) -> list:
    """Lê os arquivos de imagem e devolve uma lista de (bytes, mime_type)."""
    saida = []
    for caminho in caminhos:
        ext = str(caminho).lower().rsplit(".", 1)[-1]
        with open(caminho, "rb") as f:
            saida.append((f.read(), _MIMES.get(ext, "image/png")))
    return saida


def _chamar_modelo_com_imagens(prompt: str, caminhos_imagens: list, max_tokens: int) -> str:
    """Igual ao _chamar_modelo, mas manda também imagens (prints) pro modelo."""
    imagens = _ler_imagens(caminhos_imagens)
    if PROVEDOR == "gemini":
        return _chamar_gemini_imagens(prompt, imagens)
    if PROVEDOR == "claude":
        return _chamar_claude_imagens(prompt, imagens, max_tokens)
    raise ValueError(
        f"PROVEDOR desconhecido: '{PROVEDOR}'. Use 'gemini' ou 'claude' no .env."
    )


def _chamar_gemini_imagens(prompt: str, imagens: list) -> str:
    global _client_gemini
    if _client_gemini is None:
        from google import genai
        _client_gemini = genai.Client()
    from google.genai import types

    partes = [prompt]
    for dados, mime in imagens:
        partes.append(types.Part.from_bytes(data=dados, mime_type=mime))

    def _chamada():
        resposta = _client_gemini.models.generate_content(
            model=MODELO_GEMINI, contents=partes
        )
        return (resposta.text or "").strip()

    return _com_retry(_chamada)


def _chamar_claude_imagens(prompt: str, imagens: list, max_tokens: int) -> str:
    global _client_claude
    if _client_claude is None:
        from anthropic import Anthropic
        _client_claude = Anthropic()

    conteudo = []
    for dados, mime in imagens:
        b64 = base64.standard_b64encode(dados).decode()
        conteudo.append({
            "type": "image",
            "source": {"type": "base64", "media_type": mime, "data": b64},
        })
    conteudo.append({"type": "text", "text": prompt})

    def _chamada():
        resposta = _client_claude.messages.create(
            model=MODELO_CLAUDE,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": conteudo}],
        )
        return "".join(b.text for b in resposta.content if b.type == "text").strip()

    return _com_retry(_chamada)


# ------------------------------------------------------------------
#  UTILITÁRIO
# ------------------------------------------------------------------

def _parse_json(bruto: str) -> dict:
    """Remove cercas de markdown que o modelo às vezes adiciona e faz o parse."""
    bruto = re.sub(r"^```(?:json)?\s*", "", bruto.strip())
    bruto = re.sub(r"\s*```$", "", bruto)
    return json.loads(bruto)