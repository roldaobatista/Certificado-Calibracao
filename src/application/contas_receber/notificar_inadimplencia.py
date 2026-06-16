"""Use case `notificar_inadimplencia` — montagem do aviso D+30/D+45 (T-CR-044 / D-CR-9).

Caminho C (parecer advogado, 2026-06-16): aviso ao cliente final com REMETENTE = TENANT
(o Aferê opera o envio tecnicamente, não aparece como cobrador). Texto **PROVISÓRIO** —
o definitivo entra no GATE-LGPD-RAT-CONSOLIDACAO (congelado por decisão Roldão 2026-06-12).

Minimização (D-CR-19): o aviso só carrega título/valor/vencimento/dias/canal + o que SERÁ
e o que NÃO será bloqueado (D-CR-21). Sem CPF, sem dados de terceiro. Função PURA — o
envio (`send_mail`) e a leitura de `Cliente.email` (PII) ficam no job (infra).

Só perfil A em Wave A (D-CR-9 / GATE-CR-NOTIF-D30-PERFIL-A); demais perfis recebem o
payload do evento `contas_receber.titulo_vencido` para o tenant comunicar (D-CR-22).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

MARCO_D30 = "D30"
MARCO_D45 = "D45"
_MARCOS: dict[int, str] = {30: MARCO_D30, 45: MARCO_D45}


@dataclass(frozen=True, slots=True)
class TituloVencidoInfo:
    """Dados mínimos de um título vencido para o aviso (sem PII)."""

    titulo_id: UUID
    valor_centavos: int
    data_vencimento: date
    dias_vencido: int


@dataclass(frozen=True, slots=True)
class AvisoInadimplencia:
    """Aviso montado: assunto + corpo (provisório) + dados para o evento (sem PII)."""

    marco: str
    assunto: str
    corpo: str
    data_bloqueio_prevista: date
    titulos_payload: list[dict[str, object]]


def marco_de_dias_vencido(dias_vencido: int) -> str | None:
    """D30/D45 se o dia bate exatamente um marco notificável; senão None.

    Idempotência por dia: o job roda 1×/dia, então cada marco dispara em 1 dia.
    Robustez contra job perdido (prova de envio + re-disparo) = Fatia 3b-3.
    """
    return _MARCOS.get(dias_vencido)


def _centavos_para_reais_str(centavos: int) -> str:
    reais = Decimal(centavos) / Decimal(100)
    return f"R$ {reais:.2f}".replace(".", ",")


def montar_aviso(
    *,
    tenant_nome: str,
    titulos: list[TituloVencidoInfo],
    marco: str,
    grace_perfil: int,
    canal_regularizacao_url: str,
) -> AvisoInadimplencia:
    """Monta assunto + corpo PROVISÓRIO do aviso. `titulos` não pode ser vazio.

    `data_bloqueio_prevista` = vencimento mais antigo + grace do perfil.
    O corpo é minuta provisória explícita — o texto definitivo aguarda o gate jurídico.
    """
    if not titulos:
        raise ValueError("montar_aviso: lista de títulos vazia.")
    venc_mais_antigo = min(t.data_vencimento for t in titulos)
    data_bloqueio = venc_mais_antigo + timedelta(days=grace_perfil)
    linhas = [
        f"- Título {t.titulo_id}: {_centavos_para_reais_str(t.valor_centavos)} "
        f"(vencido em {t.data_vencimento.isoformat()}, {t.dias_vencido} dias em atraso)"
        for t in titulos
    ]
    total = _centavos_para_reais_str(sum(t.valor_centavos for t in titulos))
    assunto = (
        f"[{tenant_nome}] Aviso de pendência financeira — "
        f"regularize até {data_bloqueio.isoformat()}"
    )
    corpo = (
        "[MINUTA PROVISÓRIA — texto definitivo aguarda revisão jurídica (GATE-LGPD-RAT)]\n\n"
        "Prezado(a) cliente,\n\n"
        f"Consta(m) em aberto, junto a {tenant_nome}, o(s) seguinte(s) título(s):\n"
        + "\n".join(linhas)
        + f"\n\nTotal em aberto: {total}.\n\n"
        f"Para evitar a suspensão de NOVOS atendimentos a partir de "
        f"{data_bloqueio.isoformat()}, regularize em: {canal_regularizacao_url}\n\n"
        "Importante: serviços já em andamento, certificados já emitidos e o acesso ao "
        "seu histórico NÃO são interrompidos.\n\n"
        f"Esta mensagem foi enviada pela plataforma Aferê a serviço de {tenant_nome}. "
        f"Dúvidas sobre esta cobrança devem ser tratadas diretamente com {tenant_nome}.\n"
    )
    titulos_payload: list[dict[str, object]] = [
        {
            "titulo_id": str(t.titulo_id),
            "valor_original_centavos": t.valor_centavos,
            "data_vencimento": t.data_vencimento.isoformat(),
            "dias_vencido": t.dias_vencido,
        }
        for t in titulos
    ]
    return AvisoInadimplencia(
        marco=marco,
        assunto=assunto,
        corpo=corpo,
        data_bloqueio_prevista=data_bloqueio,
        titulos_payload=titulos_payload,
    )
