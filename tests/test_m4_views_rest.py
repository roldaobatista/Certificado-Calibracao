"""Tests Fase 8 esqueleto REST — serializers DRF + smoke do ViewSet.

Foca em validacao de payload via serializers (sem DB). Tests de
integracao com Django ORM ficam Wave A quando RequireAuthz + middleware
multitenant estiverem ligados no router principal.
"""

from __future__ import annotations

from uuid import uuid4

from src.infrastructure.calibracao.serializers import (
    CancelarCalibracaoSerializer,
    ConfigurarCalibracaoSerializer,
    RecepcionarCalibracaoSerializer,
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
