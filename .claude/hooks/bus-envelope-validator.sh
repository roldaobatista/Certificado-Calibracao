#!/usr/bin/env bash
# =============================================================
# bus-envelope-validator.sh
# Enforce INV-INT-001 (NFS-e calibracao exige certificado_id) +
#         INV-INT-009 (TenantSuspenso exige modo) +
#         envelope obrigatorio com tenant_id em todo publish.
# Evento: PreToolUse(Write|Edit) em codigo Python que publica eventos.
#
# Como funciona:
#   - Le tool_input.content / new_string + file_path
#   - Detecta chamadas publish(), publish_event(), event_bus.publish()
#   - Bloqueia (exit 2) se:
#       a) payload nao mencionar tenant_id
#       b) evento `Fiscal.NFSeEmitida` com tipo_servico="calibracao" sem certificado_id
#       c) evento `BillingSaas.TenantSuspenso` sem campo "modo"
#
# Limitacao atual (pre-codigo):
#   - Bus ainda nao existe. Hook ja vigilante para quando 1a chamada surgir.
#   - Detec\xc3\xa7\xc3\xa3o por regex (heuristica) — robusta o suficiente pra Foundation F-A.
#
# Como testar:
#   echo '{"tool_input":{"file_path":"app/services.py","content":"publish(event=\"Fiscal.NFSeEmitida\", payload={\"fatura_id\": fid, \"tipo_servico\": \"calibracao\"})"}}' | bash .claude/hooks/bus-envelope-validator.sh
#   echo $?    # esperar 2 (falta certificado_id + tenant_id)
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

# So checa codigo Python que publica eventos
case "$file_path" in
    *.py) ;;
    *) exit 0 ;;
esac

# Pula testes e migrations
case "$file_path" in
    */tests/*|*/test_*|*_test.py|*/migrations/*|*/fixtures/*) exit 0 ;;
esac

# Detecta chamada de publish
if ! printf '%s' "$content" | grep -qE '(publish_event|event_bus\.publish|outbox\.publish|publish\()'; then
    exit 0
fi

# Regra 1: payload deve ter tenant_id em algum lugar
if ! printf '%s' "$content" | grep -qE '(tenant_id|"tenant_id"|tenant=)'; then
    echo "bus-envelope-validator (envelope INV-INT): publish() sem tenant_id no payload em $file_path" >&2
    echo "Envelope obrigatorio: {event_id, tenant_id, event_name, payload, ...}" >&2
    exit 2
fi

# Regra 2: NFS-e tipo calibracao exige certificado_id (INV-INT-001)
if printf '%s' "$content" | grep -qE 'Fiscal\.NFSeEmitida|NFSeEmitida'; then
    if printf '%s' "$content" | grep -qE 'tipo_servico[[:space:]]*[=:][[:space:]]*["'\'']calibracao'; then
        if ! printf '%s' "$content" | grep -qE 'certificado_id'; then
            echo "bus-envelope-validator (INV-INT-001): NFS-e tipo calibracao sem certificado_id em $file_path" >&2
            echo "Cadeia ISO 17025 cl. 8.4 — NF-e orfa nao pode ser ligada a origem tecnica." >&2
            exit 2
        fi
    fi
fi

# Regra 3: TenantSuspenso exige modo (INV-INT-009)
if printf '%s' "$content" | grep -qE 'BillingSaas\.TenantSuspenso|TenantSuspenso'; then
    if ! printf '%s' "$content" | grep -qE '(modo[[:space:]]*[=:]|"modo")'; then
        echo "bus-envelope-validator (INV-INT-009): TenantSuspenso sem campo modo em $file_path" >&2
        echo "modo deve ser enum (read_only|bloqueado_total) — sem isso, consumers nao sabem como reagir." >&2
        exit 2
    fi
fi

exit 0
