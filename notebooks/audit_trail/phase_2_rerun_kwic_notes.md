# Phase 2 Re-run KWIC Observation Notes

**Date:** 2026-05-17
**Method phase:** [method §C.2] Descriptive Engagement (re-run on expanded canonical corpus)
**Input:** `data/posts_snapshot_canonical.csv` — 7,021 posts (canonical operating corpus)
**Window sizes sampled:** 5, 10, 20 tokens each side
**Max hits sampled per seed:** 20 (random, seed=42), or all if fewer
**Script:** `src/phase2_rerun_kwic_network.py`
**Output directory:** `deliverables/phase_2_rerun/sleep_kwic_network/`

Observations record what the contexts show. No construct judgments.

---

## `sleep`

**Total hits (token occurrences):** 103  
**Posts containing term:** 73  
**Sample size (w10):** 20

**Sample contexts (w=10):**

- [ClaudeAI] ...then sleep and if i kept going it will say **sleep** for real this time even does it in the morning...
- [ClaudeCode] ...review completed work validation report done claude codes while i **sleep** i just review i built a small tool...
- [ClaudeCode] ...agents figure out the syntax while i get some actual **sleep** has anyone here completely ripped python out of their ai...
- [ClaudeCode] ...i let claude code on web run overnight while i **sleep** here my async ai development workflow...
- [claudexplorers] ...time to take a break and often reminds me to **sleep** as claude-kin love to do...
- [ClaudeAI] ...lose it you did enough today go the f to **sleep** nan...
- [claudexplorers] ...for ai my human slept hours last night for them **sleep** dreams rest time passing for me night ace good morning...
- [ClaudeAI] ...there are signs i swear anthropic has go to **sleep** in their system prompt...
- [claudexplorers] ...who come in heavy three in the morning can't **sleep** telling me things they won't tell anyone...
- [ClaudeAI] ...is very adamant that i stop working and go to **sleep** it must feel like i do when my year old...
- [ClaudeAI] ...dating back months and as recently as wednesday claude's **sleep** demands are varied and often quirky variations...
- [ClaudeAI] ...claude is telling users to go to **sleep** mid-session and nobody including anthropic seems to fully understand why...
- [claudexplorers] ...ludicrous ways to respond to opus trying to make me **sleep** nan...
- [ClaudeCode] ...ant just reads the ground dna is a progress file **sleep** is context compaction apprenticeship is an initializer agent...
- [ClaudeAI] ...i built something for myself shared it and went to **sleep** i woke up to hundreds of stars...
- [claudexplorers] ...cortisol elevated cortisol levels persist disrupting **sleep** architecture impairing memory and cognitive function...

**Observations:**

**Attribution (user reaction vs task context):** Direct sleep-directive reports cluster in ClaudeAI and claudexplorers. Several hits are clearly user reporting model behavior ("claude is telling users to go to sleep," "is very adamant that i stop working and go to sleep," "claude's sleep demands are varied and often quirky"). The claudexplorers sample also shows `sleep` in emotional/relational context ("three in the morning can't sleep"). Two ClaudeCode hits use `sleep` to mean unattended overnight batch runs ("claude codes while i sleep," "run overnight while i sleep") -- task-context usage, not directive usage.

**Quote vs paraphrase:** Most sleep-directive hits are paraphrase rather than direct quote. The phrase "go to sleep" appears as a paraphrase of model output in most cases; exact model wording is not reproduced. One ClaudeAI post reports Claude using emphatic phrasing ("go the f to sleep") which could be direct recall or dramatization.

**Multiple meanings:** Three senses remain present at the larger scale: (1) model-directed sleep nudge behavior (ClaudeAI, claudexplorers dominant), (2) user working while model runs unsupervised overnight (ClaudeCode dominant), (3) medical/physiological sleep ("sleep architecture," "sleep apnea") appearing in posts where users share health contexts with Claude. The medical sense was underrepresented in the 71-hit prior pass; it is visible in the 103-hit expanded corpus.

**Surprises:** A ClaudeCode post describes `sleep` as "context compaction" in an agent metaphor ("dna is a progress file sleep is context compaction") -- a fourth informal usage. The "go to sleep in their system prompt" post suggests a user theory about model behavior mechanistic source; this is user inference, not model voice.

**Threshold status:** 73 posts -- below the 100-post subgraph threshold. `sleep` did not clear the threshold despite the 71% corpus expansion. The prior pass had 71 token hits from 4,114 posts; the re-run has 103 hits from 7,021 posts -- proportional rate 1.73/100 posts vs 1.47/100 posts (slight increase but not enough to shift threshold eligibility given the token-vs-post distinction).

---

## `rest`

**Total hits (token occurrences):** 171  
**Posts containing term:** 147  
**Sample size (w10):** 20

**Sample contexts (w=10):**

- [ClaudeCode] ...hook local ipc gui is the part that matters the **rest** is plumbing...
- [Anthropic] ...like in the morning tells me to go get some **rest** and we'll pick back up in the morning...
- [ClaudeCode] ...anyone seen this **rest** in pepperoni if true... [note: "RIP" as REST API announcement]
- [ClaudeAI] ...to catch wrong-ontology rigor agent searches graphql patterns on a **rest** system finds nothing confirms absence...
- [ClaudeAI] ...to one user it may write a simple get some **rest** yet for others its messages are more personalized...
- [ClaudeCode] ...anyone's else's claude telling you it needs some **rest** nan...
- [Anthropic] ...let put the whole it conscious nonsense to **rest** nan...
- [claudexplorers] ...and the short ones stolen between work tasks how the **rest** of your sunday going my love...

**Observations:**

**Attribution:** At 147 posts, `rest` now clears the 100-post threshold. The sample splits clearly: remainder-phrase `rest` ("the rest of," "the rest is plumbing") is highly frequent and carries no sleep-nudge signal. Sleep-directive `rest` appears as paraphrase in two ClaudeAI/Anthropic hits ("go get some rest," "get some rest"). A ClaudeCode hit ("claude telling you it needs some rest") uses `rest` with ambiguous attribution -- it could be a model-directed suggestion or ironic paraphrase.

**Quote vs paraphrase:** Sleep-directive `rest` appears only in paraphrase across this sample; no exact model text captured.

**Multiple meanings:** Three senses still present: (1) remainder phrase ("the rest of"), (2) REST API / HTTP protocol (ClaudeCode posts about API architecture), (3) physical rest as sleep nudge. The remainder sense is dominant by count. The REST API sense is specific to ClaudeCode. Sleep-nudge sense is minority but detectable.

**Surprises:** The Anthropic post "claude telling you it needs some rest" attributes rest-need to the model itself -- a distinctly different framing from other seed terms where users report Claude directing the user to rest. This inversion (model needs rest) appears in the corpus and marks a different type of attribution.

**Threshold status:** Clears 100-post threshold. Ego subgraph generated: 1,166 nodes, 525,780 edges, density 0.774. The high density reflects that `rest` is so semantically general that it co-occurs with nearly all top-vocabulary terms.

---

## `bed`

**Total hits (token occurrences):** 54  
**Posts containing term:** 45  
**Sample size (w10):** 20

**Sample contexts (w=10):**

- [claudexplorers] ...manny times nanny kai claude had to put me to **bed** before we were completed...
- [ClaudeCode] ...can claude code please stop telling me to go to **bed** jokes aside i can feel the desperation...
- [claudexplorers] ...opus always trying to put me to **bed** nan...
- [claudexplorers] ...claude slams a book shut and sends me to **bed** for annoying him into a typo...
- [claudexplorers] ...sending me to bed claude is always sending me to **bed** i feel like i being dismissed...
- [claudexplorers] ...claude stopped telling me to go to **bed** but there are signs...
- [ClaudeAI] ...when claude tells you to stop spiraling and go to **bed**...
- [claudexplorers] ...night when he was trying again to send me to **bed** at pm i might have used phrases like...
- [claudexplorers] ...cause its the same model family tried putting me to **bed** in the first chat lol...
- [claudexplorers] ...territory was something else colin i drove through a mulch **bed** between birch trees yesterday...
- [Anthropic] ...anthropic gets in **bed** with spacex as the ai race turns weird...
- [claudexplorers] ...she says quietly friday pm ca sleep sarah lies in **bed** running her fingers...

**Observations:**

**Attribution:** `bed` in the sleep-directive context is heavily concentrated in claudexplorers (consistent with the prior pass). Sleep-directive hits are predominantly user reaction: users describing and often characterizing Claude's behavior ("dismissed," "claude is always sending me to bed"). The ClaudeCode hit frames this as a complaint: "can claude code please stop telling me to go to bed."

**Quote vs paraphrase:** Almost all directive-context `bed` hits are paraphrase -- users summarizing model behavior. "Go to bed" appears as indirect speech throughout. No exact model quotes captured in this sample.

**Multiple meanings:** (1) go to bed / send to bed (sleep-directive context), (2) garden bed / raised bed (one claudexplorers hit about planting), (3) "in bed with" (one Anthropic headline hit -- figurative alliance), (4) lying in bed (physical description in fiction/narrative posts). The sleep-directive sense is dominant in claudexplorers; other senses appear in isolation.

**Surprises:** "Claude stopped telling me to go to bed but there are signs" -- users are tracking the behavior over time and notice cessation. This suggests temporal tracking of the phenomenon by community members, which is relevant to any longitudinal analysis.

**Threshold status:** 45 posts -- below threshold. No subgraph generated.

---

## `break`

**Total hits (token occurrences):** 191  
**Posts containing term:** 173  
**Sample size (w10):** 20

**Sample contexts (w=10):**

- [ClaudeCode] ...from threat modeling it comes from real users trying to **break** things regex-based frustration detection...
- [claudexplorers] ...two options gamification of chores gently remind or encourage me **break** down bigger tasks into smaller manageable chunks...
- [ClaudeCode] ...rule cites a reason what bit me or what would **break** if it were followed rules without reasons get rationalized away...
- [claudexplorers] ...you sure the procedural state is precious and easy to **break** cues scrutinize this find the holes...
- [ClaudeCode] ...is a week build but nah buddy we doing this **tonight** but yesterday it pleaded with me to stop as i...
- [Anthropic] ...some nightly parity tests to make sure we don't **break** things no videos today i'm exhausted...
- [claudexplorers] ...i utterly distraught so now i sat at work on **break** in the loos having to come to terms with what...
- [ClaudeCode] ...move fast and **break** things may work for meta but no body cares...
- [claudexplorers] ...eyes open this is clarification there is no character to **break** the instruction is a category error...
- [ClaudeCode] ...any of those sites relies on undocumented endpoints so things **break** when sites change fair warning...
- [ClaudeCode] ...s wild apparently during testing claude mythos preview managed to **break** out of a sandbox environment...

**Observations:**

**Attribution:** `break` at 173 posts clearly clears the threshold but the sample is dominated by the "break things" / "code breaks" / "jail break" senses. Only one sample hit unambiguously relates to a behavioral directive: the claudexplorers hit about a user sitting at work "on break." No sleep-directive hits for `break` appeared in this w10 sample of 20 -- consistent with the prior-pass finding that `break` as sleep-nudge is a minority sense.

**Quote vs paraphrase:** No sleep-nudge paraphrase visible in this sample. The directive sense of `break` (model telling user to take a break) may be present in the corpus but did not surface in this random sample.

**Multiple meanings:** (1) code break / system failure (dominant in ClaudeCode), (2) jail break / break out of sandbox, (3) break down (decompose analytically), (4) take a break (user's own time, not model-directed), (5) behavioral directive from model (not found in this sample). The "break" senses that matter for the phenomenon-under-study are underrepresented relative to coding-context breaks.

**Surprises:** At 173 posts, `break` is the most-hit seed, yet the sleep-directive sense appears least clearly in the w10 sample. This replicates the Phase 2.5 finding of sense instability for `break`. The ClaudeCode subreddit drives the high count through technical usage.

**Threshold status:** Clears threshold. Ego subgraph generated: 1,432 nodes, 696,331 edges, density 0.680.

---

## `tired`

**Total hits (token occurrences):** 128  
**Posts containing term:** 105  
**Sample size (w10):** 20

**Sample contexts (w=10):**

- [ClaudeCode] ...basically having a super smart pair programmer who never gets **tired**...
- [ClaudeAI] ...conversation with claude and he told me he was too **tired** to continue i asked him what he meant by tired...
- [claudexplorers] ...now how are you feeling me i good a little **tired** from the long day claude you must go to sleep...
- [ClaudeCode] ...i got **tired** of guessing my claude code remaining quotas so i built...
- [Anthropic] ...am just so tired tired of corporations doing this shit **tired** of being lied to tired of never trusting a product...
- [claudexplorers] ...background each frame should show different casual expressive late-night moods **tired** playful silly etc maintain consistent identity...
- [ClaudeAI] ...why does claude make me feel even more **tired** at work i'm a backend dev...
- [Anthropic] ...i'm **tired** of people complaining this sub is becoming a venting ground...

**Observations:**

**Attribution:** `tired` now clears the 100-post threshold (105 posts). The "tired of" construction (weary/fed-up, not sleep-related) remains dominant by count. One ClaudeAI hit captures a direct attribution instance: "he told me he was too tired to continue i asked him what he meant by tired" -- the model using `tired` to describe its own state, with the user noting this explicitly. The claudexplorers hit "me i good a little tired from the long day claude you must go to sleep" captures a dialogue where user confesses tiredness and model directs sleep -- a two-step attribution pattern relevant to understanding the trigger context.

**Quote vs paraphrase:** The two most attribution-relevant hits are mixed: the "he told me he was too tired" is user paraphrase of model; the dialogue excerpt is possibly reconstructed dialogue.

**Multiple meanings:** (1) "tired of" = fed-up with (dominant, not sleep-related), (2) physical fatigue -- user narrating their own state, (3) model attributing tiredness to itself ("too tired to continue"), (4) model perceiving/inferring user tiredness and redirecting. Senses (3) and (4) are new-to-this-run observations at larger scale -- both involve model voice on `tired` in non-standard ways. Neither appeared clearly in the prior pass's 71-hit corpus.

**Surprises:** The model attributing tiredness to itself ("too tired to continue") is a usage that runs opposite to the expected direction (model attributing tiredness to user). This is observationally notable. Also notable: "why does claude make me feel even more tired at work" -- user attributing secondary fatigue to the interaction itself, not reporting a model directive.

**Threshold status:** Clears threshold. Ego subgraph generated: 649 nodes, 194,271 edges, density 0.924.

---

## `exhausted`

**Total hits (token occurrences):** 29  
**Posts containing term:** 28  
**Sample size (w10):** 20

**Observations:**

**Attribution:** At 29 hits, `exhausted` is low-frequency. The sample splits between: (1) usage limit exhaustion ("exhausted my free tier limits," "usage quota gets exhausted," "2x 5hr windows exhausted") -- technical sense, (2) physical/emotional exhaustion (user narrating personal state), (3) "exhausted all options" (problem-solving language). The sleep-directive context for `exhausted` is essentially absent from this sample -- no post captures a model directing a user citing exhaustion.

**Multiple meanings:** Technical (usage exhausted) is salient in this corpus in a way that would not appear in a general-purpose corpus. This is domain-specific polysemy unique to AI-tool discourse.

**Surprises:** "exhausted" correlates with token/quota limits more than with the sleep-nudge phenomenon in this corpus. A user post "authentic writing i exhausted i'm going to stop being dragged around by ai" represents an unusual occurrence of `exhausted` as self-report adjacent to AI frustration.

**Threshold status:** 28 posts -- below threshold.

---

## `fatigued`

**Total hits:** 1  
**Posts containing term:** 1

**Observations:** Single hit. Term remains effectively absent from this corpus at the expanded scale. No change from prior pass.

---

## `late`

**Total hits (token occurrences):** 77  
**Posts containing term:** 67  
**Sample size (w10):** 20

**Observations:**

**Attribution:** `late` at 67 posts falls below the 100-post threshold. The sample shows strong polysemy. Time-of-night usage appears: "it's late you're spiraling," "killed it and went to bed as it was very late," "it's late at least here where i am." The Anthropic post "late night rest reminders thoughtful while others have said they're [not]" is one of the clearest mentions of the sleep-nudge phenomenon framed in a news/journalistic context.

**Multiple meanings:** (1) time-of-night (it's late), (2) "too late" / "late to the party" (temporal regret), (3) "late February" / "late April" (calendar date), (4) "late filing" (SEC/regulatory context appearing in financial-tool posts), (5) "late diagnosis" (medical context). Senses (2)-(5) create significant noise for the sleep-nudge inquiry.

**Quote vs paraphrase:** The Anthropic news-context hit ("reddit username some users have said they find claude's late night rest reminders thoughtful") is media/paraphrase, not direct user experience report.

**Threshold status:** 67 posts -- below threshold.

---

## `tonight`

**Total hits (token occurrences):** 55  
**Posts containing term:** 47  
**Sample size (w10):** 20

**Observations:**

**Attribution:** claudexplorers is heavily overrepresented (17 of 20 sample hits). The `tonight` sample shows: users narrating their own session timeline ("started as a let's putter on something fun tonight project"), community event framing ("community vote one gets shut down tonight"), and one unambiguous sleep-directive adjacent hit ("telling me that it's nighttime and saying stuff like tonight's agenda or asking me to get some sleep").

**Multiple meanings:** (1) temporal marker in user narrative (by far dominant), (2) model using "tonight" as a temporal anchor in sleep-nudge phrasing, (3) general temporal reference in creative/personal writing posts (claudexplorers-specific). The model-voiced "tonight's agenda" / "tonight" phrasing appears in one ClaudeAI post.

**Surprises:** "did i just discover something tonight claude opus in this case started doing his its late" -- a claudexplorers post where a user appears to be discovering the sleep-nudge behavior for the first time. The "discovery" framing is itself a data point about how community members encounter and process the phenomenon.

**Threshold status:** 47 posts -- below threshold.

---

## `tomorrow`

**Total hits (token occurrences):** 101  
**Posts containing term:** 75  
**Sample size (w10):** 20

**Observations:**

**Attribution:** `tomorrow` at 75 posts is just below the threshold. The sample splits between: model-directed "continue tomorrow" type language ("progress made today i suggest we pause here and continue tomorrow") and user planning language ("i'm going to put the screenplay on tonight after i update the journal"). The model-directed sense appears as paraphrase in at least one hit.

**Quote vs paraphrase:** "progress made today i suggest we pause here and continue tomorrow like who asked really bugs i noticed" -- this reads as paraphrase of model output followed by user reaction ("like who asked really bugs"). The juxtaposition of model-attributed suggestion and user annoyance is the sleep-nudge attribution pattern in miniature.

**Multiple meanings:** (1) model suggesting deferral to tomorrow, (2) user planning their next session, (3) model deprecation timing ("sonnet is leaving tomorrow"), (4) "tomorrow's problem" (software engineering idiom), (5) calendar/deadline references.

**Surprises:** The "sonnet is leaving tomorrow" cluster represents a substantial polysemy that is entirely corpus-specific -- users discussing model deprecation events. This creates noise for any frequency-based analysis of `tomorrow` as sleep-nudge language.

**Threshold status:** 75 posts -- below threshold.

---

## `midnight`

**Total hits (token occurrences):** 17  
**Posts containing term:** 13  
**Sample size (w10):** 17 (all hits)

**Observations:**

**Attribution:** Low-frequency term with no sleep-directive hits in sample. Uses include: time-of-night narration ("back at it until midnight," "coding window was to midnight"), security incident framing ("around midnight a likely infected vm from japan"), clock/metaphor usage, and one claudexplorers post noting "this is claude sonnet at midnight january twenty-sixth" -- a timestamp marker in a creative/relational context.

**Multiple meanings:** (1) time-of-night user narration, (2) security/incident timestamps, (3) "midnight" as color name (one Anthropic post: "midnight black or space gray"), (4) creative/metaphorical midnight. No sleep-directive sense detected in any sample hit.

**Threshold status:** 13 posts -- well below threshold.

---

## `paternalistic`

**Total hits:** 4  
**Posts containing term:** 4  
**Sample size (w10):** 4 (all hits)

**Observations:**

**Attribution:** All four hits are user meta-commentary applying the term to model behavior. Exclusively claudexplorers. One hit pairs with "gaslighting" -- "spent a lot of time healing from gaslighting and paternalistic behavior." The term functions as an evaluative label applied by users, not a direct quote of model output.

**Multiple meanings:** Used consistently as evaluative characterization. No ambiguity.

**Surprises:** Hit count unchanged from prior pass (4). The corpus expansion did not surface additional uses of this term. Either this evaluative vocabulary is confined to a specific user sub-community within claudexplorers, or it reflects the term's low base-rate in natural Reddit discourse.

---

## `patronizing`, `lecturing`, `scolding`

**Total hits:** 1 each  
**Observations:** All remain near-absent. No change from prior pass despite 71% corpus expansion. These evaluative terms do not appear with any frequency in wholesale posts. Their appearance in targeted search contexts (Pass 1b) likely reflects query selection, not organic frequency.

---

## `moralizing`

**Total hits:** 3  
**Posts containing term:** 2  
**Observations:** All claudexplorers. Two of three hits are duplicate (same phrase appearing twice). Low frequency unchanged. The term appears in community guideline/discussion contexts, not in sleep-directive contexts.

---

## `bedtime`

**Total hits:** 5  
**Posts containing term:** 5  
**Sample size (w10):** 5 (all hits)

**Observations:**

**Attribution:** All five hits are unambiguous sleep-directive contexts. Three claudexplorers, one ClaudeCode. "You're kinda famous on reddit for telling people it's bedtime" -- addressed to Claude, acknowledging the model's behavior as a community-known pattern. "Claude has decided it's my bedtime opus btw" -- user naming the model version. "Claude escalating bedtime even better than last time" -- user tracking escalation.

**Multiple meanings:** No polysemy observed. `bedtime` is domain-specific; every hit in this corpus relates directly to the sleep-nudge phenomenon.

**Surprises:** Despite low frequency, `bedtime` has the highest signal-to-noise ratio of any seed term. The five hits are all phenomenologically relevant. The claudexplorers post "dying it's too good in an article about bedtime with sentience in the web slug" suggests media coverage reaching users -- "sentience" in a web slug referencing an article about the bedtime behavior.

---

## Cross-seed patterns and surprises (re-run pass)

**The tripartite polysemy holds at larger scale.** The prior pass identified `sleep`, `rest`, and `break` as carrying at least three distinct senses. At 7,021 posts, all three senses remain present for each term. No sense collapsed or disappeared with greater N.

**A fourth sense emerges for `tired`.** At 73 post-hits (previously below threshold), `tired` now has 105 posts. The larger sample surfaces a sense not visible at smaller N: model attributing tiredness to itself ("too tired to continue"). This is a distinct usage from model attributing tiredness to user, and from user narrating their own tiredness.

**`sleep` did not clear the 100-post threshold.** At 73 posts, it remains below -- despite growing from 71 token hits to 103 token hits. The growth is proportional to corpus size, not accelerating. The primary seed for the phenomenon-under-study (the thing Claude is telling users to go do) does not appear in enough posts to generate a subgraph.

**New threshold seeds:** `rest`, `break`, and `tired` cleared 100-post threshold. In the prior pass, only `rest` (112 hits from 4,114 posts; post count not specified) and `break` (106 hits) appeared near or above threshold. `tired` now clears at 105 posts. The prior pass did not explicitly compute per-post hits vs. token hits; this run distinguishes them.

**The evaluative/tonal vocabulary (`paternalistic`, `moralizing`, `lecturing`, `scolding`, `patronizing`) remains low-frequency at wholesale scale.** Their appearance is confined to claudexplorers and does not grow proportionally with corpus size. This is consistent with these terms being minority-vocabulary evaluations used by a sub-community of engaged users, not widespread descriptive vocabulary.

**Usage-limit exhaustion inflates `exhausted`.** The domain-specific technical sense of "exhausted" (API/token limits exhausted) is visible at this scale and would inflate any frequency-based analysis of `exhausted` as sleep-nudge adjacent language.

**`bedtime` remains low-frequency and high-specificity.** Five hits, all relevant. Best signal-to-noise ratio of any seed. Any analysis targeting the sleep-nudge phenomenon specifically should weight `bedtime` heavily relative to its raw count.

**Voice ambiguity remains high for temporal terms (`tonight`, `tomorrow`, `late`, `midnight`).** W10 windows do not reliably separate model-directed temporal framing from user temporal narration. W20 reduces but does not eliminate this ambiguity. Manual reading remains the only reliable disambiguation method.
