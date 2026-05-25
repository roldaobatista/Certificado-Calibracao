"""Motor de calculo metrologico (P4 Fase 3 — T-CAL-046..060).

§3.3 spec M4 calibracao + ADR-0025 (validacao software cl. 7.11).

2 algoritmos independentes rodam em paralelo:
  - gum_classico (1o caminho): Decimal puro, NIT-DICLA-030 rev. 15.
  - monte_carlo (2o caminho): NumPy, JCGM 101 BIPM, seed deterministico.

validacao_replay compara os dois e classifica divergencia em 3 zonas:
  - <=0.1% silencioso
  - <=1% alerta P3
  - >1% INACEITAVEL (volta estado em_execucao + NC automatica)

arredondamento aplica NIT-DICLA-030 §7.5 (2 digitos significativos) no
resultado final antes de gravar em OrcamentoIncerteza.

Catalogo:
  - arredondamento.arredondar_2_digitos_significativos(valor)
  - gum_classico.combinar_tipo_a(s_x, n)
  - gum_classico.combinar_geral(componentes)
  - gum_classico.welch_satterthwaite(componentes_a)
  - gum_classico.fator_k_para_nivel_confianca(nivel, dof)
  - monte_carlo.simular_monte_carlo(componentes, n_iter, seed)
  - validacao_replay.comparar_algoritmos(resultado_gum, resultado_mc)
"""
