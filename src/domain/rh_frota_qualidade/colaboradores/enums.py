"""Enums do módulo `colaboradores` (T-COL-010).

str-mixin → serialização JSON nativa (molde `precificacao/enums.py`).
Refs: D-COL-4/5/6; spec §4; R-COL-2 (ASO removido do MVP).
"""

from __future__ import annotations

from enum import Enum


class Vinculo(str, Enum):
    """Vínculo empregatício / contratual do colaborador com o tenant.

    Determina base legal LGPD aplicável (ADV-COL-01 / D-COL-6):
      CLT          → art. 7º II (obrigação legal).
      PJ           → art. 7º V (execução de contrato).
      ESTAGIARIO   → Lei 11.788/2008 + art. 7º V.
      SOCIO        → art. 7º V + base societária.
      TERCEIRIZADO → art. 7º V (execução de contrato com terceiro).

    Impacta coerência de documentos: CTPS é incompatível com PJ/TERCEIRIZADO
    (INV-COL-DOC-VINCULO — minimização art. 6º III LGPD, ADV-COL-01).
    """

    CLT = "clt"
    PJ = "pj"
    ESTAGIARIO = "estagiario"
    SOCIO = "socio"
    TERCEIRIZADO = "terceirizado"


class PapelColaborador(str, Enum):
    """Papel de negócio do colaborador no tenant (D-COL-4 / spec §4).

    Papel de NEGÓCIO ≠ perfil de authz (ADR-0012): RBAC materializa
    `UsuarioPerfilTenant` ao consumir `PapelAtribuido` via outbox (D-COL-2).

    TECNICO        → executa calibração / assistência técnica no campo.
    SIGNATARIO     → assina certificados (exige usuario_id + RTCompetencia —
                     INV-COL-SIGNATARIO-IDENTIDADE/-ESCOPO, D-COL-11).
    ATENDENTE      → atende clientes / abre chamados.
    GERENTE        → gerencia equipe e aprova descontos (alçada GERENTE).
    DONO           → dono do negócio; único por tenant ativo (INV-COL-DONO-UNICO).
    QUALIDADE      → responsável por qualidade / ISO; vê auditoria (D-COL-14).
    MOTORISTA_UMC  → motorista de UMC (unidade móvel de calibração). Exige CNH
                     com validade; sem CNH → salvar com pendência (R-COL-1).
    """

    TECNICO = "tecnico"
    SIGNATARIO = "signatario"
    ATENDENTE = "atendente"
    GERENTE = "gerente"
    DONO = "dono"
    QUALIDADE = "qualidade"
    MOTORISTA_UMC = "motorista_umc"


class NivelHabilidade(str, Enum):
    """Nível de proficiência em uma habilidade (D-COL-5 / spec §4).

    APRENDIZ  → em formação; não apto para executar de forma autônoma.
    CAPACITADO → executa com autonomia; apto para atribuição de OS.
    MESTRE    → referência; pode supervisionar e avaliar outros.
    """

    APRENDIZ = "aprendiz"
    CAPACITADO = "capacitado"
    MESTRE = "mestre"


class TipoDocumento(str, Enum):
    """Tipo de documento anexável ao colaborador (D-COL-6 / R-COL-2).

    ASO (Atestado de Saúde Ocupacional) **fora do MVP** — dado de saúde art. 11
    LGPD; dono = módulo SST (R-COL-2 / ADV-COL-01). Não incluir aqui.

    CTPS            → Carteira de Trabalho e Previdência Social.
                      Incompatível com PJ/TERCEIRIZADO (INV-COL-DOC-VINCULO).
    CNH             → Carteira Nacional de Habilitação (obrigatória p/ MOTORISTA_UMC).
    CERTIFICADO_CURSO → certificado de curso/treinamento externo.
    OUTRO           → documento de outro tipo (identificação, etc.).
    """

    CTPS = "ctps"
    CNH = "cnh"
    CERTIFICADO_CURSO = "certificado_curso"
    OUTRO = "outro"
