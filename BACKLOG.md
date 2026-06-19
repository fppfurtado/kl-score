## Próximos

- gaps_detected pode reportar `[[journal-date]]` (ex.: `[[2026_06_19]]`) como gap quando mencionada ≥ 2x, embora `journals/<slug>.md` exista; fix em `kl_score/metrics.py` para também checar `journals_dir/<slug>.md` (capturado por /run-plan §3.5 do Bloco 3 — qa-reviewer finding fora-do-escopo).

## Concluídos

- criar ADR-001 métricas canonical v0 thresholds (Bloco 5 do plano upstream onda-3-knowledge-layer-scoring).
- implementar Bloco 4 do plano upstream onda-3-knowledge-layer-scoring (baseline snapshot contra piloto Onda 2 — reports/baseline-2026-06-18.md).
- implementar Bloco 3 do plano upstream onda-3-knowledge-layer-scoring (tests pytest cobrindo 4 métricas + fixtures graph sintético + integration test end-to-end).
- implementar Bloco 2 do plano upstream onda-3-knowledge-layer-scoring (parser + 4 métricas v0 + CLI wire-up).
