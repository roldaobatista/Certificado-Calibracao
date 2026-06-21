"""Geração do PDF da prestação de contas do técnico (Fatia 3c / T-CT-055).

Renderiza um template HTML+CSS leve via WeasyPrint (TL-CT-03 / D-CT-8). O dado
estruturado (``PrestacaoContas`` WORM) é a FONTE da verdade; o PDF é projeção
**on-demand** — regenerável a qualquer momento, NÃO persistido como fonte.

Anti-PII / LGPD (AC-CT-002-7 / INV-LGPD-CONSENT-001):
- GPS (coordenada) NUNCA entra no PDF — retenção própria curta (fechamento + 90d),
  desacoplada dos 5a fiscais. O PDF carrega só dados fiscais por despesa:
  data, categoria, valor, OS vinculada.
- Sem nome/CPF do técnico no corpo — identifica pelo pseudônimo do caixa
  (``tecnico_referencia`` hash, ADR-0032), nunca o dado cru.

Segurança (CVE-2025-68616 — SSRF via ``url_fetcher`` do WeasyPrint < 68.0):
- ``url_fetcher`` recusa toda URL não-``data:``. O template é HTML+CSS 100% inline,
  sem imagem/fonte externa — mesmo guard do molde ``equipamentos/services_etiqueta.py``.

Refs: D-CT-8; TL-CT-03; AC-CT-006-2; AC-CT-002-7; INV-LGPD-CONSENT-001.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.template.loader import render_to_string
from weasyprint import HTML

if TYPE_CHECKING:
    from src.domain.caixa_tecnico.entities import (
        Adiantamento,
        Despesa,
        PrestacaoContas,
    )

# Rótulos legíveis (apresentação) — não substituem o valor canônico do enum.
_DIRECAO_ROTULO = {
    "tecnico_deve": "Técnico deve ao tenant",
    "tenant_deve": "Tenant deve ao técnico (a reembolsar)",
    "quitado": "Quitado",
}


def _url_fetcher_recusa_tudo(url: str) -> dict[str, object]:
    """Bloqueia QUALQUER URL fetcher não-``data:`` (CVE-2025-68616).

    O template da prestação é HTML+CSS inline, sem imagem/fonte externa. Libera
    só ``data:`` por simetria com o molde; http/https/file/ftp → ``RuntimeError``
    — garante que HTML injetado não inicie fetch externo nem redirect.
    """
    if url.startswith("data:"):
        from weasyprint import default_url_fetcher

        return dict(default_url_fetcher(url))
    raise RuntimeError(
        f"prestacao_pdf: url_fetcher recusou URL não-data (CVE-2025-68616): {url[:80]}"
    )


def _reais(centavos: int) -> str:
    """Formata centavos (int) como BRL legível: ``1234567`` → ``'12.345,67'``.

    Preserva sinal (saldo ``tecnico_deve`` é negativo na convenção do domínio).
    """
    sinal = "-" if centavos < 0 else ""
    inteiro, resto = divmod(abs(centavos), 100)
    milhar = f"{inteiro:,}".replace(",", ".")
    return f"R$ {sinal}{milhar},{resto:02d}"


def montar_html_prestacao(
    prestacao: PrestacaoContas,
    despesas: list[Despesa],
    adiantamentos: list[Adiantamento],
    *,
    tenant_nome: str = "",
) -> str:
    """Renderiza o HTML intermediário da prestação (testável sem parsear o PDF).

    GPS AUSENTE (AC-CT-002-7): a ``coordenada`` da despesa NUNCA é passada ao
    template — só dados fiscais (data, categoria, valor, OS vinculada). O teste
    da Fatia 3c valida exatamente isso sobre esta string (o ``write_pdf`` comprime
    o conteúdo, então a verificação de ausência de GPS acontece aqui, no HTML).
    """
    linhas_despesas = [
        {
            "data": d.data.isoformat(),
            "categoria": d.categoria.value,
            "valor": _reais(d.valor.centavos),
            "os_id": str(d.os_id) if d.os_id else "—",
            "descricao": d.descricao or "",
        }
        for d in despesas
    ]
    linhas_adiantamentos = [
        {
            "data": a.entregue_em.date().isoformat() if a.entregue_em else "—",
            "meio": a.meio.value,
            "valor": _reais(a.valor.centavos),
        }
        for a in adiantamentos
    ]
    return render_to_string(
        "caixa_tecnico/prestacao_pdf.html",
        {
            "tenant_nome": tenant_nome,
            "prestacao_id": str(prestacao.prestacao_id),
            "caixa_id": str(prestacao.caixa_id),
            "tecnico_referencia": prestacao.tecnico_referencia.hash_original[:12],
            "periodo_de": prestacao.periodo.de.isoformat(),
            "periodo_ate": prestacao.periodo.ate.isoformat(),
            "total_adiantado": _reais(prestacao.total_adiantado.centavos),
            "total_despesas": _reais(prestacao.total_despesas_validadas.centavos),
            "saldo_final": _reais(prestacao.saldo_final.centavos),
            "direcao": _DIRECAO_ROTULO.get(prestacao.direcao.value, prestacao.direcao.value),
            "fechada_em": prestacao.fechada_em.isoformat(timespec="minutes"),
            "observacoes": prestacao.observacoes or "",
            "despesas": linhas_despesas,
            "adiantamentos": linhas_adiantamentos,
        },
    )


def gerar_pdf_prestacao(
    prestacao: PrestacaoContas,
    despesas: list[Despesa],
    adiantamentos: list[Adiantamento],
    *,
    tenant_nome: str = "",
) -> bytes:
    """Renderiza o PDF da prestação de contas (projeção on-demand, regenerável).

    GPS AUSENTE (AC-CT-002-7): delega a ``montar_html_prestacao`` (que nunca expõe
    coordenada) e renderiza via WeasyPrint com ``url_fetcher`` que recusa não-``data:``.

    Args:
        prestacao: registro WORM já fechado (fonte da verdade).
        despesas: despesas VALIDADAS do período (sem GPS no PDF).
        adiantamentos: adiantamentos ENTREGUES do período.
        tenant_nome: nome-fantasia do emitente (equivalente ao logo — sem PII de cliente).

    Returns:
        ``bytes`` do PDF (não-vazio).
    """
    html = montar_html_prestacao(prestacao, despesas, adiantamentos, tenant_nome=tenant_nome)
    pdf_bytes: bytes = HTML(string=html, url_fetcher=_url_fetcher_recusa_tudo).write_pdf()
    return pdf_bytes
