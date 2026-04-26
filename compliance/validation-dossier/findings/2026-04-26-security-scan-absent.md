# Finding — Security scanning formal ausente no CI

## Status

Aberto.

## Contexto

O CI (`required-gates.yml`) não inclui CodeQL, Dependabot, SCA, secret scanning, container scan, SBOM ou assinatura de imagem. O pipeline é forte em gates próprios, mas fraco em supply chain padrão.

## Impacto

- Vulnerabilidades em dependências não detectadas automaticamente.
- Secrets commitados podem passar despercebidos.
- Imagens Docker sem scan antes do deploy.

## Correção recomendada

1. Habilitar GitHub Advanced Security: CodeQL, secret scanning, Dependabot alerts.
2. Adicionar workflow de SCA (ex: `npm audit`, Snyk, OWASP Dependency-Check).
3. Scan de imagem Docker no CI (Trivy, Snyk Container).
4. Gerar SBOM e assinar imagens (cosign/Sigstore).

## Rastreamento

- Área: `.github/workflows/`
