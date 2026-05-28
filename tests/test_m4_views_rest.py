"""Tests Fase 8 esqueleto REST — serializers DRF + smoke do ViewSet.

Foca em validacao de payload via serializers (sem DB). Tests de
integracao com Django ORM ficam Wave A quando RequireAuthz + middleware
multitenant estiverem ligados no router principal.
"""

from __future__ import annotations

from uuid import uuid4

from src.infrastructure.calibracao.serializers import (
    Aprovar2aConferenciaSerializer,
    AprovarRevisaoSerializer,
    CancelarCalibracaoSerializer,
    ConfigurarCalibracaoSerializer,
    CorrigirLeituraSerializer,
    RecepcionarCalibracaoSerializer,
    RegistrarLeituraSerializer,
    RejeitarRevisaoSerializer,
)


class TestRecepcionarSerializer:
    def _payload_valido(self) -> dict:
        # SEG-CAL-01 (2026-05-27): cliente_referencia_hash + cliente_key_id
        # REMOVIDOS — derivados server-side em views.py.
        return {
            "origem_recepcao": "AVULSA",
            "atividade_os_id": None,
            "instrumento_id": str(uuid4()),
            "snapshot_equipamento_json": {"nome": "Balanca AS6000"},
            "cliente_id": str(uuid4()),
            "tipo_acreditacao": "NAO_RBC",
            "correlation_id": str(uuid4()),
        }

    def test_avulsa_valido(self) -> None:
        s = RecepcionarCalibracaoSerializer(data=self._payload_valido())
        assert s.is_valid(), s.errors

    def test_atividade_os_com_id_valido(self) -> None:
        payload = self._payload_valido()
        payload["origem_recepcao"] = "ATIVIDADE_OS"
        payload["atividade_os_id"] = str(uuid4())
        s = RecepcionarCalibracaoSerializer(data=payload)
        assert s.is_valid(), s.errors

    def test_atividade_os_sem_id_invalido(self) -> None:
        payload = self._payload_valido()
        payload["origem_recepcao"] = "ATIVIDADE_OS"
        payload["atividade_os_id"] = None
        s = RecepcionarCalibracaoSerializer(data=payload)
        assert not s.is_valid()

    def test_avulsa_com_id_invalido(self) -> None:
        payload = self._payload_valido()
        payload["origem_recepcao"] = "AVULSA"
        payload["atividade_os_id"] = str(uuid4())
        s = RecepcionarCalibracaoSerializer(data=payload)
        assert not s.is_valid()

    def test_seg_cal_01_serializer_ignora_hash_no_body(self) -> None:
        """SEG-CAL-01 (1a passada Familia 5): mesmo se cliente mandar
        cliente_referencia_hash no body, serializer NAO declara o campo
        — `validated_data` nao carrega referencia falsificada."""
        payload = self._payload_valido()
        payload["cliente_referencia_hash"] = "v01$ATACANTE_PROIBIDO"
        payload["cliente_key_id"] = "key-roubada"
        s = RecepcionarCalibracaoSerializer(data=payload)
        assert s.is_valid(), s.errors
        assert "cliente_referencia_hash" not in s.validated_data
        assert "cliente_key_id" not in s.validated_data

    def test_tipo_acreditacao_fora_whitelist_recusa(self) -> None:
        payload = self._payload_valido()
        payload["tipo_acreditacao"] = "EUROLAB"
        s = RecepcionarCalibracaoSerializer(data=payload)
        assert not s.is_valid()


class TestConfigurarSerializer:
    def _payload(self) -> dict:
        return {
            "revision_esperada": 0,
            "procedimento_id": str(uuid4()),
            "procedimento_versao_snapshot": {
                "codigo": "PRO-CAL-MASSA",
                "versao": "1.0.0",
                "hash_anexo": "v01$abc=",
            },
            "regra_decisao": "ACEITACAO_SIMPLES",
            "regra_decisao_acordada_em": "2026-06-30T12:00:00Z",
            "regra_decisao_acordada_documento_id": str(uuid4()),
            "escopo_id": None,
            "analise_critica_pedido_id": None,
            "analise_critica_pedido_inline_texto": "Cliente confirmou necessidade de calibracao RBC em 2026-06-30.",
            "capacidade_tecnica_confirmada_por_user_id": str(uuid4()),
        }

    def test_payload_valido(self) -> None:
        s = ConfigurarCalibracaoSerializer(data=self._payload())
        assert s.is_valid(), s.errors

    def test_revision_negativa_recusa(self) -> None:
        payload = self._payload()
        payload["revision_esperada"] = -1
        s = ConfigurarCalibracaoSerializer(data=payload)
        assert not s.is_valid()

    def test_regra_decisao_fora_whitelist_recusa(self) -> None:
        payload = self._payload()
        payload["regra_decisao"] = "QUALQUER_REGRA"
        s = ConfigurarCalibracaoSerializer(data=payload)
        assert not s.is_valid()


class TestCancelarSerializer:
    """SEG-CAL-07 (2026-05-27): motivo_hash REMOVIDO do body — derivado
    server-side em views.py via derivar_hash_texto_canonicalizado."""

    def test_payload_valido(self) -> None:
        s = CancelarCalibracaoSerializer(
            data={
                "revision_esperada": 1,
                "motivo_cancelamento_canonicalizado": (
                    "cliente desistiu do servico apos analise critica"
                ),
            }
        )
        assert s.is_valid(), s.errors

    def test_motivo_curto_recusa(self) -> None:
        s = CancelarCalibracaoSerializer(
            data={
                "revision_esperada": 1,
                "motivo_cancelamento_canonicalizado": "curto",
            }
        )
        assert not s.is_valid()

    def test_motivo_hash_no_body_eh_ignorado(self) -> None:
        """SEG-CAL-07: cliente nao pode mais mandar motivo_hash."""
        s = CancelarCalibracaoSerializer(
            data={
                "revision_esperada": 1,
                "motivo_cancelamento_canonicalizado": "x" * 50,
                "motivo_hash": "v01$ATACANTE",
            }
        )
        assert s.is_valid(), s.errors
        assert "motivo_hash" not in s.validated_data


class TestRegistrarLeituraSerializer:
    """T-CAL-124 — LeituraViewSet.registrar."""

    def _payload(self) -> dict:
        return {
            "ponto_calibracao": "10.000",
            "numero_repeticao": 1,
            "valor_lido": "10.001",
            "unidade": "kg",
            "origem": "MANUAL",
            "timestamp": "2026-06-30T12:00:00Z",
            "correlation_id": str(uuid4()),
        }

    def test_payload_valido(self) -> None:
        s = RegistrarLeituraSerializer(data=self._payload())
        assert s.is_valid(), s.errors

    def test_client_event_id_opcional(self) -> None:
        payload = self._payload()
        payload["client_event_id"] = str(uuid4())
        s = RegistrarLeituraSerializer(data=payload)
        assert s.is_valid(), s.errors
        assert s.validated_data["client_event_id"] is not None

    def test_executor_id_hash_no_body_eh_ignorado(self) -> None:
        """SEG-CAL-09: cliente nao pode spoofar executor."""
        payload = self._payload()
        payload["executor_id_hash"] = "v01$ATACANTE"
        s = RegistrarLeituraSerializer(data=payload)
        assert s.is_valid(), s.errors
        assert "executor_id_hash" not in s.validated_data

    def test_numero_repeticao_zero_recusa(self) -> None:
        payload = self._payload()
        payload["numero_repeticao"] = 0
        s = RegistrarLeituraSerializer(data=payload)
        assert not s.is_valid()

    def test_origem_fora_whitelist_recusa(self) -> None:
        payload = self._payload()
        payload["origem"] = "INSTRUMENTO_DESCONHECIDO"
        s = RegistrarLeituraSerializer(data=payload)
        assert not s.is_valid()


class TestCorrigirLeituraSerializer:
    """T-CAL-124 — LeituraViewSet.corrigir (rasura cl. 7.5)."""

    def _payload(self) -> dict:
        return {
            "valor_corrigido": "10.005",
            "razao_correcao_canonicalizada": (
                "valor lido com casa decimal trocada — releitura confirmada"
            ),
            "corrigido_em": "2026-06-30T12:05:00Z",
            "correlation_id": str(uuid4()),
        }

    def test_payload_valido(self) -> None:
        s = CorrigirLeituraSerializer(data=self._payload())
        assert s.is_valid(), s.errors

    def test_razao_curta_recusa(self) -> None:
        payload = self._payload()
        payload["razao_correcao_canonicalizada"] = "curto"
        s = CorrigirLeituraSerializer(data=payload)
        assert not s.is_valid()

    def test_hashes_no_body_sao_ignorados(self) -> None:
        """SEG-CAL-08/09: razao_correcao_hash + corretor_id_hash sao
        derivados server-side; valores no body sao descartados."""
        payload = self._payload()
        payload["razao_correcao_hash"] = "v01$ATACANTE_HASH"
        payload["corretor_id_hash"] = "v01$ATACANTE_USER"
        s = CorrigirLeituraSerializer(data=payload)
        assert s.is_valid(), s.errors
        assert "razao_correcao_hash" not in s.validated_data
        assert "corretor_id_hash" not in s.validated_data


def _snapshot_competencia_valido() -> dict:
    return {
        "grandeza": "massa",
        "faixa_min": "0",
        "faixa_max": "10000",
        "vigencia_inicio": "2025-01-01",
        "vigencia_fim": "2028-12-31",
        "rt_competencia_id": str(uuid4()),
    }


class TestAprovarRevisaoSerializer:
    """T-CAL-126 — RevisaoViewSet.aprovar."""

    def _payload(self) -> dict:
        return {
            "revision_esperada": 2,
            "snapshot_competencia_revisor_json": _snapshot_competencia_valido(),
        }

    def test_payload_valido(self) -> None:
        s = AprovarRevisaoSerializer(data=self._payload())
        assert s.is_valid(), s.errors

    def test_com_excecao_motivo_valido(self) -> None:
        payload = self._payload()
        payload["excecao_motivo"] = "lab_unico_rt"
        s = AprovarRevisaoSerializer(data=payload)
        assert s.is_valid(), s.errors

    def test_revisor_id_no_body_eh_ignorado(self) -> None:
        """SEG-CAL-09: cliente nao pode spoofar revisor."""
        payload = self._payload()
        payload["revisor_id"] = str(uuid4())
        s = AprovarRevisaoSerializer(data=payload)
        assert s.is_valid(), s.errors
        assert "revisor_id" not in s.validated_data

    def test_snapshot_sem_chave_obrigatoria_recusa(self) -> None:
        payload = self._payload()
        del payload["snapshot_competencia_revisor_json"]["grandeza"]
        s = AprovarRevisaoSerializer(data=payload)
        assert not s.is_valid()

    def test_revision_negativa_recusa(self) -> None:
        payload = self._payload()
        payload["revision_esperada"] = -1
        s = AprovarRevisaoSerializer(data=payload)
        assert not s.is_valid()


class TestRejeitarRevisaoSerializer:
    """T-CAL-126 — RevisaoViewSet.rejeitar."""

    def _payload(self) -> dict:
        return {
            "revision_esperada": 2,
            "motivo_rejeicao_canonicalizado": (
                "ponto 5kg apresentou desvio fora do esperado pelo procedimento"
            ),
        }

    def test_payload_valido(self) -> None:
        s = RejeitarRevisaoSerializer(data=self._payload())
        assert s.is_valid(), s.errors

    def test_motivo_curto_recusa(self) -> None:
        payload = self._payload()
        payload["motivo_rejeicao_canonicalizado"] = "curto"
        s = RejeitarRevisaoSerializer(data=payload)
        assert not s.is_valid()


class TestAprovar2aConferenciaSerializer:
    """T-CAL-127 — ConferenciaViewSet.aprovar_2a."""

    def _payload(self) -> dict:
        return {
            "revision_esperada": 3,
            "snapshot_competencia_conferente_json": (
                _snapshot_competencia_valido()
            ),
        }

    def test_payload_valido(self) -> None:
        s = Aprovar2aConferenciaSerializer(data=self._payload())
        assert s.is_valid(), s.errors

    def test_com_excecao_completa_valido(self) -> None:
        payload = self._payload()
        payload["excecao_motivo"] = "lab_unico_rt"
        payload["excecao_2a_conf_id"] = str(uuid4())
        s = Aprovar2aConferenciaSerializer(data=payload)
        assert s.is_valid(), s.errors

    def test_conferente_id_no_body_eh_ignorado(self) -> None:
        """SEG-CAL-09: cliente nao pode spoofar conferente."""
        payload = self._payload()
        payload["conferente_id"] = str(uuid4())
        s = Aprovar2aConferenciaSerializer(data=payload)
        assert s.is_valid(), s.errors
        assert "conferente_id" not in s.validated_data

    def test_snapshot_sem_chave_obrigatoria_recusa(self) -> None:
        payload = self._payload()
        del payload["snapshot_competencia_conferente_json"]["rt_competencia_id"]
        s = Aprovar2aConferenciaSerializer(data=payload)
        assert not s.is_valid()
