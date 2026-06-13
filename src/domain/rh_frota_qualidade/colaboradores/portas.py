"""Portas (Protocols) do módulo `colaboradores` (T-COL-014).

`ColaboradorReferenciadoPort`: contrato para verificar se um colaborador está
  referenciado em módulos a jusante (OS, certificados, comissões) antes de
  permitir hard-delete físico (INV-COL-INATIVO / D-COL-3 / ADR-0066).

`StubColaboradorReferenciadoConservador`: implementação fail-safe que SEMPRE
  retorna True (assume referenciado) → bloqueia hard-delete conservadoramente.
  Substituto até os módulos a jusante existirem (fail-open lazy ADR-0066 cabe
  aqui: consulta a módulo inexistente, porta síncrona, blocking adequado).

`AnexoStoragePort`: contrato para persistência de arquivo de documento do
  colaborador (CTPS, CNH, foto, etc.). Molde:
  `src/application/metrologia/procedimentos_calibracao/anexo_storage.py`.

Molde: `CustoProvider` / `StubCustoProvider` da precificacao.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable
from uuid import UUID


@runtime_checkable
class AnexoStoragePort(Protocol):
    """Porta de armazenamento de arquivo de documento do colaborador (T-COL-032).

    Contrato estrutural (duck-typing) — qualquer implementação que exponha
    `salvar(pdf_bytes, nome_sugerido)` satisfaz a porta.

    Molde: `src/application/metrologia/procedimentos_calibracao/anexo_storage.py`.
    """

    def salvar(self, *, pdf_bytes: bytes, nome_sugerido: str) -> str:
        """Persiste o conteúdo e retorna a storage_key opaca."""
        ...


@runtime_checkable
class ColaboradorReferenciadoPort(Protocol):
    """Porta de verificação de referência de colaborador a jusante (D-COL-3).

    Pergunta: "o colaborador está referenciado em algum módulo a jusante
    (OS, certificado, comissão) que impediria hard-delete físico?"

    Fail-open lazy (ADR-0066): quando o módulo a jusante não existe ou não
    está disponível, implementar o stub conservador que assume True.

    Implementação concreta surge quando os módulos a jusante existirem
    (agenda, OS, comissoes, certificados). Até lá, o stub bloqueia.

    Args:
      colaborador_id: UUID do colaborador a verificar.
      tenant_id:      UUID do tenant (isolamento multi-tenant ADR-0002).

    Returns:
      True se o colaborador está referenciado (bloquear hard-delete);
      False se com certeza não há referências.
    """

    def esta_referenciado(self, colaborador_id: UUID, tenant_id: UUID) -> bool: ...


class StubColaboradorReferenciadoConservador:
    """Stub conservador: SEMPRE retorna True (assume referenciado).

    Fail-safe (INV-COL-INATIVO / D-COL-3): na ausência dos módulos a jusante,
    o caminho seguro é bloquear hard-delete. Nunca retorna False por falta de dado.

    Substituto até `os`, `comissoes`, `certificados` existirem e exporem
    sua implementação concreta do Protocol. Injetado na view por padrão (Wave A).
    """

    def esta_referenciado(self, colaborador_id: UUID, tenant_id: UUID) -> bool:
        """Assume conservadoramente que o colaborador está referenciado.

        Bloqueia hard-delete até que a implementação concreta exista.
        Nunca retorna False para evitar deleção acidental de dado referenciado
        (INV-COL-INATIVO / fail-safe ADR-0066).
        """
        return True
