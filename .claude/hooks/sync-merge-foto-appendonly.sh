#!/usr/bin/env bash
# =============================================================
# sync-merge-foto-appendonly.sh — Marco 3 T-OS-106
#
# Defende INV-OS-SYNC-001 (ADR-0027 + ADR-0031) — `EvidenciaFotoAtividade`
# eh Padrao B append-only. Sync mobile e qualquer codigo de merge so pode
# INSERIR fotos (`.create(...)` / `.bulk_create(...)`), NUNCA atualizar
# nem deletar via ORM. UPDATE/DELETE em PG sao bloqueados por trigger
# `evidencia_foto_atividade_append_only_check()` (defesa em profundidade);
# este hook eh defesa em camada de aplicacao.
#
# Bloqueia (exit 2) em arquivos sob `sagas/sync_mobile.py`, `sync*.py`,
# `merge*.py` ou que importem `EvidenciaFotoAtividade`:
#
# 1. `EvidenciaFotoAtividade.objects.update(...)` / `.filter(...).update(...)`.
# 2. `EvidenciaFotoAtividade.objects.delete(...)` / `.filter(...).delete()`.
# 3. `<instancia>.save(update_fields=...)` ou `.save()` em foto ja persistida
#    (heuristica: chamada `.save(` em arquivo de sync sem `create(`).
#
# Allow (exit 0):
# - `.objects.create(...)` ou `.bulk_create(...)`.
# - Codigo em `tests/regressao/test_inv_os_sync_*` (testes que PROVAM
#   bloqueio — usam update/delete pra disparar o trigger).
# - Override: `# sync-foto: skip -- <razao>=10 chars>`.
#
# Como testar:
#   echo '{"tool_input":{"file_path":"src/infrastructure/ordens_servico/sagas/sync_mobile.py","content":"EvidenciaFotoAtividade.objects.filter(id=x).update(b2_uri=y)"}}' \
#     | bash .claude/hooks/sync-merge-foto-appendonly.sh
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

# Normaliza separadores Windows (backslash -> forward).
norm_path="${file_path//\\//}"

# So aplica em arquivos .py.
case "$norm_path" in
    *.py) ;;
    *) exit 0 ;;
esac

# Allowlist: testes de regressao do INV-OS-SYNC-001 disparam update/delete
# de proposito para provar o trigger bloqueando. Tambem migrations
# (criacao do trigger), management commands, models (entidade declarada
# la), o proprio modulo que define a classe e admin (read-only Django admin).
case "$norm_path" in
    tests/regressao/test_inv_os_sync_*|*/tests/regressao/test_inv_os_sync_*) exit 0 ;;
    *migrations/*) exit 0 ;;
    *management/*) exit 0 ;;
    *models.py) exit 0 ;;
    *admin.py) exit 0 ;;
esac

# Override explicito com razao.
if printf '%s' "$content" | grep -qE '#[[:space:]]*sync-foto:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{10,}'; then
    exit 0
fi

# Decide se o arquivo eh "sensivel a sync de foto":
#   - path indica saga/sync/merge mobile.
#   - OU codigo importa EvidenciaFotoAtividade.
sensivel=0
if printf '%s' "$norm_path" | grep -qE 'sync_mobile|/sync|/merge|sagas/sync'; then
    sensivel=1
fi
if printf '%s' "$content" | grep -qE 'import[[:space:]]+.*EvidenciaFotoAtividade|from[[:space:]]+.*import[[:space:]]+.*EvidenciaFotoAtividade|EvidenciaFotoAtividade\.objects'; then
    sensivel=1
fi
[ "$sensivel" -eq 0 ] && exit 0

# 1) update() em EvidenciaFotoAtividade.objects.
if printf '%s' "$content" | grep -qE 'EvidenciaFotoAtividade\.objects[^)]*\.update[[:space:]]*\(|EvidenciaFotoAtividade\.objects\.filter\([^)]*\)\.update[[:space:]]*\('; then
    cat >&2 <<EOF
sync-merge-foto-appendonly: UPDATE em EvidenciaFotoAtividade detectado
em $file_path (INV-OS-SYNC-001 + ADR-0027 + ADR-0031).

Foto eh Padrao B append-only. Sync mobile NUNCA atualiza foto — sempre
INSERT novo registro. Trigger PG bloqueia UPDATE de qualquer campo
diferente de 'revogado_em' (LGPD art. 18). Hook bloqueia tambem na
camada de aplicacao.

Caminho correto:
  EvidenciaFotoAtividade.objects.create(...)  # foto nova
  # OU para revogar (LGPD art. 18 face cliente):
  EvidenciaFotoAtividade.objects.filter(id=x).update(revogado_em=now)
    # ^ EXATAMENTE 1 campo: revogado_em. Outro update -> trigger raises.

Override (com razao >=10 chars):
  # sync-foto: skip -- <razao>
EOF
    # Excecao: update SOH com revogado_em eh legitimo (LGPD art. 18).
    # Checa se update so tem revogado_em.
    if printf '%s' "$content" | grep -qE 'update[[:space:]]*\([[:space:]]*revogado_em[[:space:]]*=[^,)]*\)'; then
        # Pode ser que tenha outro update ilegitimo no MESMO arquivo;
        # ja imprimiu mensagem — bloqueia mesmo assim se houver update
        # de outro campo.
        if printf '%s' "$content" | grep -qE 'EvidenciaFotoAtividade\.objects[^)]*\.update[[:space:]]*\([^)]*[a-z_]+[[:space:]]*=' | grep -vqE 'update[[:space:]]*\([[:space:]]*revogado_em[[:space:]]*='; then
            exit 2
        fi
        # Apenas update(revogado_em=...) - PASS
        exit 0
    fi
    exit 2
fi

# 2) delete() em EvidenciaFotoAtividade.objects.
if printf '%s' "$content" | grep -qE 'EvidenciaFotoAtividade\.objects[^)]*\.delete[[:space:]]*\(|EvidenciaFotoAtividade\.objects\.filter\([^)]*\)\.delete[[:space:]]*\('; then
    cat >&2 <<EOF
sync-merge-foto-appendonly: DELETE em EvidenciaFotoAtividade detectado
em $file_path (INV-OS-SYNC-001).

Foto vai pra Backblaze B2 WORM com retencao de 25 anos. DELETE eh
sempre erro de programacao — trigger PG raises. Hook bloqueia tambem
na camada de aplicacao.

Override (com razao >=10 chars):
  # sync-foto: skip -- <razao>
EOF
    exit 2
fi

# 3) .save() em foto ja persistida (heuristica conservadora).
# Bloqueia quando ha .save() E sensivel=1 E nao ha .create(.
if printf '%s' "$content" | grep -qE '\bfoto[a-zA-Z_]*\.save[[:space:]]*\('; then
    if ! printf '%s' "$content" | grep -qE 'EvidenciaFotoAtividade[^)]*\.create[[:space:]]*\('; then
        cat >&2 <<EOF
sync-merge-foto-appendonly: chamada .save() em foto sem .create()
detectada em $file_path. EvidenciaFotoAtividade eh append-only — sync
nunca chama .save() em foto ja persistida.

Override (com razao >=10 chars):
  # sync-foto: skip -- <razao>
EOF
        exit 2
    fi
fi

exit 0
