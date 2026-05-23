"""Value Objects + enums do dominio Ordens de Servico (T-OS-021).

Imutaveis (frozen=True). Sem Django. Cobrem:

- `EstadoOS`: 7 estados da OS (INV-OS-ATIV-001).
- `EstadoAtividade`: 6 estados da AtividadeDaOS.
- `TipoAtividade`: enum fechado de 6 tipos (INV-OS-ATIV-003).
- `PrecedenteDispensa`: enum 3 valores (P-OS-A4).
- `TipoFotoEvidencia`: 5 tipos de foto.
- `TipoEventoDeOS`: 19 tipos de evento (audit timeline).
- `EstadoChecklistItem`: 3 estados.
- `PrioridadeSLA`: 4 niveis.
- `NumeroOSFormatado`: VO pra exibicao 'OS-YYYY-NNNNNN'.
- `MotivoCancelamento`: ≥30 chars + anti-PII (INV-OS-TXT-001).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

# =============================================================
# Enums fechados
# =============================================================


class EstadoOS(str, Enum):
    """Estado da OS — computado a partir das atividades (INV-OS-ATIV-001)."""

    RASCUNHO = "rascunho"
    AGENDADA = "agendada"
    EM_EXECUCAO = "em_execucao"
    CONCLUIDA = "concluida"
    CANCELADA = "cancelada"
    FATURADA = "faturada"
    PAGA = "paga"

    @property
    def terminal(self) -> bool:
        """Estado nao-mutavel via maquina principal."""
        return self in {EstadoOS.CONCLUIDA, EstadoOS.CANCELADA, EstadoOS.FATURADA, EstadoOS.PAGA}


class EstadoAtividade(str, Enum):
    """Estado da AtividadeDaOS — INV-OS-ATIV-001."""

    PENDENTE = "pendente"
    AGENDADA = "agendada"
    EM_EXECUCAO = "em_execucao"
    CONCLUIDA = "concluida"
    NAO_CONFORME = "nao_conforme"
    CANCELADA = "cancelada"

    @property
    def terminal(self) -> bool:
        """OS so transita pra CONCLUIDA quando TODAS atividades terminais."""
        return self in {
            EstadoAtividade.CONCLUIDA,
            EstadoAtividade.NAO_CONFORME,
            EstadoAtividade.CANCELADA,
        }


class TipoAtividade(str, Enum):
    """Tipo enum fechado (INV-OS-ATIV-003 + ADR-0023). Nao adicionar sem ADR."""

    CALIBRACAO = "calibracao"
    MANUTENCAO_CORRETIVA = "manutencao_corretiva"
    MANUTENCAO_PREVENTIVA = "manutencao_preventiva"
    INSTALACAO = "instalacao"
    VERIFICACAO_INMETRO = "verificacao_inmetro"
    VISTORIA = "vistoria"


class PrecedenteDispensa(str, Enum):
    """Precedente obrigatorio pra DispensaAceiteAtividade (P-OS-A4)."""

    NO_SHOW = "no_show"
    RECUSA_EXPLICITA = "recusa_explicita"
    IMPOSSIBILIDADE_TECNICA = "impossibilidade_tecnica"


class TipoFotoEvidencia(str, Enum):
    """Tipos de EvidenciaFotoAtividade (P-OS-T5)."""

    CHECKLIST_ITEM = "checklist_item"
    CONCLUSAO = "conclusao"
    NC = "nc"
    NO_SHOW = "no_show"
    RECUSA_ACEITE = "recusa_aceite"


class TipoEventoDeOS(str, Enum):
    """Tipos de evento na timeline da OS (INV-OS-AUD-001)."""

    ATIVIDADE_ADICIONADA = "atividade_adicionada"
    ATIVIDADE_INICIADA = "atividade_iniciada"
    ATIVIDADE_CONCLUIDA = "atividade_concluida"
    ATIVIDADE_NAO_CONFORME = "atividade_nao_conforme"
    ATIVIDADE_NC_RESOLVIDA = "atividade_nc_resolvida"
    ATIVIDADE_CANCELADA = "atividade_cancelada"
    ATIVIDADE_REAGENDADA = "atividade_reagendada"
    ATIVIDADE_TECNICO_TRANSFERIDO = "atividade_tecnico_transferido"
    NO_SHOW_CLIENTE = "no_show_cliente"
    DISPENSA_ACEITE_EMITIDA = "dispensa_aceite_emitida"
    FOTO_EVIDENCIA_TARDIA = "foto_evidencia_tardia"
    WATCHDOG_ESTENDIDO = "watchdog_estendido"
    OS_ABERTA = "os_aberta"
    OS_ATRIBUIDA = "os_atribuida"
    OS_CONCLUIDA = "os_concluida"
    OS_CANCELADA = "os_cancelada"
    OS_REABERTA = "os_reaberta"
    OS_ESCOPO_ALTERADO = "os_escopo_alterado"
    SLA_BREACH = "sla_breach"


class EstadoChecklistItem(str, Enum):
    """Estado de cada item do ChecklistDaAtividade."""

    PENDENTE = "pendente"
    PREENCHIDO = "preenchido"
    NAO_APLICAVEL = "nao_aplicavel"

    @property
    def terminal(self) -> bool:
        return self in {EstadoChecklistItem.PREENCHIDO, EstadoChecklistItem.NAO_APLICAVEL}


class PrioridadeSLA(str, Enum):
    """Niveis de SLA — alta/emergencia disparam consumer sla-breach (US-OS-007 saga 4)."""

    BAIXA = "baixa"
    NORMAL = "normal"
    ALTA = "alta"
    EMERGENCIA = "emergencia"

    @property
    def dispara_sla_breach(self) -> bool:
        """Se True, cancelarOS publica evento sla_breach."""
        return self in {PrioridadeSLA.ALTA, PrioridadeSLA.EMERGENCIA}


# =============================================================
# Value Objects estruturados
# =============================================================


@dataclass(frozen=True, slots=True)
class NumeroOSFormatado:
    """VO pra exibicao do numero da OS (ADR-0056).

    `numero_os` vem da sequence global PG; formatado `OS-YYYY-NNNNNN`.
    Coluna no DB usa `GENERATED ALWAYS AS STORED` pra evitar drift.
    """

    ano: int
    numero: int

    def __post_init__(self) -> None:
        if not (2026 <= self.ano <= 2099):
            raise ValueError(f"NumeroOSFormatado: ano {self.ano} fora do intervalo [2026, 2099].")
        if self.numero <= 0:
            raise ValueError(f"NumeroOSFormatado: numero deve ser positivo, recebido {self.numero}.")

    def __str__(self) -> str:
        return f"OS-{self.ano}-{self.numero:06d}"


# Lista mínima de regex anti-PII de INV-OS-TXT-001 (estendida P-OS-A3).
_CPF_RE = re.compile(r"\b\d{3}[.\-]?\d{3}[.\-]?\d{3}[\-.]?\d{2}\b")
_CNPJ_RE = re.compile(r"\b[\dA-Z]{2}[.\-]?[\dA-Z]{3}[.\-]?[\dA-Z]{3}[/]?\d{4}[\-]?\d{2}\b")
_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")
_TELEFONE_RE = re.compile(r"\b(?:\+?55\s?)?\(?\d{2}\)?\s?9?\s?\d{4}\s?[\-.]?\d{4}\b")
_NOMES_RE = re.compile(r"\b[A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b")
_ENDERECO_RE = re.compile(
    r"\d+\s*(?:ap|apto|apt|bloco|sala|conjunto|cj)\.?\s*\d+",
    re.IGNORECASE,
)
_SEQ_NUMERICA_RE = re.compile(r"\b\d{7,}\b")

# Palavras-chave que disparam revisao do gerente (P-OS-A3 — REQUER OAB).
_PALAVRAS_SAUDE = re.compile(
    r"\b(?:paciente|leito|prontu[áa]rio|menor|crian[çc]a|gestante|hiv|positivo)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class MotivoCancelamento:
    """Motivo livre obrigatorio em cancelamentos / NC / dispensas.

    Cobre INV-OS-TXT-001 com regex estendida P-OS-A3:
    - Minimo 30 chars (cumprimento obrigatorio US-OS-007/008/011..014).
    - Maximo 500 chars (limite operacional).
    - Anti-PII: bloqueia CPF/CNPJ/email/telefone/2-nomes-juntos/endereco/
      sequencia ≥7 digitos.
    - Palavras-chave saude disparam `revisao_gerente_pendente=True`
      (nao bloqueia INSERT — quarentena 24h em camada de aplicacao).

    Texto canonicalizado (NFC + lowercase + strip) usado pro hash.
    """

    texto: str

    def __post_init__(self) -> None:
        if not isinstance(self.texto, str):
            raise TypeError("MotivoCancelamento: texto deve ser str.")
        if len(self.texto) < 30:
            raise ValueError(
                f"MotivoCancelamento: minimo 30 chars (recebido {len(self.texto)})."
            )
        if len(self.texto) > 500:
            raise ValueError(
                f"MotivoCancelamento: maximo 500 chars (recebido {len(self.texto)})."
            )

        # Anti-PII canonicalizado.
        canonico = self._canonicalizar(self.texto)
        for nome, regex in [
            ("CPF", _CPF_RE),
            ("CNPJ", _CNPJ_RE),
            ("email", _EMAIL_RE),
            ("telefone", _TELEFONE_RE),
            ("endereco", _ENDERECO_RE),
            ("sequencia_numerica", _SEQ_NUMERICA_RE),
        ]:
            if regex.search(canonico):
                raise ValueError(
                    f"MotivoCancelamento (INV-OS-TXT-001): texto contem {nome}."
                )

        # Nomes capitalizados consecutivos — checa antes da normalizacao lowercase
        if _NOMES_RE.search(self.texto):
            raise ValueError(
                "MotivoCancelamento (INV-OS-TXT-001): texto contem ≥2 nomes proprios consecutivos."
            )

    @property
    def revisao_gerente_pendente(self) -> bool:
        """True se gatilho saude detectado (P-OS-A3) — handler poe em quarentena 24h."""
        return bool(_PALAVRAS_SAUDE.search(self.texto))

    @staticmethod
    def _canonicalizar(texto: str) -> str:
        """NFC + lowercase + strip — INV-DOC-CANON-001 paralelo."""
        import unicodedata

        return unicodedata.normalize("NFC", texto).lower().strip()
