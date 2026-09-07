# Gerador de Posts

Gera posts de Instagram **originais** a partir de uma referência: você dá o texto ou imagem
de um post que curtiu + o tema que quer abordar, e a ferramenta extrai a *fórmula*
da referência (formato, gancho, estrutura) e escreve um post novo na voz da sua
marca — já renderizado como carrossel em imagem.

A referência serve de molde estrutural; o conteúdo que sai é seu, não uma cópia.

## Como funciona

```
referência + tema
      │
      ▼
1. analisa a referência   → extrai o "esqueleto" (formato, gancho, estrutura, tom)
2. gera o post            → conteúdo original na voz da marca (slides + legenda + hashtags)
3. renderiza              → transforma os slides em imagens PNG no visual da marca
      │
      ▼
pasta com post.json + legenda.txt + slides PNG
```

O motor de IA é **trocável**: roda no Gemini (grátis) ou no Claude, escolhido no `.env`.

> Opcional: em vez de escrever a voz da marca na mão no `config.py`, dá pra
> gerá-la a partir de prints do perfil — veja "Aprender a marca" abaixo.

## Instalação

```bash
pip install -r requirements.txt
playwright install chromium      # navegador headless que "printa" os slides (uma vez só)
cp .env.example .env             # depois preencha a chave dentro
```

No `.env`, preencha pelo menos:

```
PROVEDOR=gemini
GEMINI_API_KEY=sua-chave-do-google-ai-studio
MODELO_GEMINI=gemini-3.6-flash
```

Chave do Gemini (grátis, sem cartão): https://aistudio.google.com/apikey

## Teste rápido

**1. Testar só o visual** (não gasta chamada de IA — renderiza o exemplo pronto):

```bash
python render.py exemplo_slides.json
```

Deve criar a pasta `saida/` com 6 slides PNG. Se as imagens saírem, o motor
visual tá ok.

**2. Testar o fluxo completo** (gera texto + arte a partir de uma referência):

```bash
python criar.py "3 erros que todo comércio comete no PDV: não treinar a equipe, ignorar o controle de estoque e não olhar relatório de vendas" "por que um sistema sob medida evita esses erros"
```

Deve criar uma pasta em `posts/` com `post.json`, `legenda.txt` e os slides.
Se sair tudo, o pipeline inteiro tá funcionando.

## Uso

**Comando único (o do dia a dia)** — faz tudo, da referência à arte:

```bash
python criar.py "texto da referência" "tema do seu post"
```

Cria uma pasta (ex: `posts/2026-09-07_seu-tema/`) com:
- `post.json` — dados do post
- `legenda.txt` — legenda + hashtags prontas pra colar no Instagram
- `slide_01.png` … — as artes do carrossel

**Comandos separados (pra testar cada metade):**

```bash
python cli.py analisar "referência"           # só mostra o esqueleto extraído
python cli.py gerar "referência" "tema"        # só o texto (sem renderizar)
python render.py post.json                     # só renderiza slides de um JSON
python render.py exemplo_slides.json           # renderiza o exemplo (útil pra ajustar o visual)
```

## Aprender a marca (opcional)

Gera a voz da marca (`config.py`) a partir de prints do perfil, em vez de
escrever na mão. Roda uma vez, ou quando a marca mudar.

```bash
mkdir prints_perfil          # coloque prints do perfil aqui (bio, grade, legendas)
python aprender_marca.py
```

A IA extrai a voz, mostra na tela e pergunta se grava. Ao gravar, a marca nova
entra ativa e a anterior fica comentada no `config.py` (nada é apagado). Só a
voz é extraída; as cores (`marca_visual.py`) você ajusta na mão.

## Configuração

| Arquivo            | O que ajusta                                              |
|--------------------|-----------------------------------------------------------|
| `.env`             | chaves de API e qual IA usar (`PROVEDOR`)                 |
| `config.py`        | a **voz** da marca (tom, público, valores)                |
| `marca_visual.py`  | a **cara** da marca (cores, fonte, @)                     |
| `slide.html.j2`    | o layout dos slides (HTML/CSS — edite como web)           |

### Trocar pro Claude

Quando tiver a chave da Anthropic, no `.env`: mude `PROVEDOR=claude` e preencha
`ANTHROPIC_API_KEY` e `MODELO_CLAUDE`. Nenhuma mudança de código.

## Estrutura

```
criar.py           fluxo completo (gerar + renderizar)
aprender_marca.py  extrai a voz da marca de prints do perfil (opcional)
cli.py             gerador de texto (analisar / gerar)
render.py          motor visual (slides → PNG)
gerador.py         lógica do cérebro + motor de IA trocável
config.py          voz da marca
marca_visual.py    visual da marca
slide.html.j2      template dos slides
exemplo_slides.json exemplo pra testar o visual
requirements.txt   dependências
.env               chaves (não versionar)
```

## Notas

- **Só publica você.** A ferramenta gera e salva as artes no seu PC; postar é manual,
  na sua conta oficial. Não há scraping nem automação de conta de Instagram.
- **Formato JSON:** o modelo precisa devolver os slides no formato certo. O Gemini
  Flash às vezes escorrega — se der erro, rode de novo. No Claude isso é mais raro.
- **Texto longo pode vazar** do slide (tamanho de fonte fixo). Ajuste o texto ou o
  CSS em `slide.html.j2` por enquanto.