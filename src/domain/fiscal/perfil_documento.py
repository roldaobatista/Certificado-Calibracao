"""Trava metrológica PURA por perfil (Fatia 1a — T-FIS-014).

D-FIS-5/6 (convergência tech-lead TL-06 + consultor-rbc RBC-01): esta função roda
DENTRO do use case `emitir_nfse` (regra de negócio com estado persistido —
coerência ADR-0073), NÃO no permission layer DRF. Recebe o `Certificado` JÁ
CARREGADO (snapshot do M8) e o perfil JÁ RESOLVIDO server-side (a borda DRF lê via
ContextVar — INV-FIS-001, nunca do payload).

INV-FIS-002 (fonte de verdade): o vínculo RBC vem EXCLUSIVAMENTE do
`Certificado.tipo_acreditacao` snapshotado pelo M8. Esta função NUNCA reconsulta
`Tenant.acreditacao_vigencia_fim` — a vigência foi avaliada uma única vez, na data
de emissão do certificado (M8, INV-CER-CGCRE-VIG-001). A NFS-e herda o snapshot
(fatura serviço já prestado).

Matriz (PRD §3.1, AC-FIS-001):
  - A: exige `certificado_id` vinculado — RBC **ou** NAO_RBC (D-FIS-6: lab
       acreditado pode faturar calibração não-RBC; a obrigatoriedade RBC é sobre
       *capacidade*, não sobre *todo certificado*).
  - B/C: exige certificado SIMPLES (não-RBC). Certificado RBC referenciado por
         perfil B/C → incompatível (AC-FIS-001-8, defesa anti-fraude L6).
  - D: aceita `declaracao_id` (declaração básica sem ritual 17025).

`tipo_servico` ≠ CALIBRACAO (manutenção/outro) → sem trava (vínculo opcional).
"""

from __future__ import annotations

from .enums import PerfilRegulatorio, TipoAcreditacaoVinculo, TipoServico
from .erros import DocIncompativelComPerfilError, DocMetrologicoObrigatorioError


def documento_metrologico_obrigatorio_por_perfil(
    *,
    perfil: PerfilRegulatorio,
    tipo_servico: TipoServico,
    tipo_acreditacao_certificado: TipoAcreditacaoVinculo | None,
    tem_declaracao: bool,
) -> None:
    """Valida a compatibilidade perfil × documento metrológico. Levanta erro de
    domínio (→422/403) se incompatível; retorna `None` se OK.

    `tipo_acreditacao_certificado` = snapshot do `Certificado` referenciado, ou
    `None` se nenhum certificado foi vinculado. `tem_declaracao` = há
    `declaracao_calibracao_basica_id` vinculado (perfil D).
    """
    # Serviço sem exigência metrológica: vínculo é opcional.
    if tipo_servico is not TipoServico.CALIBRACAO:
        return

    if perfil is PerfilRegulatorio.D:
        # Perfil D: declaração básica OU certificado simples bastam.
        if tem_declaracao or tipo_acreditacao_certificado is TipoAcreditacaoVinculo.NAO_RBC:
            return
        if tipo_acreditacao_certificado is TipoAcreditacaoVinculo.RBC:
            # Perfil D não emite RBC — incompatível.
            raise DocIncompativelComPerfilError(
                "perfil D não pode referenciar certificado RBC"
            )
        raise DocMetrologicoObrigatorioError(
            "perfil D exige declaração de calibração básica ou certificado simples"
        )

    # Perfis A/B/C exigem certificado vinculado.
    if tipo_acreditacao_certificado is None:
        raise DocMetrologicoObrigatorioError(
            f"perfil {perfil.value} exige certificado vinculado para calibração"
        )

    if perfil is PerfilRegulatorio.A:
        # A aceita RBC ou NAO_RBC (D-FIS-6).
        return

    # Perfis B/C: certificado deve ser SIMPLES (não-RBC). RBC → incompatível.
    if tipo_acreditacao_certificado is TipoAcreditacaoVinculo.RBC:
        raise DocIncompativelComPerfilError(
            f"perfil {perfil.value} não pode referenciar certificado RBC "
            "(esperado certificado simples)"
        )
    return
