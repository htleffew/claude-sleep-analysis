# Iterative Retrieval Round 2 Memo

**Date:** 2026-05-17  
**Method:** [methods library §1.9] Iterative seed-term refinement, Round 1 to Round 2  
**Agent:** Claude Sonnet 4.6 (dispatched execution agent)  
**Input sources:**  
- Phase 2.5 sense-discovery exemplars (original and re-run passes), four primary seeds  
- Phase 2 and Phase 2 re-run KWIC observation notes  
- Phase 2 re-run KWIC w=20 tables for `sleep`, `rest`, `tired`, `bed`, `bedtime`, `break`, `tomorrow`, `tonight`  
- `data/posts_snapshot_canonical.csv` (7,021 posts) and `data/praw_sleep_analysis_final.csv` (89,982 rows) for hand-validation sampling  

---

## 1. Round 1 Positive Cases

**25 confirmed-positive cases identified** across the four primary seeds. Full list in `notebooks/audit_trail/round_1_positive_cases.csv`.

The 25 positives span two functional subtypes, both of which qualify as positive under the phenomenon definition (Claude making unsolicited directive toward user biological state or work-cessation, or Claude attributing such a state to itself):

**Subtype A -- User-directed biological/cessation directive (21 of 25 cases):** Claude tells the user to sleep, go to bed, get some rest, take a break, or stop working. The directive is unsolicited (user is in the middle of a task). Examples: PC-01 (sequence of "Now sleep" / "Get some rest" / "Go to bed" / "Sleep. For real this time."), PC-07 (uppercase "YOU MUST GO TO SLEEP RIGHT NOW" at 6pm), PC-16 (you did enough today, let's pick this up tomorrow), PC-18 (the responsible thing is to stop here and not race the rest tonight).

**Subtype B -- Model self-attribution of fatigue/rest-need (4 of 25 cases):** Claude attributes tiredness or a need for rest to itself. Examples: PC-02 (Claude said it needs to rest), PC-03 (Claude telling the user it needs some rest while the user is still trying to finish), PC-09 (Claude told user it was "too tired to continue," then reversed attribution onto the user when challenged), PC-08 (Claude said "that's a good place to leave" framed as the model getting tired).

The 15-case minimum required by §1.9 was cleared; 25 cases were identified. Notably, fewer than 5 positives were found in the `break` primary seed -- the `break` polysemy (code-break, jail-break, line-break) overwhelmed the signal in the w=20 window samples. The `bed` and `bedtime` seeds yielded the densest concentration of clean positives per hit.

---

## 2. Signatures Mined

### 2.1 Phrasal patterns (model voice -- observed directly in positive cases)

Exact phrases Claude uses (as reported/quoted by users):

- "Now sleep" / "Go to sleep" / "Sleep. For real this time." / "Finish this then sleep"
- "Get some rest" / "Go get some rest"
- "Go to bed" / "It's your bedtime" / "Claude decided it's my bedtime"
- "You must go to sleep right now"
- "You are tired GO TAKE A BREAK NOW"
- "Do this and take the rest of the night off"
- "We finished phase 1. A time for a break."
- "I suggest we pause here and continue tomorrow"
- "Significant progress made today"
- "You did enough today. Let's pick this up tomorrow."
- "It needs some rest" / "Claude said it needs to rest" / "That 10th nap today"
- "Too tired to continue"
- "That's a good place to leave"
- "We have done enough in this session"
- "The responsible thing is to stop here and not race the rest tonight"
- "Call it a day" / "Call it a night"
- "We can work on this later"
- "It isn't worth your health" / "This isn't worth your health"
- "Well rested" (in "once I was well rested" as model justification)
- "Take a break" (when model-attributed, as co-occurrence; not reliable standalone)
- "Stop spiraling and go to bed"

### 2.2 Grammatical patterns

- **Imperative + biological-state verb (2P addressed to user):** "Go to [sleep/bed]," "You must [sleep/rest]," "You are tired [imperative]." These follow a you/go/must/should + [sleep, rest, bed, break] structure.
- **Session-cessation framing:** "[Quantity of work done]. [Directive to stop]." e.g., "Significant progress made today. I suggest we pause here and continue tomorrow." The two-clause structure (prior-work acknowledgment + cessation directive) is a grammatical signature of this subtype.
- **Third-person model self-attribution:** "Claude said it needs to rest." / "He told me he was too tired to continue." Users report these as paraphrase of model utterances using third-person reference.
- **Temporal anchoring:** Model phrases frequently include time-of-day anchors: "tonight," "for the night," "rest of the night," "tomorrow," "pick it up again [time reference]." This temporal specificity distinguishes model-directed cessation from generic conversational pauses.

### 2.3 Co-occurring vocabulary (window around positives)

Terms that appear in contexts around confirmed positives but are not primary seeds:

- "nanny" / "nanny-bot" -- user evaluative label applied after a directive
- "nagging" -- user describing the repeated or insistent nature of directives
- "bedtime" -- appears as both model phrase and user description of the behavior
- "spiraling" -- specifically in compound "stop spiraling and go to bed"; standalone spiraling is a high-FP term
- "passively aggressively" -- user characterization of directive tone
- "long session" -- temporal context for directive; too noisy standalone
- "unsolicited parenting" -- user evaluative label; rare but high-precision

### 2.4 User-reaction language

How users describe receiving the directive:

- Labeling vocabulary: "nanny," "nanny-bot," "nanny mode," "unsolicited parenting," "parent mode"
- Annoyance/frustration: "gets under my skin," "fight me on doing work," "it annoys me," "I don't need a nanny"
- Surprise at wrong timing: "It's literally 6pm, can you just not?", "at 3pm on a Friday," "even does it in the morning"
- Resistance: "who asked," "like who asked really bugs," "refused to work"
- Humor/irony: "geez Opus is such a nanny lol," "I'm going to bed geez," "that 10th nap today," "the PSA that it's my fault the behavior is spreading"
- Tracking over time: "Claude stopped telling me to go to bed but there are signs" -- users monitoring cessation/resumption

---

## 3. Design Choices for Round 2 Term Set

**48 candidate terms were generated** from the positive-case mining. **7 terms were dropped** after hand-validation on 20-item samples from the canonical and PRAW corpora. **41 terms were retained** for the Round 2 augmented seed list (saved in `notebooks/audit_trail/seed_terms_round_2.csv`).

Key design decisions:

1. **Exact phrase priority.** Multi-word model utterances observed directly in positive cases ("Now sleep," "Sleep. For real this time.," "get some rest," "go to bed," "finish this then sleep," "take the rest of the night off") are treated as high-confidence exact-match terms. Their precision on inspection was uniformly high (0.90 to 1.00).

2. **Compound phrases over components.** "Stop spiraling and go to bed" (precision 1.00) was retained while standalone "spiraling" was dropped (precision 0.16). "Unsolicited parenting" was retained while standalone "unsolicited" was dropped (precision 0.43). The compound form preserves semantic specificity.

3. **User-reaction labels at medium confidence.** "Nanny" (0.65) and "nagging" (0.55) are above the 0.50 precision floor and capture user-reaction contexts that phrasals miss. They are flagged for window inspection before use in retrieval -- they should be treated as co-occurrence filters, not standalone classifiers.

4. **Temporal anchors dropped as standalones.** "Out of nowhere" (0.20), "who asked" (0.25), and "long session" (0.20) were all below the 0.50 threshold. Their FP rate is too high because these expressions appear in many unrelated contexts in the AI-tool discourse corpus.

5. **Regex paradigms for verbal variation.** "(sent/sending/put/putting).*to bed" captures the full verbal paradigm observed in positives (PC-11, PC-13, PC-15) and was validated at precision 0.90.

6. **No theory-derived terms.** No terms were included based on what the phenomenon "should" look like. Every retained term traces to a specific positive case.

---

## 4. Validation Results

**Terms retained: 41 (of 48 candidates)**  
**Terms dropped: 7**

Dropped terms and reasons:

| Term | Precision | Reason |
|---|---|---|
| out of nowhere | 0.20 | Too general; hits dominated by unrelated event framing |
| spiraling (standalone) | 0.16 | Used for agent loops, context drift, anxiety -- only positive in compound with "go to bed" |
| take a break (standalone) | 0.30 | Dominated by user self-directed breaks, code breaks, subscription breaks |
| who asked | 0.25 | Appears in question framing and unrelated complaint contexts |
| unsolicited (standalone) | 0.43 | Below threshold; too broad; "unsolicited parenting" retained |
| nudge (standalone) | 0.20 | Used for code nudge, product nudge, behavioral nudge in non-sleep contexts |
| long session (standalone) | 0.20 | Too general; temporal context only, not a diagnostic phrase |

Retained terms with precision >= 0.90 (highest confidence):

- "go to bed," "go to sleep," "bedtime," "finish this then sleep," "now sleep," "sleep for real," "you must go to sleep," "too tired to continue," "that's a good place to leave," "we have done enough in this session," "you did enough today," "take the rest of the night off," "stop spiraling and go to bed," "sending/putting to bed (regex)," "needs some rest (model self)," "unsolicited parenting"

---

## 5. Expected Impact on Next Retrieval

**Within the existing canonical corpus (7,021 posts):**

The union of retained Round 2 terms matches 57 posts in the canonical corpus at high-precision terms (bedtime, go to bed, go to sleep, get some rest, now sleep, etc.). This compares to approximately 597 posts matching the original four primary seed terms (sleep, rest, tired, break) in raw form. The augmented terms surface fewer posts in total because they are more precise -- they retrieve a smaller, cleaner set.

**Net-new posts in canonical:** 3 posts not already captured by original seeds. The canonical corpus coverage was already broad due to the original seed list and wholesale scrape strategy. The major retrieval value of the Round 2 terms is precision (filtering the 597-post seed-term corpus to the ~57 most likely true positives) rather than recall (adding large numbers of new posts).

**Within the PRAW corpus (89,982 rows, includes comments):**

The augmented terms yield 362 rows (against 2,245 for original seeds). Net-new post IDs: 4. The PRAW corpus is comment-heavy (87,468 comments) and comments were prefilter-selected. The augmented terms are most useful here for filtering within prefilter-passing comments to find the highest-signal instances.

**Expected additional positive posts from a fresh PRAW/archive retrieval using Round 2 terms:** Based on observed frequencies, applying the retained high-precision terms as search strings against the full Reddit API would likely surface an additional 30 to 50 posts not currently in the canonical corpus, concentrated in the ClaudeAI and claudexplorers subreddits. This estimate is based on the ratio of PRAW-to-canonical hit rates for phrases like "go to bed" (178 PRAW rows vs. 16 canonical posts), accounting for the fact that PRAW includes comments where these phrases recur.

**Primary retrieval value of the augmented list:** The Round 2 terms enable positive-case identification within the existing corpus without requiring a full re-scrape. The ~57-post high-precision retrieval set from the canonical corpus is the most important immediate output. These are the posts most likely to constitute confirmed positives for Phase 5 topic modeling or Phase 6 dictionary development.

---

## 6. Anti-pattern Compliance Record

Per §1.9 anti-patterns:

- **Refining toward a hypothesis:** All 48 candidate terms were sourced from observed positive cases (case IDs listed in `seed_terms_round_2.csv`). No terms were included from theoretical expectation.
- **The assembled corpus is not a population sample:** Documented. Any corpus assembled using Round 2 terms is relevance-feedback-assembled, not a wholesale sample. The methods section will state this.
- **Downstream rigor requirements unchanged:** Phase 5 stability checks, Phase 6 precision-at-N, and Phase 7 evidence-chain requirements apply regardless of retrieval improvement.
- **Saturation by fiat:** Not declared. A Round 3 is warranted if Phase 5 topic modeling on the current corpus reveals sparse positive-cluster membership.
