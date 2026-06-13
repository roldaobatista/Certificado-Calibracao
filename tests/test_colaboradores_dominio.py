"""Frente `colaboradores` — Fatia 1a (T-COL-016): domínio puro, sem banco.

Cobre todos os casos obrigatórios da task T-COL-016:
  - Signatário sem usuario_id → SignatarioSemUsuario
  - RT não casa → SignatarioRtNaoCasa
  - Escopo não vigente → SignatarioSemEscopo
  - Signatário OK (perfil A) → sem erro
  - 2º DONO → DonoJaExiste
  - MOTORISTA sem CNH → pendencia=True SEM erro (R-COL-1)
  - TERCEIRIZADO+CTPS → coerencia_documento_vinculo retorna False (alerta)
  - Cascade revoga papéis (ativos revogados; já-revogados intocados)
  - Payload desligamento v9 completo (todos os campos, chave idempotente)
  - Comissão fora 0..100 → ComissaoForaDaFaixa
  - Habilidade catalogo XOR livre → ValueError quando ambos ou nenhum

Refs: T-COL-016; spec §5 INV-COL-*; D-COL-10/11/13; R-COL-1.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from src.domain.rh_frota_qualidade.colaboradores.entities import (
    CatalogoHabilidade,
    Colaborador,
    PapelColaboradorAtribuido,
)
from src.domain.rh_frota_qualidade.colaboradores.enums import (
    NivelHabilidade,
    PapelColaborador,
    TipoDocumento,
    Vinculo,
)
from src.domain.rh_frota_qualidade.colaboradores.erros import (
    ComissaoForaDaFaixa,
    DonoJaExiste,
    SignatarioRtNaoCasa,
    SignatarioSemEscopo,
    SignatarioSemUsuario,
)
from src.domain.rh_frota_qualidade.colaboradores.portas import (
    ColaboradorReferenciadoPort,
    StubColaboradorReferenciadoConservador,
)
from src.domain.rh_frota_qualidade.colaboradores.regras import (
    cascade_revoga_papeis,
    coerencia_documento_vinculo,
    derivar_ativo,
    montar_payload_desligamento,
    pendencia_cnh_motorista,
    pode_atribuir_signatario,
    validar_catalogo_xor_livre,
    validar_comissao,
    validar_dono_unico,
)
from src.domain.shared.value_objects import CPF

# ---------------------------------------------------------------------------
# Fixtures e helpers
# ---------------------------------------------------------------------------

_T = UUID("00000000-0000-4000-8000-000000000001")  # tenant fixo
_AGORA = datetime(2026, 6, 13, 12, 0, 0, tzinfo=UTC)
_HOJE = date(2026, 6, 13)

# CPF válido para os testes (CPF publicamente conhecido como válido para testes)
_CPF_VALIDO = "529.982.247-25"


def _colaborador(
    *,
    usuario_id: UUID | None = None,
    vinculo: Vinculo = Vinculo.CLT,
    data_desligamento: date | None = None,
    deletado_em: datetime | None = None,
    comissao_pct: Decimal = Decimal("10.00"),
) -> Colaborador:
    """Fábrica de Colaborador para os testes."""
    return Colaborador(
        id=uuid4(),
        tenant_id=_T,
        nome="João da Silva",
        cpf=CPF(_CPF_VALIDO),
        email="joao@exemplo.com",
        telefone="(65) 99999-0001",
        vinculo=vinculo,
        data_admissao=date(2025, 1, 1),
        comissao_default_pct=comissao_pct,
        observacao="",
        usuario_id=usuario_id,
        data_desligamento=data_desligamento,
        deletado_em=deletado_em,
    )


def _papel(
    *,
    colaborador_id: UUID | None = None,
    papel: PapelColaborador = PapelColaborador.TECNICO,
    revogado_em: datetime | None = None,
    data_fim: date | None = None,
    pendencia_cnh: bool = False,
) -> PapelColaboradorAtribuido:
    """Fábrica de PapelColaboradorAtribuido para os testes."""
    return PapelColaboradorAtribuido(
        id=uuid4(),
        colaborador_id=colaborador_id or uuid4(),
        papel=papel,
        data_inicio=date(2025, 1, 1),
        data_fim=data_fim,
        revogado_em=revogado_em,
        pendencia_cnh=pendencia_cnh,
    )


# ---------------------------------------------------------------------------
# T-COL-016 — SIGNATARIO: identidade + escopo (INV-COL-SIGNATARIO-*)
# ---------------------------------------------------------------------------


class TestPodeAtribuirSignatario:
    """Cobre pode_atribuir_signatario — INV-COL-SIGNATARIO-IDENTIDADE/-ESCOPO."""

    def test_sem_usuario_id_levanta_signatario_sem_usuario(self) -> None:
        """Colaborador sem usuario_id → SignatarioSemUsuario (D-COL-11)."""
        with pytest.raises(SignatarioSemUsuario) as info:
            pode_atribuir_signatario(
                usuario_id=None,
                rt_casa=True,
                escopo_vigente=True,
                perfil_tenant="A",
            )
        assert info.value.reason == "SIGNATARIO_SEM_USUARIO"

    def test_rt_nao_casa_levanta_signatario_rt_nao_casa(self) -> None:
        """RTCompetencia não casa com usuario_id → SignatarioRtNaoCasa (D-COL-11)."""
        with pytest.raises(SignatarioRtNaoCasa) as info:
            pode_atribuir_signatario(
                usuario_id=uuid4(),
                rt_casa=False,
                escopo_vigente=True,
                perfil_tenant="A",
            )
        assert info.value.reason == "SIGNATARIO_RT_NAO_CASA"

    def test_escopo_nao_vigente_levanta_signatario_sem_escopo(self) -> None:
        """Escopo do RT não vigente → SignatarioSemEscopo (INV-003 / D-COL-11)."""
        with pytest.raises(SignatarioSemEscopo) as info:
            pode_atribuir_signatario(
                usuario_id=uuid4(),
                rt_casa=True,
                escopo_vigente=False,
                perfil_tenant="A",
            )
        assert info.value.reason == "SIGNATARIO_SEM_ESCOPO"

    def test_signatario_ok_perfil_a_sem_erro(self) -> None:
        """Todos os critérios satisfeitos → nenhuma exceção (path HAPPY)."""
        # Não deve levantar nada
        pode_atribuir_signatario(
            usuario_id=uuid4(),
            rt_casa=True,
            escopo_vigente=True,
            perfil_tenant="A",
        )

    def test_usuario_nulo_tem_precedencia_sobre_rt_nao_casa(self) -> None:
        """Sem usuario_id levanta SignatarioSemUsuario mesmo com rt_casa=False."""
        with pytest.raises(SignatarioSemUsuario):
            pode_atribuir_signatario(
                usuario_id=None,
                rt_casa=False,
                escopo_vigente=False,
                perfil_tenant="A",
            )


# ---------------------------------------------------------------------------
# T-COL-016 — DONO único por tenant (INV-COL-DONO-UNICO)
# ---------------------------------------------------------------------------


class TestValidarDonoUnico:
    """Cobre validar_dono_unico — INV-COL-DONO-UNICO."""

    def test_segundo_dono_levanta_dono_ja_existe(self) -> None:
        """Segundo DONO ativo → DonoJaExiste (D-COL-4)."""
        with pytest.raises(DonoJaExiste) as info:
            validar_dono_unico(dono_ja_existe=True)
        assert info.value.reason == "DONO_JA_EXISTE"

    def test_primeiro_dono_sem_erro(self) -> None:
        """Sem DONO ativo → nenhuma exceção."""
        validar_dono_unico(dono_ja_existe=False)  # Não deve levantar


# ---------------------------------------------------------------------------
# T-COL-016 — MOTORISTA_UMC: pendência de CNH (R-COL-1)
# ---------------------------------------------------------------------------


class TestPendenciaCnhMotorista:
    """Cobre pendencia_cnh_motorista — R-COL-1 (salvar com pendência, sem erro)."""

    def test_sem_cnh_retorna_pendencia_true_sem_erro(self) -> None:
        """Motorista sem CNH → pendencia=True, sem exceção (R-COL-1)."""
        resultado = pendencia_cnh_motorista(tem_cnh=False)
        assert resultado is True

    def test_com_cnh_retorna_pendencia_false(self) -> None:
        """Motorista com CNH → pendencia=False (sem pendência)."""
        resultado = pendencia_cnh_motorista(tem_cnh=True)
        assert resultado is False

    def test_pendencia_nao_levanta_excecao(self) -> None:
        """pendencia_cnh_motorista nunca levanta exceção (R-COL-1)."""
        # Não deve levantar exceção em nenhum caso
        for tem_cnh in (True, False):
            pendencia_cnh_motorista(tem_cnh=tem_cnh)


# ---------------------------------------------------------------------------
# T-COL-016 — Coerência documento × vínculo (INV-COL-DOC-VINCULO)
# ---------------------------------------------------------------------------


class TestCoerenciaDocumentoVinculo:
    """Cobre coerencia_documento_vinculo — INV-COL-DOC-VINCULO."""

    def test_terceirizado_com_ctps_retorna_false(self) -> None:
        """TERCEIRIZADO + CTPS → False (alerta de incompatibilidade)."""
        resultado = coerencia_documento_vinculo(
            tipo=TipoDocumento.CTPS,
            vinculo=Vinculo.TERCEIRIZADO,
        )
        assert resultado is False

    def test_pj_com_ctps_retorna_false(self) -> None:
        """PJ + CTPS → False (minimização LGPD art. 6º III)."""
        resultado = coerencia_documento_vinculo(
            tipo=TipoDocumento.CTPS,
            vinculo=Vinculo.PJ,
        )
        assert resultado is False

    def test_clt_com_ctps_retorna_true(self) -> None:
        """CLT + CTPS → True (coerente)."""
        resultado = coerencia_documento_vinculo(
            tipo=TipoDocumento.CTPS,
            vinculo=Vinculo.CLT,
        )
        assert resultado is True

    def test_terceirizado_com_cnh_retorna_true(self) -> None:
        """TERCEIRIZADO + CNH → True (compatível)."""
        resultado = coerencia_documento_vinculo(
            tipo=TipoDocumento.CNH,
            vinculo=Vinculo.TERCEIRIZADO,
        )
        assert resultado is True

    def test_todos_vinculos_com_cnh_retornam_true(self) -> None:
        """CNH é compatível com todos os vínculos."""
        for vinculo in Vinculo:
            assert (
                coerencia_documento_vinculo(
                    tipo=TipoDocumento.CNH,
                    vinculo=vinculo,
                )
                is True
            )


# ---------------------------------------------------------------------------
# T-COL-016 — Cascade revoga papéis (INV-COL-DESLIGAMENTO-CASCADE)
# ---------------------------------------------------------------------------


class TestCascadeRevogaPapeis:
    """Cobre cascade_revoga_papeis — INV-COL-DESLIGAMENTO-CASCADE."""

    def test_papeis_ativos_sao_revogados(self) -> None:
        """Papéis sem revogado_em e sem data_fim expirada → revogados com momento."""
        colab_id = uuid4()
        papeis = [
            _papel(colaborador_id=colab_id, papel=PapelColaborador.TECNICO),
            _papel(colaborador_id=colab_id, papel=PapelColaborador.ATENDENTE),
        ]
        resultado = cascade_revoga_papeis(papeis=papeis, momento=_AGORA)

        assert len(resultado) == 2
        for p in resultado:
            assert p.revogado_em == _AGORA

    def test_papeis_ja_revogados_nao_sao_modificados(self) -> None:
        """Papéis já revogados → mantidos sem alteração."""
        revogado_antes = datetime(2026, 1, 1, tzinfo=UTC)
        colab_id = uuid4()
        ja_revogado = _papel(
            colaborador_id=colab_id,
            papel=PapelColaborador.TECNICO,
            revogado_em=revogado_antes,
        )
        resultado = cascade_revoga_papeis(papeis=[ja_revogado], momento=_AGORA)

        assert resultado[0].revogado_em == revogado_antes  # não alterado

    def test_mix_ativos_e_revogados(self) -> None:
        """Mix: ativos são revogados; já-revogados são preservados."""
        colab_id = uuid4()
        revogado_antes = datetime(2026, 1, 1, tzinfo=UTC)
        papeis = [
            _papel(colaborador_id=colab_id, papel=PapelColaborador.TECNICO),  # ativo
            _papel(
                colaborador_id=colab_id,
                papel=PapelColaborador.GERENTE,
                revogado_em=revogado_antes,
            ),  # já revogado
        ]
        resultado = cascade_revoga_papeis(papeis=papeis, momento=_AGORA)

        tecnico = next(r for r in resultado if r.papel == PapelColaborador.TECNICO)
        gerente = next(r for r in resultado if r.papel == PapelColaborador.GERENTE)
        assert tecnico.revogado_em == _AGORA
        assert gerente.revogado_em == revogado_antes  # preservado

    def test_lista_vazia_retorna_vazia(self) -> None:
        """Lista vazia → lista vazia (sem erro)."""
        resultado = cascade_revoga_papeis(papeis=[], momento=_AGORA)
        assert resultado == []

    def test_papel_com_data_fim_expirada_nao_e_revogado(self) -> None:
        """Papel com data_fim no passado → não recebe revogado_em."""
        colab_id = uuid4()
        expirado = _papel(
            colaborador_id=colab_id,
            papel=PapelColaborador.TECNICO,
            data_fim=date(2026, 1, 1),  # antes de _AGORA (2026-06-13)
        )
        resultado = cascade_revoga_papeis(papeis=[expirado], momento=_AGORA)
        assert resultado[0].revogado_em is None  # não foi revogado


# ---------------------------------------------------------------------------
# T-COL-016 — Payload desligamento v9 (D-COL-10 / TL-COL-13)
# ---------------------------------------------------------------------------


class TestMontarPayloadDesligamento:
    """Cobre montar_payload_desligamento — payload v9 completo."""

    def test_payload_v9_campos_obrigatorios(self) -> None:
        """Payload v9 deve conter todos os campos da spec §6 (D-COL-10)."""
        colab_id = uuid4()
        data_deslig = date(2026, 6, 13)

        payload = montar_payload_desligamento(
            colaborador_id=colab_id,
            data_desligamento=data_deslig,
            is_rt_signatario=True,
            tipos_servico_assinava=["calibracao_massa", "calibracao_temperatura"],
        )

        assert payload["colaborador_id"] == str(colab_id)
        assert payload["is_rt_signatario"] is True
        assert payload["tipos_servico_assinava"] == [
            "calibracao_massa",
            "calibracao_temperatura",
        ]
        assert payload["comissoes_pendentes_count"] == 0  # stub — GATE-COL-COMISSAO-COUNT
        assert "chave_idempotente" in payload

    def test_chave_idempotente_estavel(self) -> None:
        """Mesmos inputs → mesma chave idempotente (TL-COL-13)."""
        colab_id = UUID("12345678-0000-4000-8000-000000000001")
        data_deslig = date(2026, 6, 13)

        payload1 = montar_payload_desligamento(
            colaborador_id=colab_id,
            data_desligamento=data_deslig,
            is_rt_signatario=False,
            tipos_servico_assinava=[],
        )
        payload2 = montar_payload_desligamento(
            colaborador_id=colab_id,
            data_desligamento=data_deslig,
            is_rt_signatario=False,
            tipos_servico_assinava=[],
        )
        assert payload1["chave_idempotente"] == payload2["chave_idempotente"]

    def test_chave_idempotente_formato(self) -> None:
        """Chave idempotente segue formato `{colaborador_id}:{data_desligamento}`."""
        colab_id = UUID("12345678-0000-4000-8000-000000000001")
        data_deslig = date(2026, 6, 13)

        payload = montar_payload_desligamento(
            colaborador_id=colab_id,
            data_desligamento=data_deslig,
            is_rt_signatario=False,
            tipos_servico_assinava=[],
        )
        chave = payload["chave_idempotente"]
        assert chave == f"{colab_id}:{data_deslig}"

    def test_comissoes_pendentes_count_sempre_zero(self) -> None:
        """comissoes_pendentes_count = 0 stub (GATE-COL-COMISSAO-COUNT)."""
        payload = montar_payload_desligamento(
            colaborador_id=uuid4(),
            data_desligamento=_HOJE,
            is_rt_signatario=False,
            tipos_servico_assinava=[],
        )
        assert payload["comissoes_pendentes_count"] == 0

    def test_tipos_servico_lista_vazia_quando_nao_signatario(self) -> None:
        """Colaborador não-signatário → tipos_servico_assinava vazia."""
        payload = montar_payload_desligamento(
            colaborador_id=uuid4(),
            data_desligamento=_HOJE,
            is_rt_signatario=False,
            tipos_servico_assinava=[],
        )
        assert payload["tipos_servico_assinava"] == []
        assert payload["is_rt_signatario"] is False


# ---------------------------------------------------------------------------
# T-COL-016 — Comissão fora de faixa (D-COL-9)
# ---------------------------------------------------------------------------


class TestValidarComissao:
    """Cobre validar_comissao — D-COL-9 / CHECK 0..100."""

    @pytest.mark.parametrize(
        "pct",
        [Decimal("-0.01"), Decimal("-1"), Decimal("100.01"), Decimal("200")],
    )
    def test_comissao_fora_da_faixa_levanta_erro(self, pct: Decimal) -> None:
        """Comissão fora de [0, 100] → ComissaoForaDaFaixa."""
        with pytest.raises(ComissaoForaDaFaixa) as info:
            validar_comissao(comissao_pct=pct)
        assert info.value.reason == "COMISSAO_FORA_DA_FAIXA"

    @pytest.mark.parametrize(
        "pct",
        [
            Decimal("0"),
            Decimal("0.01"),
            Decimal("50"),
            Decimal("99.99"),
            Decimal("100"),
        ],
    )
    def test_comissao_valida_sem_erro(self, pct: Decimal) -> None:
        """Comissão dentro de [0, 100] → sem exceção."""
        validar_comissao(comissao_pct=pct)  # Não deve levantar


# ---------------------------------------------------------------------------
# T-COL-016 — Habilidade: catalogo XOR livre (D-COL-5)
# ---------------------------------------------------------------------------


class TestValidarCatalogoXorLivre:
    """Cobre validar_catalogo_xor_livre — D-COL-5 (CHECK na migration)."""

    def test_ambos_none_levanta_value_error(self) -> None:
        """Sem catalogo_id E sem descricao_livre → ValueError."""
        with pytest.raises(ValueError, match="XOR"):
            validar_catalogo_xor_livre(catalogo_id=None, descricao_livre=None)

    def test_ambos_preenchidos_levanta_value_error(self) -> None:
        """Com catalogo_id E com descricao_livre → ValueError."""
        with pytest.raises(ValueError, match="XOR"):
            validar_catalogo_xor_livre(
                catalogo_id=uuid4(),
                descricao_livre="Solda MIG/MAG",
            )

    def test_so_catalogo_ok(self) -> None:
        """Só catalogo_id → válido."""
        validar_catalogo_xor_livre(catalogo_id=uuid4(), descricao_livre=None)

    def test_so_livre_ok(self) -> None:
        """Só descricao_livre → válido."""
        validar_catalogo_xor_livre(catalogo_id=None, descricao_livre="Solda MIG/MAG")

    def test_descricao_livre_vazia_equivale_a_none(self) -> None:
        """descricao_livre em branco (strip) sem catalogo → ValueError."""
        with pytest.raises(ValueError, match="XOR"):
            validar_catalogo_xor_livre(catalogo_id=None, descricao_livre="   ")


# ---------------------------------------------------------------------------
# T-COL-016 — derivar_ativo (D-COL-3)
# ---------------------------------------------------------------------------


class TestDerivarAtivo:
    """Cobre derivar_ativo — D-COL-3."""

    def test_sem_desligamento_sem_delete_ativo(self) -> None:
        """Sem data_desligamento e sem deletado_em → ativo=True."""
        assert derivar_ativo(data_desligamento=None, deletado_em=None) is True

    def test_com_desligamento_inativo(self) -> None:
        """Com data_desligamento → ativo=False."""
        assert derivar_ativo(data_desligamento=_HOJE, deletado_em=None) is False

    def test_com_delete_inativo(self) -> None:
        """Com deletado_em → ativo=False."""
        assert derivar_ativo(data_desligamento=None, deletado_em=_AGORA) is False

    def test_ambos_preenchidos_inativo(self) -> None:
        """Ambos preenchidos → ativo=False."""
        assert derivar_ativo(data_desligamento=_HOJE, deletado_em=_AGORA) is False


# ---------------------------------------------------------------------------
# T-COL-016 — Porta e Stub (D-COL-3 / INV-COL-INATIVO)
# ---------------------------------------------------------------------------


class TestPortaColaboradorReferenciado:
    """Cobre ColaboradorReferenciadoPort e StubColaboradorReferenciadoConservador."""

    def test_stub_sempre_retorna_true(self) -> None:
        """Stub conservador → sempre True (bloqueia hard-delete)."""
        stub = StubColaboradorReferenciadoConservador()
        assert stub.esta_referenciado(uuid4(), uuid4()) is True

    def test_stub_implementa_protocol(self) -> None:
        """Stub implementa ColaboradorReferenciadoPort (runtime_checkable)."""
        stub = StubColaboradorReferenciadoConservador()
        assert isinstance(stub, ColaboradorReferenciadoPort)

    def test_stub_para_qualquer_uuid(self) -> None:
        """Stub retorna True para qualquer combinação de UUIDs."""
        stub = StubColaboradorReferenciadoConservador()
        for _ in range(5):
            assert stub.esta_referenciado(uuid4(), uuid4()) is True


# ---------------------------------------------------------------------------
# T-COL-016 — Entidades frozen (spec §4)
# ---------------------------------------------------------------------------


class TestEntidadesFrozen:
    """Verifica que as entidades são imutáveis (frozen=True).

    Nota: `object.__setattr__` BYPASSA o frozen (é o mecanismo interno usado
    em `__post_init__`). O teste correto usa atribuição direta de atributo,
    que aciona o `__setattr__` do próprio dataclass frozen e levanta
    `FrozenInstanceError` (subclasse de `AttributeError`).
    """

    def test_colaborador_e_frozen(self) -> None:
        """Colaborador não permite mutação de campos (frozen dataclass)."""
        colab = _colaborador()
        with pytest.raises(AttributeError):
            colab.nome = "Outro Nome"  # FrozenInstanceError — atribuição direta proibida

    def test_cpf_imutavel(self) -> None:
        """CPF do colaborador não pode ser alterado (frozen dataclass)."""
        colab = _colaborador()
        with pytest.raises(AttributeError):
            colab.cpf = CPF(_CPF_VALIDO)  # FrozenInstanceError — CPF imutável pós-criação

    def test_papel_e_frozen(self) -> None:
        """PapelColaboradorAtribuido não permite mutação (frozen dataclass)."""
        p = _papel()
        with pytest.raises(AttributeError):
            p.papel = PapelColaborador.DONO  # FrozenInstanceError — papel imutável

    def test_catalogo_habilidade_e_frozen(self) -> None:
        """CatalogoHabilidade não permite mutação (frozen dataclass)."""
        cat = CatalogoHabilidade(
            codigo="MASS-001",
            descricao="Calibração de massa",
            grandeza="massa",
        )
        with pytest.raises(AttributeError):
            cat.codigo = "OUTRO"  # FrozenInstanceError — catálogo imutável

    def test_colaborador_ativo_property_derivado(self) -> None:
        """Propriedade `ativo` deriva corretamente do estado do colaborador."""
        ativo = _colaborador()
        assert ativo.ativo is True

        desligado = _colaborador(data_desligamento=_HOJE)
        assert desligado.ativo is False

        deletado = _colaborador(deletado_em=_AGORA)
        assert deletado.ativo is False


# ---------------------------------------------------------------------------
# T-COL-016 — Enums (spec §4 / T-COL-010)
# ---------------------------------------------------------------------------


class TestEnums:
    """Verifica cobertura de valores dos enums (T-COL-010)."""

    def test_vinculo_valores(self) -> None:
        """Vinculo deve ter os 5 valores da spec."""
        valores = {v.value for v in Vinculo}
        assert valores == {"clt", "pj", "estagiario", "socio", "terceirizado"}

    def test_papel_colaborador_valores(self) -> None:
        """PapelColaborador deve ter os 7 valores da spec."""
        valores = {p.value for p in PapelColaborador}
        assert valores == {
            "tecnico",
            "signatario",
            "atendente",
            "gerente",
            "dono",
            "qualidade",
            "motorista_umc",
        }

    def test_nivel_habilidade_valores(self) -> None:
        """NivelHabilidade deve ter os 3 valores da spec."""
        valores = {n.value for n in NivelHabilidade}
        assert valores == {"aprendiz", "capacitado", "mestre"}

    def test_tipo_documento_sem_aso(self) -> None:
        """TipoDocumento não deve ter ASO (R-COL-2)."""
        valores = {t.value for t in TipoDocumento}
        assert "aso" not in valores
        assert valores == {"ctps", "cnh", "certificado_curso", "outro"}
