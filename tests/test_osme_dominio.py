"""Frente `os-multi-equipamento` — Fatia 1a (T-OSME-014): dominio puro, sem banco.

Cobre os casos obrigatorios da Fatia 1a:
  - TipoItemComercial tem os 3 valores corretos (T-OSME-010)
  - ItemComercialOSSnapshot constroi e e imutavel (T-OSME-011)
  - ItemOrcamento aceita equipamento_id=None (default) e equipamento_id=<uuid>
    (parte de T-OSME-013)

Refs: T-OSME-010/011/013; D-OSME-3; spec os-multi-equipamento §3-4.
"""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from src.application.operacao.os.abrir_os_via_orcamento import ItemOrcamento
from src.domain.operacao.os.entities import ItemComercialOSSnapshot
from src.domain.operacao.os.value_objects import TipoAtividade, TipoItemComercial

# ---------------------------------------------------------------------------
# Fixtures / constantes
# ---------------------------------------------------------------------------

_T = UUID("00000000-0000-4000-8000-000000000001")  # tenant fixo
_OS = UUID("00000000-0000-4000-8000-000000000002")  # os fixo


# ---------------------------------------------------------------------------
# T-OSME-010 — TipoItemComercial
# ---------------------------------------------------------------------------


class TestTipoItemComercial:
    def test_tem_tres_membros(self) -> None:
        """TipoItemComercial deve ter exatamente 3 valores (D-OSME-3)."""
        assert len(TipoItemComercial) == 3

    def test_valores_corretos(self) -> None:
        """Valores dos membros batem com a spec (D-OSME-3)."""
        assert TipoItemComercial.DESLOCAMENTO.value == "deslocamento"
        assert TipoItemComercial.TAXA_VISITA.value == "taxa_visita"
        assert TipoItemComercial.OUTRO.value == "outro"

    def test_e_str_enum(self) -> None:
        """TipoItemComercial herda de str — compativel com serializer JSON."""
        assert isinstance(TipoItemComercial.DESLOCAMENTO, str)
        assert TipoItemComercial.DESLOCAMENTO == "deslocamento"


# ---------------------------------------------------------------------------
# T-OSME-011 — ItemComercialOSSnapshot
# ---------------------------------------------------------------------------


class TestItemComercialOSSnapshot:
    def _snapshot(self, **kwargs) -> ItemComercialOSSnapshot:
        defaults: dict = {
            "id": uuid4(),
            "tenant_id": _T,
            "os_id": _OS,
            "tipo": TipoItemComercial.DESLOCAMENTO,
            "descricao_publica": "Deslocamento padrao",
            "valor": Decimal("75.00"),
            "quantidade": 1,
            "origem_item_id": None,
        }
        defaults.update(kwargs)
        return ItemComercialOSSnapshot(**defaults)

    def test_constroi_happy(self) -> None:
        """ItemComercialOSSnapshot constroi com todos os campos validos."""
        snap = self._snapshot()
        assert snap.tipo == TipoItemComercial.DESLOCAMENTO
        assert snap.valor == Decimal("75.00")
        assert snap.origem_item_id is None

    def test_origem_item_id_opcional(self) -> None:
        """origem_item_id aceita None e UUID (rastreio opcional do orcamento)."""
        snap_sem = self._snapshot(origem_item_id=None)
        snap_com = self._snapshot(origem_item_id=uuid4())
        assert snap_sem.origem_item_id is None
        assert isinstance(snap_com.origem_item_id, UUID)

    def test_imutavel_setar_valor_levanta(self) -> None:
        """frozen=True: setattr() em campo 'valor' deve levantar FrozenInstanceError.

        Nota: object.__setattr__ bypassa slots (nao levanta). Usar setattr() ou
        atribuicao direta que chama __setattr__ do dataclass.
        """
        snap = self._snapshot()
        with pytest.raises((AttributeError, TypeError)):
            snap.valor = Decimal("0.00")

    def test_imutavel_setar_tipo_levanta(self) -> None:
        """Verificacao adicional: setattr() em campo 'tipo' levanta FrozenInstanceError."""
        snap = self._snapshot()
        with pytest.raises((AttributeError, TypeError)):
            snap.tipo = TipoItemComercial.OUTRO

    def test_todos_os_tipos_constroem(self) -> None:
        """Todos os 3 TipoItemComercial devem ser aceitos no snapshot."""
        for tipo in TipoItemComercial:
            snap = self._snapshot(tipo=tipo)
            assert snap.tipo == tipo


# ---------------------------------------------------------------------------
# T-OSME-013 (parte) — ItemOrcamento.equipamento_id
# ---------------------------------------------------------------------------


class TestItemOrcamentoEquipamentoId:
    def _item(self, **kwargs) -> ItemOrcamento:
        defaults: dict = {
            "tipo": TipoAtividade.MANUTENCAO_CORRETIVA,
            "sequencia": 1,
            "valor_unitario": Decimal("100.00"),
            "requer_recebimento": False,
        }
        defaults.update(kwargs)
        return ItemOrcamento(**defaults)

    def test_default_equipamento_id_none(self) -> None:
        """ItemOrcamento sem equipamento_id => None (item comercial, D-OSME-3)."""
        item = self._item()
        assert item.equipamento_id is None

    def test_aceita_uuid_equipamento(self) -> None:
        """ItemOrcamento com equipamento_id UUID => atividade tecnica (AC-OSME-002-2)."""
        eid = uuid4()
        item = self._item(equipamento_id=eid)
        assert item.equipamento_id == eid

    def test_call_sites_existentes_nao_quebram(self) -> None:
        """Call-sites que constroem ItemOrcamento sem equipamento_id continuam funcionando."""
        item = ItemOrcamento(
            tipo=TipoAtividade.CALIBRACAO,
            sequencia=2,
            valor_unitario=Decimal("200.00"),
            requer_recebimento=True,
        )
        assert item.equipamento_id is None

    def test_imutavel(self) -> None:
        """ItemOrcamento tambem e frozen — setattr() deve levantar FrozenInstanceError."""
        item = self._item(equipamento_id=uuid4())
        with pytest.raises((AttributeError, TypeError)):
            item.equipamento_id = None
