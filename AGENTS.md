# Repository guidance

Start with `docs/HANDOFF.md` and `docs/EXPERIMENTS.md`; `CLAUDE.md` applies the same factual guidance to Claude.

- Preserve original raw predictions, assessments, locked selection policies and experiment results. Put new experiments in new folders.
- Keep baseline as default unless a newly evaluated candidate passes factual-retention gates and a fair full benchmark.
- Distinguish reported results from hypotheses and future plans. SCST from the external repo has not been independently reproduced here.
- Historical spending instructions are not active authorization. This export does not authorize launching GPU jobs.
- Do not commit secrets, checkpoints, data images, environments, notebook outputs or generated archives.
- Preserve the `outputs/` sibling layout: existing scripts depend on it. Document remote-volume prerequisites instead of pretending a fresh clone is self-contained.
- Do not delegate to subagents unless the user explicitly requests it.
