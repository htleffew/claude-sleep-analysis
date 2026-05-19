# Phase 3 — Unit-of-Analysis Decision Record (Sleep-Nudge Project)

**Date of record:** 2026-05-17
**Method version:** `community_reported_llm_behavior_method.md` v1.0 (with 2026-05-17 §C.1 retrieval-mode addendum)
**Phase:** [method §C.3] Unit-of-Analysis Determination

---

## Decision

**Primary unit:** post and comment as **two stratified analytical units**.
**Secondary unit:** post + its comment subtree (when comment-tree structure is exploited in Phase 4 or later).

Phase 5 theme discovery, Phase 6 dictionary construction, and Phase 8 inferential work all stratify on the `type` column. Constructs may differ between posts and comments; if they converge, the convergence is itself a finding. If they diverge, the divergence is a finding.

## Empirical justification

The Pass 1b Phase 2 KWIC/co-occurrence/network analysis (`deliverables/phase_2_pass1b/sleep_kwic_network/`) and the corresponding summary (`phase_2_pass1b_kwic_network_summary.md`) produced direct evidence that posts and comments are structurally different in this corpus:

| Network | Nodes | Edges | Density |
|---|---|---|---|
| Post-only co-occurrence | 1,500 | 237,838 | **0.212** |
| Comment-only co-occurrence | 491 | 2,322 | **0.019** |

An 11× density gap. The two networks describe different linguistic worlds: posts are longer narrative accounts (top-20 degree nodes skew broader: *code, real, tool, answer*), comments are short reactive utterances (top-20 degree nodes skew on-topic: *bed, sleep, session, take, break, telling*).

Convergent evidence from Pass 1b Phase 2 freq:
- In the comments stratum, `bed` is rank #2 content term and `sleep` is rank #3, above `code` and `model`.
- In the posts stratum, `bed` ranks below #13 and `sleep` similarly.
- Comments concentrate directive-attribution grammar (*telling bed, told bed, sent me to bed*); posts spread across broader framing.

Reading: **posts narrate the phenomenon; comments react to it.** Two different evidentiary kinds of testimony.

## Implications

1. **Phase 5 theme discovery** runs separately on post-only and comment-only sub-corpora. Themes may match, partially overlap, or diverge. The comparison is structural evidence about how the phenomenon is described vs. how it is reacted to.

2. **Phase 6 dictionary construction** may produce separate dictionaries for narrative descriptions (posts) and reactive responses (comments), or a shared dictionary with stratified precision-at-N. Decision deferred to Phase 6 work; the structural justification for stratification is established.

3. **Phase 7 construct formation** may need to articulate the post–comment relationship as itself a finding. Candidate framing: *"The phenomenon is described in narrative posts and reacted to in comments; the lexical and grammatical surface differs systematically between the two."* This is not a pre-imposed construct; it is empirically grounded.

4. **Phase 8 inferential work** stratifies. Any frequency, PMI, or regression analysis reports separately for posts and comments unless the analysis explicitly justifies merging.

5. **Phase 4 voice segmentation** (next) must respect the stratification: segmentation heuristics may behave differently in narrative posts (where users may quote model utterances inline or describe them in third person) versus in reactive comments (which are typically not direct quotes of the model).

## Cross-reference

- Pass 1b canonical corpus: `data/pass1b_canonical.csv` (773 rows: 242 posts, 531 comments).
- Phase 2 KWIC network summary: `notebooks/audit_trail/phase_2_pass1b_kwic_network_summary.md`.
- Phase 2 freq summary: `notebooks/audit_trail/phase_2_pass1b_freq_summary.md`.
- Procedural method §C.3 requirements satisfied: primary and secondary units empirically determined, with documented rationale tied to specific Phase 2 evidence.
