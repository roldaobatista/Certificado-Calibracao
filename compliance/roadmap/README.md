# Roadmap

Fonte canônica executável do roadmap por fatias verticais V1-V5.

`harness/10-roadmap.md` explica a decisão arquitetural. `v1-v5.yaml` é o artefato validado por gate e usado como referência operacional antes de iniciar V1.

## Gate

```bash
pnpm roadmap-check
```

O gate exige ordem estrita V1-V5, dependência sequencial, release-norm, dossiê de validação, pacote normativo e gates de saída por fatia.

Cada fatia também declara:

- `epic_id`: identificador canônico do épico L0 usado pela cascata de verificação;
- `linked_requirements`: lista de REQs cuja re-auditoria pode ser agregada por esse épico.

`linked_requirements` é validado contra `compliance/validation-dossier/requirements.yaml`: cada ID precisa existir e não pode ser compartilhado por mais de uma fatia.

O bloco `coverage` torna a cobertura do roadmap explícita:

- `tracked_requirement_prefixes` define quais famílias de requisito o V1-V5 deve cobrir;
- `excluded_requirements` lista os requisitos rastreados que ficam fora das fatias por pertencerem a gates transversais.
