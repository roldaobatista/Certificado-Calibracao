"""Camada de aplicação da frente fiscal/NFS-e (use cases puros).

`emitir_nfse` / `cancelar_nfse` / `consultar_status_nfse`. Use cases PUROS
(ADR-0007): Input frozen + porta `FiscalProvider` + Repository Protocol injetados.
A trava metrológica por perfil roda AQUI (D-FIS-5, ADR-0073), não no DRF.
"""
