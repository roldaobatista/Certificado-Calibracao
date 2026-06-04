"""Fixtures PG-real compartilhadas do M8 `certificados` (Sub-fatia 2b/3).

NÃO é arquivo de teste (sem `test_`); helpers reutilizados pelos testes de
adapters de leitura (query_service) e pelos testes REST/emissão. Tudo é criado
DENTRO de `run_in_tenant_context` (a policy de INSERT da RLS usa
`app.active_tenant_id` — factory-boy fora do contexto seria recusado). Calibração
APROVADA é 1 INSERT direto (o trigger anti-mutação terminal só dispara em
UPDATE/DELETE — criar já-aprovada é permitido), o caminho mais barato sem
percorrer a máquina de 12 estados.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

from django.db import connection
from django.utils import timezone
from src.domain.metrologia.calibracao.enums import (
    EstadoCalibracao,
    LeiEscalonamento,
    MetodoTipoAPonto,
)
from src.infrastructure.calibracao.models import (
    Calibracao,
    Leitura,
    OrcamentoIncerteza,
    OrcamentoPorPonto,
)
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.equipamentos.models import Equipamento
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory


def cenario_tenant_equipamento(slug_prefix: str = "m8", *, perfil_a: bool = False):
    """Cria tenant (+ trait perfil A opcional) + Cliente PJ + Equipamento. Retorna
    `(tenant, equipamento)`."""
    sfx = uuid4().hex[:8]
    kwargs = {"slug": f"{slug_prefix}-{sfx}"}
    if perfil_a:
        kwargs["perfil_a"] = True
    tenant = TenantFactory(**kwargs)
    with run_in_tenant_context(tenant.id):
        cliente = Cliente.objects.create(
            tenant=tenant,
            tipo_pessoa=TipoPessoa.PJ,
            documento="11222333000181",
            nome="Cliente Cert M8",
            aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
        )
        equipamento = Equipamento.objects.create(
            tenant=tenant,
            tag=f"CERT-{sfx}",
            numero_serie=f"NS-{sfx}",
            fabricante="Toledo",
            modelo="Prix 4",
            cliente_atual=cliente,
            perfil_tenant_snapshot={"perfil": "A" if perfil_a else "D"},
        )
    return tenant, equipamento


def criar_calibracao_aprovada(
    tenant,
    equipamento,
    *,
    grandeza: str = "massa",
    faixa_min: Decimal = Decimal("0"),
    faixa_max: Decimal = Decimal("1000"),
    unidade: str = "g",
) -> Calibracao:
    """1 INSERT de `Calibracao` em `status='aprovada'` com grandeza/faixa declaradas
    (ADR-0076). `numero_interno` vem da sequence real (unicidade)."""
    with run_in_tenant_context(tenant.id):
        with connection.cursor() as cur:
            cur.execute("SELECT nextval('calibracao_numero_seq_global')")
            numero = cur.fetchone()[0]
        return Calibracao.objects.create(
            tenant=tenant,
            instrumento=equipamento,
            numero_interno=numero,
            cliente_referencia_hash="v01$cli",
            cliente_key_id="cli-key-v1",
            status=EstadoCalibracao.APROVADA.value,
            grandeza_calibrada=grandeza,
            faixa_calibrada_min=faixa_min,
            faixa_calibrada_max=faixa_max,
            unidade_calibrada=unidade,
            snapshot_equipamento_json={"tag": equipamento.tag},
        )


def criar_calibracao_em_estado(
    tenant,
    equipamento,
    *,
    status: EstadoCalibracao,
    subcontratado_id=None,
    executor_id=None,
    grandeza: str = "massa",
    unidade: str = "g",
) -> Calibracao:
    """1 INSERT de `Calibracao` num `status` arbitrario (trigger anti-mutacao
    so dispara em UPDATE/DELETE — criar ja num estado intermediario eh permitido).

    Usado por testes de subcontratacao (T-CAL-129): CONFIGURADA para o caminho
    `subcontratar`; AGUARDANDO_SUBCONTRATADO + `subcontratado_id` para o
    caminho `registrar_recebimento`. `executor_id` opcional alimenta o teste de
    separacao de funcoes (recebedor != executor — INV-CAL-FRAUDE-RECEB-001)."""
    with run_in_tenant_context(tenant.id):
        with connection.cursor() as cur:
            cur.execute("SELECT nextval('calibracao_numero_seq_global')")
            numero = cur.fetchone()[0]
        campos = {
            "tenant": tenant,
            "instrumento": equipamento,
            "numero_interno": numero,
            "cliente_referencia_hash": "v01$cli",
            "cliente_key_id": "cli-key-v1",
            "status": status.value,
            "grandeza_calibrada": grandeza,
            "faixa_calibrada_min": Decimal("0"),
            "faixa_calibrada_max": Decimal("1000"),
            "unidade_calibrada": unidade,
            "snapshot_equipamento_json": {"tag": equipamento.tag},
        }
        if subcontratado_id is not None:
            campos["subcontratado_id"] = subcontratado_id
        if executor_id is not None:
            campos["executor_id"] = executor_id
        return Calibracao.objects.create(**campos)


def criar_orcamento_incerteza(tenant, calibracao) -> OrcamentoIncerteza:
    """Pai dos `OrcamentoPorPonto` (FK NOT NULL). Agregado pior-caso não-normativo."""
    with run_in_tenant_context(tenant.id):
        return OrcamentoIncerteza.objects.create(
            tenant=tenant,
            calibracao=calibracao,
            u_combinada=Decimal("0.4"),
            grau_liberdade_efetivo=Decimal("60"),
            U_expandida=Decimal("0.9"),
            documentacao_agregacao="orcamento de incerteza de teste (fixture M8 PG)",
            versao_motor_calculo="v1.0.0",
            algoritmo_1_resultado={"U_expandida": "0.9"},
            replay_determinismo_hash="v01$replay",
            calculado_em=timezone.now(),
        )


def criar_ponto_orcamento(
    tenant,
    orcamento,
    *,
    ponto: str,
    U: str,
    k: str = "2",
    nivel: str = "0.9545",
    nu: str = "60",
    n: int = 10,
) -> OrcamentoPorPonto:
    """1 `OrcamentoPorPonto` (read-model `U(ponto)` ADR-0077). `u_combinada = U/k`."""
    with run_in_tenant_context(tenant.id):
        return OrcamentoPorPonto.objects.create(
            tenant=tenant,
            orcamento_incerteza=orcamento,
            ponto_calibracao=Decimal(ponto),
            u_combinada_no_ponto=Decimal(U) / Decimal(k),
            U_expandida_no_ponto=Decimal(U),
            k_no_ponto=Decimal(k),
            nivel_confianca_no_ponto=Decimal(nivel),
            grau_liberdade_efetivo_no_ponto=Decimal(nu),
            replay_determinismo_hash_no_ponto="v01$ponto",
            metodo_tipo_a_ponto=MetodoTipoAPonto.SX_PROPRIO.value,
            n_repeticoes_ponto=n,
            lei_escalonamento_aplicada=LeiEscalonamento.CONSTANTE.value,
            tipo_a_insuficiente=False,
            s_tipo_a_no_ponto=None,
        )


def criar_escopo_cmc_confirmado(
    tenant,
    *,
    grandeza: str = "massa",
    faixa_min: Decimal = Decimal("0"),
    faixa_max: Decimal = Decimal("1000"),
    unidade: str = "g",
    cmc_valor: Decimal = Decimal("0.5"),
):
    """1 `EscopoCMC` CONFIRMADO + vigente (RBC acreditado, CMC ABSOLUTA) que cobre a
    faixa. Vigência início 30d no passado para cobrir a `data_emissao` (que o
    cmc_para_adapter converte para meia-noite UTC do dia). Usado nos testes RBC."""
    from src.domain.metrologia.escopos_cmc.enums import EstadoEscopo
    from src.infrastructure.metrologia.escopos_cmc.models import EscopoCMC

    sfx = uuid4().hex[:6]
    with run_in_tenant_context(tenant.id):
        inicio = timezone.now() - timedelta(days=30)
        return EscopoCMC.objects.create(
            tenant=tenant,
            grandeza=grandeza,
            faixa_min=faixa_min,
            faixa_max=faixa_max,
            unidade=unidade,
            cmc_forma="ABSOLUTA",
            cmc_valor=cmc_valor,
            cmc_unidade=unidade,
            rbc_acreditado=True,
            numero_escopo_cgcre=f"CRL {1000 + (uuid4().int % 9000):04d}-{sfx[:2]}",
            estado=EstadoEscopo.CONFIRMADO.value,
            vigente_a_partir=inicio,
            vigencia_inicio=inicio,
        )


def criar_leituras(
    tenant,
    calibracao,
    *,
    ponto: str,
    valores: Sequence[str] | Iterable[str],
    unidade: str = "g",
) -> None:
    """N `Leitura` (repetições) de um ponto. A média (Decimal) vira o
    `valor_reportado` do `PontoMedido` lido por `listar_pontos_medidos`."""
    with run_in_tenant_context(tenant.id):
        for i, v in enumerate(valores, start=1):
            Leitura.objects.create(
                tenant=tenant,
                calibracao=calibracao,
                ponto_calibracao=Decimal(ponto),
                numero_repeticao=i,
                valor_lido=Decimal(v),
                unidade=unidade,
                timestamp=timezone.now(),
                executor_id_hash="v01$exec",
            )
