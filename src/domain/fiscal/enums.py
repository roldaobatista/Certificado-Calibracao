"""Enums fechados do domínio fiscal (frente NFS-e, Fatia 1a — T-FIS-010/013/014).

str-mixin → serialização JSON nativa (mesmo padrão de `metrologia/*/enums.py`).
Domínio NÃO importa Django (ADR-0007).
"""

from __future__ import annotations

from enum import Enum


class InvoiceStatus(str, Enum):
    """Estado do documento fiscal — AGNÓSTICO de país/fornecedor (D-FIS-1).

    Máquina de estados (D-FIS-3): `PENDING → AUTHORIZED | REJECTED`;
    `AUTHORIZED → CANCELED`. `REJECTED` e `CANCELED` são TERMINAIS. `network_timeout`
    do provider NÃO é estado da nota (erro de transporte — nenhuma persistência).
    """

    PENDING = "PENDING"
    AUTHORIZED = "AUTHORIZED"
    REJECTED = "REJECTED"
    CANCELED = "CANCELED"


class TipoServico(str, Enum):
    """Natureza do serviço faturado. Decide se a trava metrológica se aplica.

    `CALIBRACAO` exige documento metrológico compatível com o perfil (INV-FIS-001).
    Perfil D usa o MESMO valor `CALIBRACAO` (termo simples — decisão Roldão
    2026-06-08, D-FIS-7): "calibração" sozinha é serviço comercial genérico; só
    "calibração RBC/acreditada" exige acreditação (a distinção vem do vínculo
    documental, não do nome do serviço). `MANUTENCAO`/`OUTRO` não exigem vínculo.
    """

    CALIBRACAO = "calibracao"
    MANUTENCAO = "manutencao"
    OUTRO = "outro"


class TipoAcreditacaoVinculo(str, Enum):
    """Classificação RBC do certificado vinculado, LIDA do snapshot do M8
    (`Certificado.tipo_acreditacao`) — INV-FIS-002. O fiscal NUNCA reavalia
    vigência; só lê o que o M8 congelou na emissão do certificado.
    """

    RBC = "RBC"
    NAO_RBC = "NAO_RBC"


class PerfilRegulatorio(str, Enum):
    """Espelho do `Tenant.perfil_regulatorio` (ADR-0067) para uso PURO no domínio
    (sem importar a camada tenant). Lido server-side via ContextVar na borda;
    chega aqui como valor já resolvido (INV-FIS-001 — nunca do payload).
    """

    A = "A"  # acreditado RBC
    B = "B"  # rastreável
    C = "C"  # em preparação D→A
    D = "D"  # comercial puro
