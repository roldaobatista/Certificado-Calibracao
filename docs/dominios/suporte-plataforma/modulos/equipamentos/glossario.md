---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: equipamentos
dominio: suporte-plataforma
---

# Glossário — Equipamentos do cliente

> Termos específicos deste módulo. Transversais ficam em `docs/comum/glossario.md`.

---

| Termo | Definição (1 linha) | Sinônimos proibidos | Se vir na tela/log, significa | Origem |
|---|---|---|---|---|
| Equipamento do cliente | Instrumento físico que o tenant calibra para um cliente final (ex: balança, paquímetro) | "produto", "item" | Ativo do cliente cadastrado no Aferê | OP17, INV-025 |
| TAG do equipamento | Identificador interno + único por tenant (humano-legível) | "código", "ID externo" | Etiqueta colada no instrumento | OP17 |
| QR Code do equipamento | Código 2D impresso na etiqueta que aponta para a ficha do equipamento | "código de barras" | Acesso rápido via leitor mobile | OP17 / INV-025 |
| Número de série (NS) | Identificador do fabricante, gravado no equipamento | "serial number" cru | Identificação original do fabricante | Fabricante |
| Ficha do equipamento | Visão consolidada: dados + histórico de calibração + OS abertas | "ficha técnica" só | Tela 360° do ativo | OP17 |
| Histórico imutável | Linha do tempo de eventos do equipamento após emissão de certificado | "log" | Eventos não-editáveis | INV-025 |
| Versionamento de equipamento | Registro de mudança de atributo descritivo após emissão (cria nova versão, preserva antiga) | "edição direta" | Snapshot antigo permanece no certificado | INV-025 |
| Vínculo cliente-equipamento | Relação entre equipamento e cliente final (transferência exige aceite) | "dono", "owner" | Quem é o titular do equipamento | OP17 |
| Status do equipamento | Estado operacional: ativo / inativo / sucata / em calibração | "situação" | Filtro de listagem | OP17 |

---

## Como esta lista evolui

- Termo novo → adicionar + verificar conflito com glossário comum.
- Termo descontinuado → marcar `@deprecated` + janela 3 meses.
