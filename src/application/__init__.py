"""Camada de aplicacao — casos de uso (use cases).

Cada caso de uso recebe Protocols (repository, eventbus) via injecao
de dependencia. NUNCA importa de infrastructure — apenas de domain.

Exemplos futuros (Wave A):
- emitir_certificado.py
- abrir_ordem_servico.py
- assinar_documento.py
"""
