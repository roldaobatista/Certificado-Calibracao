"""Tasks Procrastinate de auditoria — export pra Backblaze B2 (WORM).

Marco 4 entrega STUB. Destino real (B2) entra apenas quando Roldao
autorizar deploy (memoria project_deploy_so_quando_roldao_quiser).
Por agora, escreve em /tmp/audit-export-YYYY-MM-DD-HH.jsonl localmente.

Quando deploy autorizado:
- Trocar `_destino_local()` por adapter `B2Storage`
- Adicionar `correlation_id` no envelope (INV-INT-009 — bus envelope validator)
- Configurar retencao WORM no bucket B2 (immutability 25 anos — ISO 17025 8.4)
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


def _destino_local(janela_inicio: datetime) -> Path:
    """Arquivo JSONL por hora. Apenas stub local — substituir por B2 em deploy."""
    nome = janela_inicio.strftime("audit-export-%Y-%m-%d-%H.jsonl")
    return Path("/tmp") / nome


def exportar_janela_horaria(janela_inicio: datetime | None = None) -> int:
    """Exporta todas as linhas da auditoria criadas na ultima janela horaria.

    Marco F-B vai conectar isto a um cron Procrastinate. Por agora a funcao
    e chamavel manualmente em `python manage.py shell_plus`.

    Returns: numero de linhas exportadas.
    """
    # Import tardio — Django apps loading
    from .models import Auditoria

    if janela_inicio is None:
        agora = datetime.now(timezone.utc)
        janela_inicio = agora.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)
    janela_fim = janela_inicio + timedelta(hours=1)

    destino = _destino_local(janela_inicio)
    destino.parent.mkdir(parents=True, exist_ok=True)

    linhas = Auditoria.objects.filter(
        timestamp__gte=janela_inicio,
        timestamp__lt=janela_fim,
    ).order_by("timestamp")

    total = 0
    with destino.open("w", encoding="utf-8") as fp:
        for linha in linhas.iterator(chunk_size=500):
            envelope = {
                "audit_id": str(linha.id),
                "tenant_id": str(linha.tenant_id) if linha.tenant_id else None,
                "usuario_id": str(linha.usuario_id) if linha.usuario_id else None,
                "action": linha.action,
                "resource_summary": linha.resource_summary,
                "payload": linha.payload_jsonb,
                "hash_anterior": linha.hash_anterior,
                "hash_atual": linha.hash_atual,
                "timestamp": linha.timestamp.isoformat(),
            }
            fp.write(json.dumps(envelope, ensure_ascii=False) + "\n")
            total += 1

    logger.info("audit.export: %s linhas -> %s", total, destino)
    return total
