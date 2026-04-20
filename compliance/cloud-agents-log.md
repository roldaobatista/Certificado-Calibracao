# Cloud Agents Log

Registro append-only de execuções Tier 3 aprovadas.

Cada entrada deve conter: commit, branch, mecanismo de attestation, issuer OIDC, comando verificador, timestamp e veredito.

Entradas reais só podem ser adicionadas após `gh attestation verify` ou `cosign verify-blob` retornar sucesso para o commit/artefato avaliado.
