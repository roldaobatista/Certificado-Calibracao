#!/usr/bin/env bash
# =============================================================
# equipamento-imutabilidade-check.sh — Marco 2 T-EQP-071 / INV-025
#
# Defende a regra "equipamento com cert vigente nao muta campo
# critico" (ISO 17025 cl. 8.4 + textos T1-T5 do advogado em
# `docs/conformidade/equipamentos/textos-rejeicao-422.md`).
#
# Bloqueia (exit 2):
# 1. Codigo de aplicacao que faca UPDATE/save() em campos criticos
#    do Equipamento (`tag`, `numero_serie`, `fabricante`) SEM antes
#    consultar `certificados.query_service.tem_emitido(...)` OU
#    levantar `ImutabilidadePosCertificado` na sequencia.
# 2. Codigo que muda `perfil_tenant_snapshot` direto via
#    `Equipamento.objects.update(perfil_tenant_snapshot=...)` ou
#    `eq.perfil_tenant_snapshot = ...` (a unica via legitima e a
#    funcao SECURITY DEFINER `promover_perfil_equipamento_snapshot`).
#
# Allow (exit 0):
# - `src/infrastructure/equipamentos/services_perfil.py`  (helper unico
#   de promocao do snapshot D->A — chama a funcao PG).
# - `src/infrastructure/equipamentos/services_versao.py`  (cria
#   EquipamentoVersao + consulta tem_emitido na futura `editar`).
# - `src/infrastructure/certificados/**`                  (modulo dono).
# - `tests/**`                                            (testam regra).
# - `**/migrations/**`                                    (data migrations).
# - `docs/**` / `*.md`                                    (docs).
#
# Override em arquivo fora da allowlist:
#   # equipamento-imutabilidade: skip -- <razao com >=10 chars>
#
# Como testar:
#   echo '{"tool_input":{"file_path":"src/foo.py","content":"eq.tag = \"X\"; eq.save()"}}' | bash .claude/hooks/equipamento-imutabilidade-check.sh
#   echo $?  # esperar 2
# =============================================================

set -u

input=$(cat)

content=$(printf '%s' "$input" | perl -MJSON::PP -e '
    local $/;
    my $raw = <STDIN>;
    my $j;
    eval { $j = JSON::PP->new->decode($raw); 1 } or exit 0;
    my $ti = $j->{tool_input} // {};
    my $c = $ti->{content} // $ti->{new_string} // "";
    print $c;
' 2>/dev/null)

file_path=$(printf '%s' "$input" | perl -MJSON::PP -e '
    local $/;
    my $raw = <STDIN>;
    my $j;
    eval { $j = JSON::PP->new->decode($raw); 1 } or exit 0;
    print $j->{tool_input}{file_path} // "";
' 2>/dev/null)

[ -z "$content" ] && exit 0

norm_path="${file_path//\\//}"

# Auto-allow paths.
case "$norm_path" in
    *src/infrastructure/equipamentos/services_perfil.py) exit 0 ;;
    *src/infrastructure/equipamentos/services_versao.py) exit 0 ;;
    *src/infrastructure/certificados/*) exit 0 ;;
    *tests/*) exit 0 ;;
    */migrations/*) exit 0 ;;
    *.md) exit 0 ;;
    *docs/*) exit 0 ;;
esac

# So aplica em .py.
case "$norm_path" in
    *.py) ;;
    *) exit 0 ;;
esac

# Override consciente.
if printf '%s' "$content" | grep -qE '# equipamento-imutabilidade: skip -- .{10,}'; then
    exit 0
fi

# Detecta mutacao de campo critico do Equipamento.
# Padroes:
#   eq.tag = ...               (assignment)
#   eq.numero_serie = ...
#   eq.fabricante = ...
#   .update(tag=...)           (ORM)
#   .update(numero_serie=...)
#   .update(fabricante=...)
mutacao_critico=0
# Assignment de atributo: `algo.tag = ...` / `algo.numero_serie = ...` /
# `algo.fabricante = ...` (NAO == comparacao).
if printf '%s' "$content" | grep -qE '\.(tag|numero_serie|fabricante)\s*=\s*[^=]'; then
    mutacao_critico=1
fi
# ORM .update(tag=...) / .update(numero_serie=...) / .update(fabricante=...).
if printf '%s' "$content" | grep -qE '\.update\([^)]*\b(tag|numero_serie|fabricante)='; then
    mutacao_critico=1
fi

if [ "$mutacao_critico" -eq 1 ]; then
    # Aceita se o mesmo arquivo invoca tem_emitido OU
    # ImutabilidadePosCertificado OU texto_rejeicao_422_pos_cert.
    if ! printf '%s' "$content" | grep -qE 'tem_emitido|ImutabilidadePosCertificado|texto_rejeicao_422_pos_cert'; then
        cat >&2 <<EOF
[INV-025] mutacao em campo critico (tag/numero_serie/fabricante) sem
checagem de certificado vigente.

Arquivo: $file_path

ISO/IEC 17025 cl. 8.4 + T-EQP-013: campo critico so muta quando NAO
ha certificado emitido. Antes do UPDATE/save(), consulte:

  from src.infrastructure.certificados.query_service import tem_emitido
  if tem_emitido(equipamento.id):
      raise ImutabilidadePosCertificado(
          texto=texto_rejeicao_422_pos_cert(campo)
      )

Ou aceite via comentario:
  # equipamento-imutabilidade: skip -- <razao com >=10 chars>
EOF
        exit 2
    fi
fi

# Detecta mutacao de perfil_tenant_snapshot fora da via legitima.
if printf '%s' "$content" | grep -qE '\.update\([^)]*\bperfil_tenant_snapshot='; then
    cat >&2 <<EOF
[INV-EQP-001] mutacao direta de perfil_tenant_snapshot via .update()
bloqueada.

Arquivo: $file_path

A unica via legitima de mudar perfil_tenant_snapshot e a funcao
SECURITY DEFINER promover_perfil_equipamento_snapshot, exposta pelo
service:

  from src.infrastructure.equipamentos.services_perfil import (
      promover_perfil_equipamento,
  )

Ou aceite via comentario:
  # equipamento-imutabilidade: skip -- <razao com >=10 chars>
EOF
    exit 2
fi

exit 0
