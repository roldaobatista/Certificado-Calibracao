# ADR 0057 — Fechamento da V5 em Qualidade e governança regulatória avançada

## Status

Aceito

## Contexto

Os módulos da Qualidade e da governança regulatória já existiam como leituras canônicas úteis para orientação e auditoria, mas ainda não operavam sobre o estado persistido do sistema. Depois do fechamento de V1–V4 com auth, cadastros, fluxo operacional, portal, QR público e reemissão, a V5 precisava transformar esse conjunto em operação real de Qualidade sobre dados do tenant.

## Decisão

Adotar o fechamento conjunto de `V5.1` a `V5.5` sobre a mesma base persistida da emissão:

1. Criar tabelas próprias de V5 para NCs, trabalho não conforme, ciclos de auditoria interna, reuniões de análise crítica e perfil de compliance/regulatório da organização.
2. Manter `?scenario=` como fallback demonstrativo; sem ele, os módulos V5 respondem sobre dados reais e protegidos por sessão.
3. Derivar indicadores e o hub da Qualidade do núcleo persistido da emissão, das reemissões, das NCs, das auditorias e das reuniões, em vez de depender exclusivamente de cenários estáticos.
4. Concentrar a governança regulatória avançada em um perfil persistido da organização, incluindo perfil regulatório, escopo/CMC, parecer jurídico e governança normativa, sem mover a decisão regulatória para heurística silenciosa.
5. Restringir escrita de V5 a `admin` e `quality_manager`, mantendo leitura persistida também para papéis operacionais críticos.

## Consequências

### Positivas

- Fecha a última fatia do roadmap com Qualidade real sobre OS, certificados, reemissões e trilha crítica.
- Reduz dependência de payloads estáticos nas telas centrais da V5 e torna o hub gerencial auditável sobre operação verdadeira.
- Integra o estado regulatório avançado à leitura operacional do produto, em vez de deixá-lo apenas em documentação paralela.

### Limitações honestas

- O módulo de indicadores continua derivado do estado persistido existente e não substitui um BI histórico dedicado.
- A análise crítica permanece com entradas mínimas automáticas e decisões persistidas; calendário externo, ata binária e assinatura eletrônica da reunião seguem como evolução futura.
- A governança regulatória avançada continua apoiada no pacote normativo, no parecer jurídico e no rito de release-norm; não substitui avaliação humana em caso-limite regulatório.
