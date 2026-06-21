"""Stubs/Fakes Wave A das portas do caixa_tecnico (Fatia 2).

Implementações TEMPORÁRIAS das portas do domínio para rodar sem adapters reais.
Fatia 3a substitui por adapters reais (OS, colaboradores, GPS, storage B2).

Exportados como aliases para facilitar uso nos testes e na view Wave A.

# tests-coverage: tests/fakes/caixa_tecnico_fakes.py
"""

from __future__ import annotations

import hashlib
from uuid import UUID


class FotoComprovanteStorageFake:
    """Fake do ``FotoComprovanteStoragePort`` (Wave A).

    Calcula SHA-256 dos bytes como foto_hash (sem EXIF strip).
    Retorna URL fake content-addressed.

    Fatia 3a substitui por ``FotoComprovanteStorageLocal`` (real).
    """

    def validar_e_processar(
        self,
        bytes_foto: bytes,
        mime_type: str,
    ) -> tuple[bytes, str]:
        foto_hash = hashlib.sha256(bytes_foto).hexdigest()  # audit-pii-salt: skip -- SHA-256 de bytes de imagem (binario, nao PII textual) em FAKE de teste Wave A; hash deterministico; molde equipamentos/services_foto_storage.py
        return bytes_foto, foto_hash

    def salvar(
        self,
        tenant_id: UUID,
        foto_hash: str,
        bytes_limpos: bytes,
    ) -> str:
        return f"/media/caixa_tecnico/{tenant_id}/{foto_hash[:2]}/{foto_hash}"


class OSReferenciaFake:
    """Fake do ``OSReferenciaPort`` (Wave A). Sempre retorna True."""

    def __init__(self, os_existe: bool = True) -> None:
        self._os_existe = os_existe

    def existe_os(self, os_id: UUID, tenant_id: UUID) -> bool:
        return self._os_existe


class ConsentimentoGpsFake:
    """Fake do ``ConsentimentoGpsPort`` (Wave A).

    Configurável: ``opt_in_ativo`` define o retorno de ``opt_in_vigente``.
    Default: False (sem opt-in) → gps_aviso=True na despesa, sem bloquear.
    """

    def __init__(self, opt_in_ativo: bool = False) -> None:
        self.opt_in_ativo = opt_in_ativo

    def opt_in_vigente(
        self,
        tenant_id: UUID,
        colaborador_id: UUID,
        na_data: object,
    ) -> bool:
        return self.opt_in_ativo


class ColaboradorCaixaFake:
    """Fake do ``ColaboradorCaixaPort`` (Wave A). Sempre retorna True."""

    def __init__(self, e_tecnico: bool = True) -> None:
        self._e_tecnico = e_tecnico

    def e_tecnico(self, tenant_id: UUID, colaborador_id: UUID) -> bool:
        return self._e_tecnico


class ColaboradorReferenciadoFake:
    """Fake do ``ColaboradorReferenciadoPort`` (Wave A). Sempre retorna False."""

    def __init__(self, esta_referenciado: bool = False) -> None:
        self._esta_referenciado = esta_referenciado

    def esta_referenciado(self, tenant_id: UUID, colaborador_id: UUID) -> bool:
        return self._esta_referenciado
