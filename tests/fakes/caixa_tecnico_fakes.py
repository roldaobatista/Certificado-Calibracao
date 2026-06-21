"""Fakes das 5 portas do domínio caixa_tecnico (Fatia 2 — T-CT-030).

Implementam os 5 Protocols de ``src/domain/caixa_tecnico/portas.py``
para uso nos testes de aplicação/REST (sem banco real, sem I/O).

Fakes:
  - FotoComprovanteStorageFake  — retorna foto_hash determinístico
  - OSReferenciaFake            — sempre retorna True (OS existe)
  - ConsentimentoGpsFake        — configurável on/off
  - ColaboradorCaixaFake        — sempre retorna True (é técnico)
  - ColaboradorReferenciadoFake — sempre retorna False (não referenciado)

Zero Django. Zero I/O.
"""

from __future__ import annotations

import hashlib
from uuid import UUID


class FotoComprovanteStorageFake:
    """Fake do ``FotoComprovanteStoragePort``.

    ``validar_e_processar`` retorna (bytes_originais, hash_sha256_hex).
    ``salvar`` retorna URL content-addressed determinística.
    """

    def validar_e_processar(
        self,
        bytes_foto: bytes,
        mime_type: str,
    ) -> tuple[bytes, str]:
        """Calcula SHA-256 dos bytes como foto_hash (sem EXIF strip — fake).

        Determinístico: mesmos bytes → mesmo hash.
        """
        foto_hash = hashlib.sha256(bytes_foto).hexdigest()  # audit-pii-salt: skip -- SHA-256 de bytes de imagem (binario, nao PII textual) em FAKE de teste; hash deterministico p/ isolamento; molde equipamentos/services_foto_storage.py
        return bytes_foto, foto_hash

    def salvar(
        self,
        tenant_id: UUID,
        foto_hash: str,
        bytes_limpos: bytes,
    ) -> str:
        """Retorna URL fake content-addressed por tenant."""
        return f"/media/caixa_tecnico/{tenant_id}/{foto_hash[:2]}/{foto_hash}"


class OSReferenciaFake:
    """Fake do ``OSReferenciaPort``.

    Sempre retorna ``True`` (OS existe no tenant) para testes que não
    exercitam a validação de OS.

    Para testes que precisam de OS ausente, instanciar com ``os_existe=False``.
    """

    def __init__(self, os_existe: bool = True) -> None:
        self._os_existe = os_existe

    def existe_os(self, os_id: UUID, tenant_id: UUID) -> bool:
        return self._os_existe


class ConsentimentoGpsFake:
    """Fake do ``ConsentimentoGpsPort``.

    Configurável: ``opt_in_ativo=True`` simula colaborador com opt-in GPS;
    ``opt_in_ativo=False`` simula ausência de consentimento.

    Permite alterar via ``opt_in_ativo`` em tempo de execução para cenários
    de teste que precisam variar o comportamento por item/chamada.
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
    """Fake do ``ColaboradorCaixaPort``.

    Sempre retorna ``True`` (colaborador é técnico) para testes de fluxo
    normal. Para testes de validação de papel, instanciar com ``e_tecnico=False``.
    """

    def __init__(self, e_tecnico: bool = True) -> None:
        self._e_tecnico = e_tecnico

    def e_tecnico(self, tenant_id: UUID, colaborador_id: UUID) -> bool:
        return self._e_tecnico


class ColaboradorReferenciadoFake:
    """Fake do ``ColaboradorReferenciadoPort``.

    Sempre retorna ``False`` (colaborador não está referenciado) para testes
    de fluxo normal (hard-delete permitido). Para testes de guard, instanciar
    com ``esta_referenciado=True``.
    """

    def __init__(self, esta_referenciado: bool = False) -> None:
        self._esta_referenciado = esta_referenciado

    def esta_referenciado(self, tenant_id: UUID, colaborador_id: UUID) -> bool:
        return self._esta_referenciado
