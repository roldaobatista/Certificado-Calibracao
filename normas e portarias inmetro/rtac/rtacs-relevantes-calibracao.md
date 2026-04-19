# RTACs relevantes para Laboratórios de Calibração

> Os **RTACs** se aplicam principalmente a **produtos** sujeitos à avaliação da conformidade. Para laboratórios de calibração, são relevantes principalmente quando o laboratório:
> 1. Calibra instrumentos usados em **ensaios obrigatórios** definidos por RTAC.
> 2. Faz parte de um **OAC** (Organismo de Avaliação da Conformidade).
> 3. Atende clientes em setores regulamentados que precisam apresentar resultados rastreáveis para fins de certificação.

> **Verificar vigência sempre nos portais oficiais** — RTACs são frequentemente revisados.

## RTAC para serviços (não produtos)

| RTAC / Portaria | Tema |
|-----------------|------|
| Portaria Inmetro nº 590/2013 | Aprova RTAC para o serviço de calibração de instrumentos de medição |

Este é o **RTAC mais diretamente relacionado a laboratórios de calibração** — define requisitos para a prestação do serviço de calibração no âmbito do Sinmetro.

## RTACs por setor (relevância indireta para labs de calibração)

### Equipamentos médicos
- RTACs sobre equipamentos eletromédicos — quando o laboratório calibra equipamentos médicos para hospitais, os ensaios em campo precisam de calibrações rastreáveis.

### EPIs
- Capacetes, óculos, calçados de segurança — exigem ensaios mecânicos com instrumentos calibrados (células de carga, dinamômetros).

### Veicular
- **Pneus, vidros, capacetes motociclistas, GNV, cintos de segurança** — RTACs frequentemente exigem ensaios físicos com rastreabilidade demonstrada.
- **Cronotacógrafos:** instrumento sujeito a metrologia legal e a verificação periódica.

### Construção civil
- **Cimento, blocos, aço CA-50:** ensaios mecânicos e químicos com instrumentos calibrados (prensas, balanças, paquímetros, micrômetros).

### Eletroeletrônicos
- **Plugues e tomadas, fios e cabos, transformadores, brinquedos:** ensaios elétricos exigem instrumentos calibrados (multímetros, fontes, padrões de tensão/corrente).

### Eficiência energética (PBE)
- **Eletrodomésticos** — ensaios de consumo/eficiência exigem instrumentos calibrados de potência, energia, temperatura, vazão.

### Recipientes a pressão
- **Botijões GLP, extintores:** ensaios hidrostáticos exigem manômetros calibrados.

### Brinquedos
- Ensaios físicos com rastreabilidade dimensional, força, etc.

## Relação entre RTAC e laboratório de calibração

```
   Fabricante  ──────►  Produto                  RTAC define requisitos
                          │
                          ▼
                  Ensaio em laboratório  ◄─────  Lab de ensaio acreditado
                          │                        ISO/IEC 17025
                          ▼
                  Instrumentos                 ◄── Lab de CALIBRAÇÃO
                  do laboratório de ensaio        (ISO/IEC 17025)
                  precisam ser calibrados
                  com rastreabilidade
                          │
                          ▼
                  Padrões (laboratório
                  de calibração / INMs)       ◄── Cgcre / BIPM
```

## Onde consultar a lista completa de RTACs vigentes

- **Inmetro — Avaliação da Conformidade:** https://www.gov.br/inmetro/pt-br/assuntos/avaliacao-da-conformidade
- **Lista de produtos regulamentados:** disponível no mesmo portal, atualizada regularmente.

## Como anexar um RTAC nesta pasta
1. Identificar a Portaria que aprovou o RTAC.
2. Baixar o PDF do anexo (texto do RTAC).
3. Salvar como `rtac-<tema>-portaria-<num>-<ano>.pdf`.
4. Criar ficha resumo `rtac-<tema>.md` com:
   - Portaria de aprovação + data DOU
   - Objeto e campo de aplicação
   - Mecanismo de avaliação (certificação/declaração/etiquetagem)
   - Requisitos de ensaio relevantes
   - Periodicidade de manutenção da conformidade
   - Vigência atual
