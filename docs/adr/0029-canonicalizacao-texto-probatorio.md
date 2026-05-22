---
adr: 0029
titulo: Canonicalização determinística de texto para hash probatório
status: aceito
data: 2026-05-23
proposto-por: agente (auditoria rodada 2 — NOVO-ALTO-5 advogado)
revisado-por: advogado-saas-regulado + tech-lead-saas-regulado
aceito-em: 2026-05-23 (necessário pra fechar NOVO-CRIT-2)
bloqueia-fase: Wave A Marco 3 (codificar AceiteAtividade)
depende-de: ADR-0023 (OS com Atividades)
---

# ADR-0029 — Canonicalização determinística de texto para hash probatório

## Contexto

`AceiteAtividade.hash_texto_termo` (modelo OS) e similares (futuros termos de manutenção, devolução, dispensa) usam SHA-256 do texto canônico do termo como prova vinculante. **Sem regra de canonicalização**, dois servidores podem produzir hashes diferentes do mesmo conteúdo lógico:

- Line endings: `LF` (Unix) vs `CRLF` (Windows) — diferença byte-a-byte.
- BOM UTF-8 (`EF BB BF`) — presente ou não no início do arquivo.
- Normalização Unicode: NFC (composto — `é` 1 codepoint) vs NFD (decomposto — `e` + acento 2 codepoints).
- Trailing whitespace por linha — invisível mas modifica hash.
- Encoding: UTF-8 vs UTF-16, ASCII vs Latin-1.

Tribunais já invalidaram aceite eletrônico por inconsistência de hash (TJSP, série 1037xxx-xx). Sem regra, prova Lei 14.063/2020 art. 4º cai.

## Decisão

**Função única `canonicalizar_texto_termo(texto: str) -> bytes`** aplicada ANTES de qualquer SHA-256 para fim probatório.

### Regras de canonicalização

| Aspecto | Regra | Justificativa |
|---|---|---|
| **Encoding** | UTF-8 sem BOM | Padrão Unicode universal |
| **Line endings** | `\n` (LF) — converter `\r\n`/`\r` em LF | POSIX padrão |
| **Normalização Unicode** | NFC (Composto) — `unicodedata.normalize("NFC", texto)` | RFC 3629 + W3C; preserva legibilidade |
| **Trailing whitespace** | Remover `[ \t]+$` em cada linha | Invisível ao humano, varia entre editores |
| **Trailing newlines** | Garantir exatamente 1 `\n` no fim do arquivo | Convenção POSIX |
| **Leading/trailing newlines no corpo** | Strip (`texto.strip("\n")`) | Imune a edição estilística |
| **Tabs vs spaces** | Preservar como está | Mudança altera intenção |
| **BIDI control chars (U+202A-U+202E, U+2066-U+2069)** | Rejeitar (RuntimeError) | Bidirectional text spoofing attack vector |

### Implementação de referência

```python
import unicodedata

BIDI_CONTROL = {chr(c) for c in (0x202A, 0x202B, 0x202C, 0x202D, 0x202E,
                                  0x2066, 0x2067, 0x2068, 0x2069)}

def canonicalizar_texto_termo(texto: str) -> bytes:
    """Canonicaliza texto para hash probatório (ADR-0029).

    Determinístico: mesmo input lógico produz mesmo output byte-a-byte
    em qualquer plataforma. Bloqueia BIDI control chars.
    """
    if any(c in texto for c in BIDI_CONTROL):
        raise CanonicalizacaoBidiRejeitada(
            "BIDI control char proibido em texto probatório (ADR-0029)"
        )
    # 1. Normalizar Unicode
    texto = unicodedata.normalize("NFC", texto)
    # 2. Normalizar line endings (CRLF → LF; CR → LF)
    texto = texto.replace("\r\n", "\n").replace("\r", "\n")
    # 3. Remover trailing whitespace por linha
    texto = "\n".join(linha.rstrip(" \t") for linha in texto.split("\n"))
    # 4. Strip leading/trailing newlines + garantir 1 newline no fim
    texto = texto.strip("\n") + "\n"
    # 5. Encoding UTF-8 sem BOM
    return texto.encode("utf-8")
```

### Extração do corpo de termos versionados

Texto canônico vive em `docs/conformidade/comum/termos/<slug>-vN.md` entre marcadores literais:

```
<<<CORPO INICIO>>>
... texto do termo ...
<<<CORPO FIM>>>
```

Função `extrair_corpo_termo(arquivo: Path) -> str` lê arquivo, encontra marcadores, retorna conteúdo entre eles (excluindo as próprias linhas dos marcadores). Hash é aplicado SOBRE o resultado de `canonicalizar_texto_termo(corpo)`.

### Hash final

```python
import hashlib

def hash_texto_termo(arquivo: Path) -> bytes:
    """Hash SHA-256 canonicalizado do corpo do termo versionado."""
    corpo = extrair_corpo_termo(arquivo)
    return hashlib.sha256(canonicalizar_texto_termo(corpo)).digest()
```

Retorno: `bytes` de 32 bytes. Armazenado em `AceiteAtividade.hash_texto_termo` (`bytea` no PostgreSQL).

## Caminhos alternativos considerados

| Alternativa | Por que NÃO |
|---|---|
| Hash do arquivo inteiro (incluindo frontmatter) | Frontmatter `revisado_em` muda sem alterar conteúdo legal — invalidaria aceites antigos |
| JSON canonicalization (RFC 8785) | Texto narrativo não é JSON; complexidade injustificada |
| Sem canonicalização (hash do arquivo cru) | LF vs CRLF entre dev/prod já produz hash diferente — quebra prova |
| Markdown rendering → HTML → hash | Engine de markdown não-determinístico entre versões |

## Consequências

### Positivas

- Hash determinístico cross-platform (Linux dev, Windows local, Docker prod).
- Prova Lei 14.063/2020 art. 4º robusta — perito reproduz hash em qualquer ambiente.
- Resistente a BIDI attack (caracteres invisíveis que mudam meaning).
- Versões antigas de termos continuam verificáveis: basta preservar o arquivo Markdown da versão.

### Negativas (mitigáveis)

- Editor que adiciona BOM (Notepad Windows) quebra hash → solução: hook `pre-commit` strip BOM em `docs/conformidade/comum/termos/`.
- Trailing whitespace varia entre editores → solução: hook `pre-commit` + `.editorconfig` em pasta termos.

## Non-goals

- NÃO normaliza ortografia ou case-sensitivity (`Calibração` ≠ `calibração`).
- NÃO traduz idiomas (cada idioma = versão própria — `aceite-atividade-en-v1.0.md`).
- NÃO aplica-se a hash não-probatório (audit interno, payload sanitization — esses usam HMAC tenant-key).

## Invariante nova

- **INV-DOC-CANON-001:** todo arquivo em `docs/conformidade/comum/termos/` é canonicalizável (passa por `canonicalizar_texto_termo` sem RuntimeError + extrai corpo válido entre marcadores). Hook `termo-canonicalizacao-check.sh` valida no pre-commit.

## Implicações pro faseamento

- Marco 3 P4 implementa `canonicalizar_texto_termo` + `extrair_corpo_termo` + `hash_texto_termo` em utility module.
- Hook `termo-canonicalizacao-check.sh` (Wave A Marco 3) bloqueia commit que toca pasta `termos/` com BIDI ou marcadores ausentes.
- Aceite `AceiteAtividade.versao_termo = "v1.0-2026-05-23"` referencia arquivo `aceite-atividade-v1.0.md`.

## Status

Aceito 2026-05-23. Pré-requisito de codificar `AceiteAtividade` no Marco 3 P4.
