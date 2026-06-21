"""Use case: lançamento de despesa do técnico de campo (US-CT-002 / Fatia 2).

Orquestra: validação de caixa, processamento de foto, cálculo de valor,
opt-in GPS, idempotência offline e persistência.

Não publica eventos — a view faz isso dentro do ``transaction.atomic``.

Refs: D-CT-3/4/5/6/9; US-CT-002; INV-CT-FOTO-001; INV-LGPD-CONSENT-001.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from uuid import UUID, uuid4

from src.domain.caixa_tecnico.entities import Despesa
from src.domain.caixa_tecnico.enums import (
    CategoriaDespesa,
    EstadoDespesa,
    TipoDespesa,
)
from src.domain.caixa_tecnico.erros import (
    CaixaTecnicoDesligado,
    OSInexistente,
    PeriodoPrestacaoFechado,
)
from src.domain.caixa_tecnico.portas import (
    ConsentimentoGpsPort,
    FotoComprovanteStoragePort,
    OSReferenciaPort,
)
from src.domain.caixa_tecnico.regras.deslocamento import valor_deslocamento
from src.domain.shared.value_objects import Dinheiro
from src.infrastructure.caixa_tecnico.repositories import (
    CaixaTecnicoRepository,
    DespesaRepository,
    PoliticaRepository,
    PrestacaoRepository,
)


@dataclass
class LancarDespesaInput:
    """Parâmetros de entrada para o lançamento de despesa (US-CT-002).

    ``valor_centavos`` é ignorado quando ``categoria == DESLOCAMENTO``
    — o valor é calculado a partir de ``km_percorridos × tarifa_km``.
    ``km_percorridos`` é obrigatório quando ``categoria == DESLOCAMENTO``.
    """

    tenant_id: UUID
    caixa_id: UUID
    foto_bytes: bytes
    foto_mime: str
    categoria: CategoriaDespesa
    valor_centavos: int
    data: date
    colaborador_id: UUID
    descricao: str | None = None
    km_percorridos: int | None = None
    client_offline_id: str | None = None
    os_id: UUID | None = None
    tipo: TipoDespesa = TipoDespesa.NORMAL
    despesa_origem_id: UUID | None = None


@dataclass
class LancarDespesaOutput:
    """Resultado do lançamento de despesa.

    ``gps_aviso`` é True quando o colaborador não possui opt-in GPS vigente.
    A despesa é criada normalmente mesmo sem opt-in — apenas sem coordenadas
    (INV-LGPD-CONSENT-001 / D-CT-6).
    """

    despesa: Despesa
    gps_aviso: bool


class LancarDespesaUseCase:
    """Orquestra o lançamento de uma despesa do técnico de campo.

    Dependências injetadas via construtor (hexagonal — ADR-0007).
    """

    def __init__(
        self,
        caixa_repo: CaixaTecnicoRepository,
        despesa_repo: DespesaRepository,
        politica_repo: PoliticaRepository,
        prestacao_repo: PrestacaoRepository,
        foto_storage: FotoComprovanteStoragePort,
        consentimento_port: ConsentimentoGpsPort,
        os_referencia_port: OSReferenciaPort,
    ) -> None:
        self._caixa_repo = caixa_repo
        self._despesa_repo = despesa_repo
        self._politica_repo = politica_repo
        self._prestacao_repo = prestacao_repo
        self._foto_storage = foto_storage
        self._consentimento_port = consentimento_port
        self._os_referencia_port = os_referencia_port

    def executar(self, inp: LancarDespesaInput) -> LancarDespesaOutput:
        """Executa o lançamento de despesa.

        Fluxo:
        1. Carrega e valida caixa (ativo e não desligado).
        2. Processa e valida foto-comprovante via storage port.
        3. Calcula valor (deslocamento = tarifa × km; demais = valor_centavos).
        4. Verifica acima_limite contra política do tenant.
        5. Verifica opt-in GPS (não bloqueia — apenas sinaliza via gps_aviso).
        6. Verifica período fechado por prestação de contas.
        7. Garante idempotência offline via client_offline_id.
        8. Persiste e retorna.

        Raises:
            ValueError: caixa não encontrado, km ausente para deslocamento,
                        ou client_offline_id duplicado.
            CaixaTecnicoDesligado: caixa desligado (409).
            PeriodoPrestacaoFechado: período já encerrado por prestação (422).
            FotoComprovanteObrigatoria: foto ausente / bytes vazios (412).
            FotoTipoInvalido: MIME fora da allowlist, >5MB ou imagem corrompida (422).
            OSInexistente: os_id informado não existe no tenant (422).
        """
        # 1. Carrega caixa
        caixa = self._caixa_repo.obter_por_id(inp.tenant_id, inp.caixa_id)
        if caixa is None:
            raise ValueError("caixa não encontrado")
        if caixa.esta_desligado:
            raise CaixaTecnicoDesligado(
                f"CaixaTecnico {inp.caixa_id} está desligado — novos lançamentos bloqueados"
            )

        # 1.5. Valida vínculo de OS (D-CT-11 / US-CT-003 / spec §6) — quando informado,
        # a OS precisa existir no tenant (cross-tenant → inexistente). Checagem barata
        # antes do processamento da foto.
        if inp.os_id is not None and not self._os_referencia_port.existe_os(
            inp.os_id, inp.tenant_id
        ):
            raise OSInexistente(
                f"OS {inp.os_id} não existe no tenant {inp.tenant_id} (vínculo inválido)"
            )

        # 2. Processa foto
        bytes_limpos, foto_hash = self._foto_storage.validar_e_processar(
            inp.tenant_id, inp.foto_bytes, inp.foto_mime
        )

        # 3. Calcula valor
        if inp.categoria == CategoriaDespesa.DESLOCAMENTO:
            if inp.km_percorridos is None:
                raise ValueError("km_percorridos é obrigatório para categoria DESLOCAMENTO")
            politica = self._politica_repo.obter_por_tenant(inp.tenant_id)
            tarifa_km = politica.tarifa_km if politica else Dinheiro(0)
            valor = valor_deslocamento(inp.km_percorridos, tarifa_km)
        else:
            politica = self._politica_repo.obter_por_tenant(inp.tenant_id)
            valor = Dinheiro(inp.valor_centavos)

        # 4. Verifica acima_limite
        if (
            politica is not None
            and politica.limite_por_categoria is not None
            and inp.categoria.value in politica.limite_por_categoria
        ):
            acima_limite = valor.centavos > politica.limite_por_categoria[inp.categoria.value]
        else:
            acima_limite = False

        # 5. GPS opt-in (D-CT-6 / INV-LGPD-CONSENT-001)
        # Não bloqueia o lançamento — apenas sinaliza ausência de consentimento.
        # coordenada fica None em Wave A independente do consentimento.
        gps_aviso = False
        opt_in = self._consentimento_port.opt_in_vigente(
            inp.tenant_id, inp.colaborador_id, na_data=inp.data
        )
        if not opt_in:
            gps_aviso = True
        # coordenada = None em Wave A (coleta real de GPS é Wave B)
        coordenada = None

        # 6. Verifica período fechado
        prestacoes = self._prestacao_repo.listar_por_caixa(inp.tenant_id, inp.caixa_id)
        for prestacao in prestacoes:
            if prestacao.periodo.contem(inp.data):
                raise PeriodoPrestacaoFechado(
                    f"Data {inp.data} pertence ao período já encerrado "
                    f"({prestacao.periodo.de} - {prestacao.periodo.ate})"
                )

        # 7. Idempotência offline
        if inp.client_offline_id is not None:
            if self._despesa_repo.existe_gateway_offline(inp.tenant_id, inp.client_offline_id):
                raise ValueError(f"client_offline_id já existe: {inp.client_offline_id}")

        # 8. Salva foto e persiste despesa
        foto_url = self._foto_storage.salvar(inp.tenant_id, foto_hash, bytes_limpos)

        despesa = Despesa(
            despesa_id=uuid4(),
            tenant_id=inp.tenant_id,
            caixa_id=inp.caixa_id,
            tecnico_referencia=caixa.tecnico_referencia,
            categoria=inp.categoria,
            tipo=inp.tipo,
            valor=valor,
            estado=EstadoDespesa.PENDENTE,
            foto_hash=foto_hash,
            foto_url=foto_url,
            data=inp.data,
            criado_em=datetime.now(UTC),
            revision=1,
            descricao=inp.descricao,
            km_percorridos=inp.km_percorridos,
            coordenada=coordenada,
            gps_referencia_pii=None,
            os_id=inp.os_id,
            client_offline_id=inp.client_offline_id,
            despesa_origem_id=inp.despesa_origem_id,
            acima_limite=acima_limite,
        )

        self._despesa_repo.salvar_nova(despesa)

        return LancarDespesaOutput(despesa=despesa, gps_aviso=gps_aviso)
