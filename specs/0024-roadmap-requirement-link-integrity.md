# Spec 0024 — integridade do vínculo `linked_requirements` no roadmap

## Objetivo

Endurecer a fonte canônica `compliance/roadmap/v1-v5.yaml` para que o mapa `REQ -> EPIC` usado pela cascata não aceite referências soltas ou ambíguas.

## Escopo

- Validar que todo item em `linked_requirements` exista em `compliance/validation-dossier/requirements.yaml`.
- Validar que um mesmo `REQ-ID` não apareça em mais de uma fatia do roadmap.
- Falhar fechado quando `requirements.yaml` estiver ausente ou vazio ao validar a integridade do mapa.
- Atualizar a documentação do roadmap para deixar explícito que `linked_requirements` é contrato executável, não anotação livre.

## Critérios de aceite

- `roadmap-check` falha com `ROADMAP-006` quando uma fatia referencia `REQ-ID` inexistente.
- `roadmap-check` falha com `ROADMAP-006` quando um mesmo `REQ-ID` aparece em duas fatias distintas.
- Um roadmap completo continua verde quando todos os `REQ-ID`s existem e são únicos entre fatias.
- A regra usa `requirements.yaml` como fonte de verdade dos IDs aceitos.

## Fora de escopo

- Exigir cobertura total de todos os requisitos do PRD dentro do roadmap.
- Inferir automaticamente qual fatia um requisito deveria ocupar.
- Alterar a semântica do fallback da cascata além da integridade do mapa.
