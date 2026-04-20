# 2026-04-20-baseline-v0.1.0

## Tipo

Baseline bootstrap aprovado para validação técnica do pipeline P0-2.

## Fontes

- `PRD.md#16.3`
- `iso 17025/04-templates/certificado-calibracao.md`
- `normas e portarias inmetro/portarias/portaria-157-2022.md`
- `normas e portarias inmetro/portarias/portaria-289-2021.md`
- `normas e portarias inmetro/doq-cgcre/principais-laboratorios.md`
- `normas e portarias inmetro/nit-dicla/principais-laboratorios.md`

## Escopo

- Regras bloqueantes mínimas para emissão de certificado, rastreabilidade, conteúdo de certificado, incerteza, regra de decisão, IPNA, pesos padrão, símbolo Cgcre/RBC e gravação do pacote normativo.
- Este baseline é assinado por chave Ed25519 bootstrap offline. KMS real permanece pendente até haver infraestrutura/credenciais de assinatura remota.

## Limitações honestas

- O pacote consolida as fontes versionadas neste repositório; ele não substitui consulta formal às versões oficiais vigentes antes de release regulada.
- Não há chave privada versionada. A chave pública e os metadados de assinatura são sidecars auditáveis.
