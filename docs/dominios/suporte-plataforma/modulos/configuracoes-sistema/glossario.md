---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/comum/glossario.md
---

# Glossário do módulo Configurações do Sistema

> Termos específicos do módulo de central de configurações.

---

| Termo | Definição (1 linha) | Sinônimos proibidos | Se vir na tela/log, significa | Origem |
|---|---|---|---|---|
| Configuração | Parâmetro modificável por tenant que altera comportamento do sistema | "setting" (em PT, evitar) | "ajuste que o cliente pode mudar pra mudar como o sistema se comporta" | derivado |
| Tenant | Empresa-cliente isolada (multi-tenancy) | "conta" (ambíguo) | "a empresa do cliente, separada das outras" | ADR-0002 |
| Filial | Unidade física/fiscal da empresa-cliente, com CNPJ próprio | "unidade" (subset) | "um endereço da empresa, geralmente com outro CNPJ" | `novas funcionalidades.txt:1147` |
| Série de documento | Sequência numérica isolada por tipo (OS, orçamento, fatura, certificado, NF) | — | "uma sequência de numeração separada por tipo de papel" | `novas funcionalidades.txt:1149` |
| Numeração | Formato + contador atual da série | "código" (genérico) | "o próximo número que vai sair quando emitir o documento" | `novas funcionalidades.txt:1148` |
| Papel (Role) | Conjunto de permissões aplicado a usuário(s) | "perfil" (ambíguo com "perfil do usuário") | "o cargo do usuário no sistema, que define o que ele pode fazer" | RBAC |
| Permissão | Direito específico de executar ação em recurso | "autorização" (subset) | "uma ação que o papel pode ou não fazer" | `novas funcionalidades.txt:1151` |
| Workflow | Sequência configurável de etapas + transições por entidade | "fluxo" (OK como sinônimo) | "as etapas pelas quais um item passa, na ordem que o cliente definiu" | `novas funcionalidades.txt:1152` |
| Status personalizado | Estado configurável de entidade (OS, chamado, etc.) | — | "um nome de fase que o cliente criou, fora dos padrões" | `novas funcionalidades.txt:1153` |
| Campo obrigatório | Atributo que admin marcou como exigido em mutação | "required" (em PT, evitar) | "campo que tem que ser preenchido obrigatoriamente" | `novas funcionalidades.txt:1154` |
| Modelo de PDF | Template visual usado na geração de documento | "layout" (subset) | "como o papel impresso vai ficar" | `novas funcionalidades.txt:1155` |
| Cert A3 | Certificado digital padrão ICP-Brasil em token/cartão | "certificado" (ambíguo com calibração) | "o cartão/token de assinatura digital do governo" | ADR-0009, ICP-Brasil |
| Integração | Conexão configurável com sistema externo (NF, banco, WhatsApp, SEFAZ) | "API" (subset) | "uma ponte com outro sistema" | `novas funcionalidades.txt:1157` |
| Notificação | Mensagem disparada por evento via canal (e-mail, push, SMS, WhatsApp) | "alerta" (subset) | "aviso que o sistema manda quando acontece algo" | `novas funcionalidades.txt:1158` |
| Regra comercial | Política de desconto/alçada/aprovação configurável | "policy" (em PT, evitar) | "regra de negócio configurável (desconto máximo, quem aprova)" | `novas funcionalidades.txt:1159` |
| SLA | Tempo limite de atendimento configurável por tipo | — | "prazo máximo que combinamos pra resolver" | `novas funcionalidades.txt:1160` |
| Multi-depósito | Modo do estoque com >1 depósito físico/lógico | — | "vários armazéns separados em vez de um só" | `novas funcionalidades.txt:1161` |
| Centro de custo | Unidade contábil de agrupamento de receitas/despesas | — | "categoria onde encaixa cada despesa/receita" | `novas funcionalidades.txt:1162` |
| Padrão metrológico | Equipamento usado como referência em calibração | "calibrador" (ambíguo) | "o aparelho-referência que o laboratório usa pra calibrar os outros" | ISO 17025, `novas funcionalidades.txt:1163` |
| Incerteza padrão | Valor de incerteza default usado quando não informado por equipamento | — | "margem de erro padrão que o sistema usa quando não tem outro valor" | ISO 17025 |
| Backup | Cópia de dados pra recuperação em caso de falha | — | "cópia de segurança dos dados" | `novas funcionalidades.txt:1164` |
| Retenção | Período pelo qual dados são mantidos antes de descarte | — | "quanto tempo guardamos o dado antes de apagar" | LGPD, ISO 17025, fiscal — `novas funcionalidades.txt:1165` |
| Feature flag | Liga/desliga funcionalidade liberada pro plano do tenant | "toggle" (em PT, evitar) | "chave pra ligar ou desligar uma funcionalidade" | ADR-0006 |
| Auditoria de config | Histórico imutável de mudança em configuração sensível | "log" (genérico) | "registro de quem mudou o quê e quando, nas configurações importantes" | SEC-005 |

---

## Como esta lista evolui

- Termo novo → adicionar + verificar conflito com glossário comum.
- Mudança de definição → bump CHANGELOG + aviso aos integradores.

## Convenções

- PT-BR.
- "Tenant", "Cert A3", "Workflow", "SLA", "Feature flag" mantidos em inglês (uso consagrado) com tradução de campo.
