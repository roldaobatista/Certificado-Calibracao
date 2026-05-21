"""T-CLI-117 (AC-CLI-006-4) — validador anti-PII sensível em campos livres.

LGPD art. 11 (taxativa fechada do art. 5º II): origem racial/étnica,
convicção religiosa, opinião política, filiação sindical/organização
religiosa/filosófica/política, dado referente à saúde, vida sexual,
dado genético, dado biométrico.

NG-CLI-11: Aferê MVP-1 NÃO trata PII sensível. Campos livres
(`observacao`) que contenham termos da denylist → 400.

**Design endurecido** (BLOQ-A3 advogado + BLOQ-TL-2 tech-lead):

- Word-boundary `\\b` — não casa substring interna (evita falsos
  positivos `pt` em "patenteado", `trans` em "transformador" — fatal
  num ERP de balanças).
- Termos ≥ 5 chars — sem siglas curtas com colisão.
- Lista enxuta — revisão de advogado humano pré-1º tenant externo
  pago (consulta pontual 2-4h documentada em
  `docs/faseamento/M1-clientes/T-CLI-114-120/review-advogado.md`).
- Detecção é **best-effort** (não substitui análise humana —
  controlador continua responsável LGPD art. 11). Documentado.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Final

# Termos completos (≥ 5 chars), boundary-safe. Origem: art. 5º II LGPD.
_TERMOS_PII_SENSIVEL: Final[tuple[str, ...]] = (
    # Saúde (art. 5 II + art. 11)
    "diabet",
    "hipertens",
    "cancer",
    "tumor",
    "depres",
    "psiqui",
    "soropositivo",
    "alcool",
    "drogad",
    "vicio",
    # Saúde reprodutiva
    "menstr",
    "gravid",
    "gestant",
    "aborto",
    # Biometria
    "biometr",
    "facial",
    "retina",
    "datilo",
    # Genética
    "geneti",
    "hereditari",
    "cromoss",
    # Política (palavras inteiras — não siglas)
    "esquerda",
    "direita",
    "comunist",
    "fascist",
    # Religião
    "evangelic",
    "catolic",
    "islam",
    "judaic",
    "budist",
    "umbanda",
    "candomble",
    "espirita",
    # Orientação sexual
    "lgbtq",
    "homosex",
    "bissex",
    "transex",
    # Origem racial/étnica (BLOQ-A1 advogado)
    "racial",
    "indigena",
    "negroide",
    "caucasiano",
    # Sindicato (art. 5º II)
    "sindical",
    "sindicat",
)

# Word-boundary case-insensitive — `\w*` permite sufixo
# (`diabet` casa `diabetes`, `diabético`, `diabéticos`).
_RE_PII_SENSIVEL: Final[re.Pattern[str]] = re.compile(
    r"\b(" + "|".join(_TERMOS_PII_SENSIVEL) + r")\w*\b",
    re.IGNORECASE,
)

MENSAGEM_REJEICAO: Final[str] = (
    "dado sensível não é tratado no Aferê MVP-1 (LGPD art. 11 + NG-CLI-11)"
)


def _normalizar(texto: str) -> str:
    """Remove diacríticos (`á` → `a`) pra denylist case-insensitive
    funcionar em PT-BR (`grávida` casa `gravid`).

    Normaliza NFKD + filtra combining marks (categoria Mn).
    """
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def conter_pii_sensivel(texto: str) -> bool:
    """Detecção word-boundary case-insensitive + acento-insensitive.

    BLOQ-A1 + BLOQ-TL-2 (advogado + tech-lead).

    Best-effort — NÃO substitui análise humana (controlador continua
    responsável LGPD art. 11). Lista taxativa fechada do art. 5º II.

    Retorna True se algum termo da denylist aparecer no texto com
    word-boundary (não substring interna — evita falsos positivos
    fatais em ERP metrológico tipo "transformador"/"genealogia").
    Diacríticos removidos antes do match (`grávida` casa `gravid`).
    """
    if not texto:
        return False
    return _RE_PII_SENSIVEL.search(_normalizar(texto)) is not None
