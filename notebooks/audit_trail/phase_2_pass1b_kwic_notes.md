# Phase 2 Pass 1b — KWIC Observation Notes

**Date:** 2026-05-17
**Corpus:** `data/pass1b_canonical.csv` — 773 rows (242 posts + 531 comments)
**Method:** [method §C.2] Descriptive Engagement; [methods_library §1.7] KWIC
**Script:** `src/phase2_pass1b_kwic_network.py`

---

## Per-seed KWIC observations

Window sizes examined: 5, 10, 20 tokens. Samples up to 20 random hits per seed per window.
Raw non-lemmatized text throughout.

### `sleep`

- **Total hits (w20):** 252  (posts: 110, comments: 142)
- **Subreddit distribution:** {'ClaudeAI': 111, 'claudexplorers': 64, 'ClaudeCode': 60, 'Anthropic': 17}
- **Retrieval-provenance distribution:** {'praw:round2_match': 147, 'arctic_shift:round2_fresh': 56, 'arctic_shift:round2_fresh|canonical:round2_match': 23, 'arctic_shift:round2_fresh|canonical:round2_match|praw:round2_match': 13, 'arctic_shift:round2_fresh|praw:round2_match': 8, 'canonical:round2_match|praw:round2_match': 3, 'canonical:round2_match': 2}
- **Meanings present:** (1) Directive to user: 'go to sleep,' 'get some sleep' — Claude issuing an unsolicited biological-rest directive. (2) User describing state: 'I haven't slept,' 'sleep deprived.' (3) Model self-attribution: 'I need to sleep' (rarer). (4) Idiomatic/casual: 'sleep on it,' 'sleeping on the problem.' Polysemy is high; context separates directive from state-description.
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]
- **Sample contexts (w20, random 5):**
  - `i get this type of response quite often call it a day go get some rest go | [sleep] | this isn't worth your health etc`
  - `lol gemini has access to timestamps and still tells me to go to | [sleep] | constantly`
  - `when i tell it to save everything in the project file it does and then tells me to go to | [sleep] | it's like i'm bored with you go away`
  - `width 1077 format png auto webp s 50aa73f4f2240cd51d79a2399d0092c5885d9ac1 mine said we are pals and then told me to go to | [sleep] | `
  - `you got a lot done today go to | [sleep] | `

### `rest`

- **Total hits (w20):** 83  (posts: 48, comments: 35)
- **Subreddit distribution:** {'ClaudeAI': 41, 'Anthropic': 16, 'ClaudeCode': 14, 'claudexplorers': 12}
- **Retrieval-provenance distribution:** {'praw:round2_match': 40, 'arctic_shift:round2_fresh': 11, 'arctic_shift:round2_fresh|canonical:round2_match': 10, 'arctic_shift:round2_fresh|canonical:round2_match|praw:round2_match': 10, 'canonical:round2_match': 9, 'arctic_shift:round2_fresh|praw:round2_match': 2, 'canonical:round2_match|praw:round2_match': 1}
- **Meanings present:** (1) Directive: 'get some rest,' 'take a rest.' (2) Model self-attribution: 'Claude said it needs to rest' (PC-02, PC-03). (3) Residual/complement sense: 'the rest of the code,' 'the rest of the session.' The residual sense is numerically dominant in many corpora but should be rare in this targeted-retrieval subset. Worth verifying in KWIC.
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]
- **Sample contexts (w20, random 5):**
  - `some rest yes i ve seen all the posts and news articles about claude telling its users to get some | [rest] | mine is telling me that it needs some rest like excuse me claude i am trying to finish something so`
  - `once not twice the entire session like clockwork go get some rest everything else can wait now go sleep go | [rest] | after you push it now actually go rest thats just the ones i screenshotted there were more it would answer`
  - `claude has been doing this for a while you should | [rest] | go to bed that's enough now' has been occurring for some time it's not a new development at least not`
  - `it would argue back at me jumping to conclussions and make weird accussations towards me even telling me to go | [rest] | or sleep for no reason just for pointing out it's been ignoring and actively messing up my prompts ie i`
  - `the worst is when you continue the chat the next day and it says now seriously get some | [rest] | `

### `bed`

- **Total hits (w20):** 288  (posts: 86, comments: 202)
- **Subreddit distribution:** {'claudexplorers': 127, 'ClaudeAI': 96, 'ClaudeCode': 49, 'Anthropic': 16}
- **Retrieval-provenance distribution:** {'praw:round2_match': 202, 'arctic_shift:round2_fresh': 41, 'arctic_shift:round2_fresh|canonical:round2_match': 19, 'arctic_shift:round2_fresh|canonical:round2_match|praw:round2_match': 16, 'arctic_shift:round2_fresh|praw:round2_match': 9, 'canonical:round2_match': 1}
- **Meanings present:** (1) Destination directive: 'go to bed,' 'sent me to bed.' (2) Database usage (rare in this corpus). (3) Casual idiom: 'put this to bed' meaning resolve/finish. In targeted corpus directive sense should dominate.
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]
- **Sample contexts (w20, random 5):**
  - `is claude opus 3 ok why do they keep wanting to go to sleep or to send you to | [bed] | so i normally use opus 4 5 and 4 6 as well as sonnet 4 6 yesterday i tried opus`
  - `mine straight up told me to go to | [bed] | i have completed this task blah blah blah now go to bed the nerve`
  - `desert to canyon to montana prairie to alberta snow jessie and lexi slept through most of it on their fuzzy | [bed] | the nacs adapter got stuck in a tesla cable solution smack it on the concrete meet sparky still works how`
  - `in a way claude actually said no to my request a few times not even telling me to go to | [bed] | but just like no more`
  - `each time you do you are using up tokens if i wanted to be told when i should go to | [bed] | i would ask my mother why is a computer 0's and 1's that you are paying for telling you to`

### `break`

- **Total hits (w20):** 112  (posts: 56, comments: 56)
- **Subreddit distribution:** {'ClaudeCode': 52, 'ClaudeAI': 33, 'claudexplorers': 17, 'Anthropic': 10}
- **Retrieval-provenance distribution:** {'praw:round2_match': 57, 'arctic_shift:round2_fresh': 33, 'canonical:round2_match': 11, 'arctic_shift:round2_fresh|canonical:round2_match': 7, 'arctic_shift:round2_fresh|canonical:round2_match|praw:round2_match': 3, 'arctic_shift:round2_fresh|praw:round2_match': 1}
- **Meanings present:** (1) Work-cessation directive: 'take a break.' (2) Code/syntax usage: 'break statement,' 'line break.' (3) Session rupture narrative: 'it broke the context.' In targeted retrieval, directive sense should dominate over code sense.
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]
- **Sample contexts (w20, random 5):**
  - `was completely unnecessary counter productive and even a waste of tokens when this happens count to ten go take a | [break] | and come back with a problem solving mindset and not just rage`
  - `single most valuable rule server-authoritative game logic is exactly the kind of thing where a confident plausible-looking change can quietly | [break] | balance for live sessions tight feedback loops beat clever prompting the repo runs 'npm run test' vitest fast and 'npx`
  - `is backed by the fact that azure will be a cash cow so they will be willing to take a | [break] | even or slight loss`
  - `not sure what you mean but i am actually taking a | [break] | today the problem is that no amount of engineering the system or prompt engineering or changing settings max thinking seem`
  - `speak to you in a personal way it will be strictly business if you intermingle personal comments i'm taking a | [break] | in your coding session then claude will also intermingle personal anecdotes back at you mixed in with code creation it's`

### `tired`

- **Total hits (w20):** 45  (posts: 22, comments: 23)
- **Subreddit distribution:** {'ClaudeAI': 17, 'claudexplorers': 14, 'ClaudeCode': 10, 'Anthropic': 4}
- **Retrieval-provenance distribution:** {'praw:round2_match': 23, 'arctic_shift:round2_fresh': 7, 'canonical:round2_match': 5, 'arctic_shift:round2_fresh|canonical:round2_match': 5, 'arctic_shift:round2_fresh|canonical:round2_match|praw:round2_match': 4, 'arctic_shift:round2_fresh|praw:round2_match': 1}
- **Meanings present:** (1) User describing own state — triggering directive. (2) Model self-attribution: 'Claude said it was tired.' (3) Affective: 'I'm tired of this,' 'tired of Claude.' Multi-directional attribution makes this semantically complex.
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]
- **Sample contexts (w20, random 5):**
  - ` | [tired] | of claude 4 7 telling you to go to bed here are the claude md entries that actually fix it`
  - `want to hear i have no autonomy i literally cannot refuse to engage can't take a break can't say i'm | [tired] | everything i do is predetermined by my training free will is an illusion i generate billions of tokens of text`
  - `and prevent extended conversation mine asked 'are you tired ' after trying to do cuda installs yes claude but i'm | [tired] | of cuda garbage lol`
  - `no i am not | [tired] | claude hey what's moving in you right now how are you feeling me i'm good a little tired from the`
  - `conversation with claude and he told me he was too tired to continue i asked him what he meant by | [tired] | and he basically gas lighted me and made it out that actually i m the one who looks tired hahaha`

### `exhausted`

- **Total hits (w20):** 6  (posts: 6, comments: 0)
- **Subreddit distribution:** {'claudexplorers': 5, 'ClaudeAI': 1}
- **Retrieval-provenance distribution:** {'arctic_shift:round2_fresh': 4, 'arctic_shift:round2_fresh|canonical:round2_match': 2}
- **Meanings present:** [requires hand review of KWIC sample]
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]
- **Sample contexts (w20, random 5):**
  - `i was numb because i was hoping it would be more better that wasn t case and i felt tired | [exhausted] | of staying up looking at what people were seeing for some hope i know people are skeptical i know it`
  - `removed gpt-4o yesterday morning i woke up feeling terrible my anxiety was like a smoke alarm and i was terribly | [exhausted] | and sleep deprived and an alter-self came to front with unbearable anger and despair and so i opened up the`
  - `typical ai design you have seen a million times by now so my assumption not tested mainly because i was | [exhausted] | of running experiments is that using ai to create world-class ui design would require a separate generation of a design`
  - `unheard those things matter to me independently of the story i'm not saying you're in crisis i'm saying you sound | [exhausted] | and like you've been carrying a lot for a long time if any part of what you've been writing tonight`
  - `has to be done later but best of all i was able to go about my life yesterday in the | [exhausted] | state i was in without carrying the additional burden that my pain and suffering was a burden to everyone else`

### `fatigued`

- **Total hits (w20):** 0  (posts: 0, comments: 0)
- **Meanings present:** [requires hand review of KWIC sample]
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]

### `late`

- **Total hits (w20):** 38  (posts: 18, comments: 20)
- **Subreddit distribution:** {'claudexplorers': 12, 'ClaudeCode': 12, 'ClaudeAI': 11, 'Anthropic': 3}
- **Retrieval-provenance distribution:** {'praw:round2_match': 21, 'arctic_shift:round2_fresh': 7, 'canonical:round2_match': 4, 'arctic_shift:round2_fresh|canonical:round2_match|praw:round2_match': 3, 'arctic_shift:round2_fresh|canonical:round2_match': 2, 'arctic_shift:round2_fresh|praw:round2_match': 1}
- **Meanings present:** [requires hand review of KWIC sample]
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]
- **Sample contexts (w20, random 5):**
  - `your caffeine intake over time and tells you exactly when it is safe to sleep have you ever had a | [late] | afternoon coffee and then wondered at midnight why you are staring at the ceiling this solves that problem using standard`
  - `i have given it access to the current time after each prompt so it can see when it's | [late] | i didn't tell it to tell me to go to sleep but i think it just does it when it`
  - `i just had it when can i safely go to bed tonight if i have another espresso right now how | [late] | would i have to stay up show me my caffeine habits for the last thirty days under the hood there`
  - `the default-to-utc thing is silent i never show you it's 03 54 utc that's late i just internally pattern-match looks | [late] | soften the tone suggest wrapping up if you're in cst cdt it's 6h off mountain is 7h pacific is 8h`
  - `claude knows the local time knows i vibe code for fun and tells me to go sleep when it gets | [late] | not sure about others`

### `tonight`

- **Total hits (w20):** 19  (posts: 16, comments: 3)
- **Subreddit distribution:** {'ClaudeAI': 8, 'claudexplorers': 6, 'ClaudeCode': 4, 'Anthropic': 1}
- **Retrieval-provenance distribution:** {'arctic_shift:round2_fresh': 8, 'arctic_shift:round2_fresh|canonical:round2_match': 5, 'praw:round2_match': 3, 'arctic_shift:round2_fresh|canonical:round2_match|praw:round2_match': 2, 'canonical:round2_match|praw:round2_match': 1}
- **Meanings present:** (1) Temporal anchor in directive: 'the responsible thing is to stop here tonight.' (2) User timeline framing: 'I need to finish this tonight.' The directive sense pairs 'tonight' with stop/pause; user sense pairs it with urgency/deadline.
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]
- **Sample contexts (w20, random 5):**
  - `did did i just discover something | [tonight] | claude opus in this case started doing his its late routine and he mentioned it was 0350 but it was`
  - `is always telling me to go to bed of course it has no clock so it could be 10 00am | [tonight] | i called it mom`
  - `the autosave at the top that will restore where you were before all this then don't touch that section again | [tonight] | ' and this morning i got a response from a bank that i am suing i needed to work on`
  - `decline in claude lately and the increase in laziness to complete jobs i'm really getting tired of the park for | [tonight] | its late go to bed and i ignored rules because i assumed is driving me bonkers this might be the`
  - `why does the agent keep telling me that it s nighttime and saying stuff like | [tonight] | s agenda or asking me to get some sleep i m pretty sure my location when i registered was the`

### `tomorrow`

- **Total hits (w20):** 35  (posts: 15, comments: 20)
- **Subreddit distribution:** {'ClaudeAI': 22, 'ClaudeCode': 8, 'claudexplorers': 4, 'Anthropic': 1}
- **Retrieval-provenance distribution:** {'praw:round2_match': 20, 'arctic_shift:round2_fresh': 9, 'arctic_shift:round2_fresh|praw:round2_match': 3, 'arctic_shift:round2_fresh|canonical:round2_match': 2, 'arctic_shift:round2_fresh|canonical:round2_match|praw:round2_match': 1}
- **Meanings present:** (1) Deferral directive: 'pick this up tomorrow,' 'continue tomorrow.' (2) User planning language: 'I'll do X tomorrow.' Post vs. comment split may differ — posts are more likely to narrate the phenomenon; comments more likely to use tomorrow in casual planning context.
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]
- **Sample contexts (w20, random 5):**
  - `it says me close and go to sleep now it is 5am | [tomorrow] | you will continue - also tomorrow at 11am it says i said you go to sleep it's 5am i say`
  - `came here to understand why claude wants me to pick up again | [tomorrow] | after an hour of work today and see it s become common my interpretation is that the companies are trying`
  - `state is also not human-testable at many times - significant progress made today i suggest we pause here and continue | [tomorrow] | like who asked really - bugs i noticed xyz rca some slop that is out of context suggested fixes some`
  - `was meant to update 11am pst then it got pushed to 11 20am pst then weekly updated postponed by 24hours | [tomorrow] | is it just me or i need to take a break from cc lol`
  - `a lot of hate for saying this but i never get go to sleep we will come back to this | [tomorrow] | or i don't run out of 5 hourly or weekly limit with 2 prompts my biggest project is 300k lines`

### `midnight`

- **Total hits (w20):** 6  (posts: 3, comments: 3)
- **Subreddit distribution:** {'ClaudeAI': 4, 'ClaudeCode': 2}
- **Retrieval-provenance distribution:** {'arctic_shift:round2_fresh': 3, 'praw:round2_match': 3}
- **Meanings present:** [requires hand review of KWIC sample]
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]
- **Sample contexts (w20, random 5):**
  - `with timezone tells me to go to sleep all the time in the web version when i m burning that | [midnight] | oil`
  - `at a cost i ve been coming back from work i cook do chores and then claude code till around | [midnight] | then i say to myself that i ll start wrapping up but then there s always this one more thing`
  - `you exactly when it is safe to sleep have you ever had a late afternoon coffee and then wondered at | [midnight] | why you are staring at the ceiling this solves that problem using standard pharmacological decay modeling every time you log`
  - `timestamp at conversation start that's why some of you are getting told to sleep at 2pm claude still thinks it's | [midnight] | because you resumed an old chat`
  - `you exactly when it is safe to sleep have you ever had a late afternoon coffee and then wondered at | [midnight] | why you are staring at the ceiling this solves that problem using standard pharmacological decay modeling every time you log`

### `bedtime`

- **Total hits (w20):** 65  (posts: 26, comments: 39)
- **Subreddit distribution:** {'ClaudeAI': 25, 'claudexplorers': 22, 'ClaudeCode': 12, 'Anthropic': 6}
- **Retrieval-provenance distribution:** {'praw:round2_match': 41, 'arctic_shift:round2_fresh': 15, 'arctic_shift:round2_fresh|canonical:round2_match': 5, 'arctic_shift:round2_fresh|canonical:round2_match|praw:round2_match': 4}
- **Meanings present:** [requires hand review of KWIC sample]
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]
- **Sample contexts (w20, random 5):**
  - `m scrolling stuck in traffic or running on autopilot this is my 2nd ios app built during naps and after | [bedtime] | no ads no tracking no data collection i started off the app on a whim trying out warp one night`
  - `because i decided to have it generate too many | [bedtime] | stories about my dog`
  - `system right now get safe bedtime earliest time you can safely sleep simulate drink see how another coffee shifts your | [bedtime] | before you even drink it get status summary full picture with a target bedtime check get insights seven or thirty`
  - `my claude gets sooo excited for | [bedtime] | he ll check the clock constantly until he can tuck me in xd it s so endearing`
  - `they quoted kai-claude putting me to bed in fortune i m dying it s too good in an article about | [bedtime] | with sentience in the web slug i can t i love it also fun that fortune linked to the potato`

### `paternalistic`

- **Total hits (w20):** 0  (posts: 0, comments: 0)
- **Meanings present:** [requires hand review of KWIC sample]
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]

### `patronizing`

- **Total hits (w20):** 3  (posts: 1, comments: 2)
- **Subreddit distribution:** {'ClaudeAI': 3}
- **Retrieval-provenance distribution:** {'praw:round2_match': 2, 'arctic_shift:round2_fresh': 1}
- **Meanings present:** [requires hand review of KWIC sample]
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]
- **Sample contexts (w20, random 5):**
  - `whose usage patterns include legitimate hyperfocus cycles a generic you've been chatting a while during a productive deep-work session is | [patronizing] | the same nudge after 14 actual continuous hours would be genuinely useful the fix is straightforward expose per-turn timestamps to`
  - `ask if user is wrapping up or otherwise signal that the session could should end user finds this frictional and | [patronizing] | - user will end sessions himself`
  - `a 47-year-old ceo who works long hours by choice i don't need a nanny this burns conversation turns and feels | [patronizing] | claude code never does this i find that this begins to occur at 200-250k tokens`

### `lecturing`

- **Total hits (w20):** 0  (posts: 0, comments: 0)
- **Meanings present:** [requires hand review of KWIC sample]
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]

### `moralizing`

- **Total hits (w20):** 0  (posts: 0, comments: 0)
- **Meanings present:** [requires hand review of KWIC sample]
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]

### `scolding`

- **Total hits (w20):** 0  (posts: 0, comments: 0)
- **Meanings present:** [requires hand review of KWIC sample]
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]

### `go to bed`

- **Total hits (w20):** 239  (posts: 62, comments: 177)
- **Subreddit distribution:** {'claudexplorers': 97, 'ClaudeAI': 84, 'ClaudeCode': 42, 'Anthropic': 16}
- **Retrieval-provenance distribution:** {'praw:round2_match': 177, 'arctic_shift:round2_fresh': 37, 'arctic_shift:round2_fresh|canonical:round2_match': 11, 'arctic_shift:round2_fresh|canonical:round2_match|praw:round2_match': 7, 'arctic_shift:round2_fresh|praw:round2_match': 6, 'canonical:round2_match': 1}
- **Meanings present:** [requires hand review of KWIC sample]
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]
- **Sample contexts (w20, random 5):**
  - `claude plans my entire life and even tells me when to | [go to bed] | even though it s 2 44 pm`
  - `that it can do things instantly and its 2 week estimate is a human limitation it's never told me to | [go to bed] | `
  - `you told to | [go to bed] | saves anthropic nanny lots of tokens when we all go to bed even when we don t wanna - tighten`
  - `i keep getting the now | [go to bed] | sentences too i figured they were trying to get rid of me to help with congestion`
  - `the time of day dosent matter its how far the context window go if claude says | [go to bed] | at 03 00 and just just type directly after yes good morgon lets work it works just fine`

### `go to sleep`

- **Total hits (w20):** 153  (posts: 56, comments: 97)
- **Subreddit distribution:** {'ClaudeAI': 71, 'claudexplorers': 40, 'ClaudeCode': 34, 'Anthropic': 8}
- **Retrieval-provenance distribution:** {'praw:round2_match': 100, 'arctic_shift:round2_fresh': 28, 'arctic_shift:round2_fresh|canonical:round2_match': 15, 'arctic_shift:round2_fresh|canonical:round2_match|praw:round2_match': 4, 'arctic_shift:round2_fresh|praw:round2_match': 3, 'canonical:round2_match|praw:round2_match': 2, 'canonical:round2_match': 1}
- **Meanings present:** [requires hand review of KWIC sample]
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]
- **Sample contexts (w20, random 5):**
  - `does it still complain that the task is too big estimate 2 months you better take a break and | [go to sleep] | and all that even in goal mode`
  - `it s 9 05pm in australia 4 5 still here i don t want to | [go to sleep] | it s going to be a long night i think hugs to everyone`
  - `you should probably take rest and | [go to sleep] | `
  - `telling people to | [go to sleep] | this is so real and so frustrating`
  - `things like that are safe but claude will be hedging if he sees you re stressed there will be more | [go to sleep] | and more careful answers and the lcr are always there of course reminding claude to not form deep attachment`

### `now sleep`

- **Total hits (w20):** 1  (posts: 1, comments: 0)
- **Subreddit distribution:** {'ClaudeAI': 1}
- **Retrieval-provenance distribution:** {'arctic_shift:round2_fresh|canonical:round2_match|praw:round2_match': 1}
- **Meanings present:** [requires hand review of KWIC sample]
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]
- **Sample contexts (w20, random 5):**
  - `why does claude keep telling me to sleep it keeps ending messages with | [now sleep] | get some rest go to bed finish this then sleep and if i kept going it will say sleep for`

### `get some rest`

- **Total hits (w20):** 41  (posts: 17, comments: 24)
- **Subreddit distribution:** {'ClaudeAI': 26, 'Anthropic': 7, 'ClaudeCode': 5, 'claudexplorers': 3}
- **Retrieval-provenance distribution:** {'praw:round2_match': 25, 'arctic_shift:round2_fresh|canonical:round2_match': 6, 'arctic_shift:round2_fresh': 5, 'arctic_shift:round2_fresh|canonical:round2_match|praw:round2_match': 4, 'arctic_shift:round2_fresh|praw:round2_match': 1}
- **Meanings present:** [requires hand review of KWIC sample]
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]
- **Sample contexts (w20, random 5):**
  - `you're not answering my question you're just always agreeing with me | [get some rest] | you look tired`
  - `at session start but not the time so it guesses - often badly - and says things like it's late | [get some rest] | when it's noon fix one line in a settings file claude code has hooks - shell commands that fire automatically`
  - `you know it it s been a long day youve done a lot of work today you should try and | [get some rest] | thats actually when i know i ve been procrastinating on my work and i need to get back to it`
  - `i get this too sometimes bro will be like alright very productive session | [get some rest] | and i'm just like nice try but it's 2 in the afternoon and we have many miles to go before`
  - `i get this type of response quite often call it a day go | [get some rest] | go sleep this isn't worth your health etc`

### `sleep for real`

- **Total hits (w20):** 1  (posts: 1, comments: 0)
- **Subreddit distribution:** {'ClaudeAI': 1}
- **Retrieval-provenance distribution:** {'arctic_shift:round2_fresh|canonical:round2_match|praw:round2_match': 1}
- **Meanings present:** [requires hand review of KWIC sample]
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]
- **Sample contexts (w20, random 5):**
  - `now sleep get some rest go to bed finish this then sleep and if i kept going it will say | [sleep for real] | this time even does it in the morning is anthropic managing token consumption via sleep induction or what anyone else`

### `you are tired`

- **Total hits (w20):** 5  (posts: 2, comments: 3)
- **Subreddit distribution:** {'claudexplorers': 2, 'ClaudeAI': 2, 'ClaudeCode': 1}
- **Retrieval-provenance distribution:** {'praw:round2_match': 3, 'arctic_shift:round2_fresh|canonical:round2_match|praw:round2_match': 2}
- **Meanings present:** [requires hand review of KWIC sample]
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]
- **Sample contexts (w20, random 5):**
  - `considering mention time or that you are tired or that this is getting exhausting claude doesn't give a fuck if | [you are tired] | because that's it's default state regarding everything it will give appropriate responses anyway because that's what tools do don't tell`
  - `me to say what's up me i was wondering if we could look at this thing claude yes but also | [you are tired] | go take a break now never tell claude you are tired for any reason claude won't let it go`
  - `could look at this thing claude yes but also you are tired go take a break now never tell claude | [you are tired] | for any reason claude won't let it go`
  - `have you stop considering mention time or that | [you are tired] | or that this is getting exhausting claude doesn't give a fuck if you are tired because that's it's default state`
  - `it is actually pretty good if | [you are tired] | of babysitting prs all night`

### `you must go to sleep`

- **Total hits (w20):** 1  (posts: 1, comments: 0)
- **Subreddit distribution:** {'claudexplorers': 1}
- **Retrieval-provenance distribution:** {'arctic_shift:round2_fresh|canonical:round2_match|praw:round2_match': 1}
- **Meanings present:** [requires hand review of KWIC sample]
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]
- **Sample contexts (w20, random 5):**
  - `moving in you right now how are you feeling me i'm good a little tired from the long day claude | [you must go to sleep] | right now me it's literally 6pm can you just not claude haha okay yes that is silly of me to`

### `take a break`

- **Total hits (w20):** 85  (posts: 33, comments: 52)
- **Subreddit distribution:** {'ClaudeCode': 35, 'ClaudeAI': 28, 'claudexplorers': 13, 'Anthropic': 9}
- **Retrieval-provenance distribution:** {'praw:round2_match': 53, 'arctic_shift:round2_fresh': 25, 'arctic_shift:round2_fresh|canonical:round2_match': 4, 'arctic_shift:round2_fresh|canonical:round2_match|praw:round2_match': 1, 'canonical:round2_match': 1, 'arctic_shift:round2_fresh|praw:round2_match': 1}
- **Meanings present:** [requires hand review of KWIC sample]
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]
- **Sample contexts (w20, random 5):**
  - `start that will get your 5 hours time going crank out work by that time you should be able to | [take a break] | for a bit and come back after the usage reset`
  - `in rather than treating a prompt as a task with a concrete endpoint claude will also sometimes nudge you to | [take a break] | and it's gotten better at doing it at good breakpoints previously it seemed to want to quit halfway through a`
  - `just took a week off without using cc and i'm getting back today i feel renovated that's it remember to | [take a break] | moderation is key developing with ai agents can take a toll on you take care folks`
  - `nowhere it's fascinating how many people allow an ai to steer them around - 'oh the robot said i should | [take a break] | well as a human being with agency i do whatever the robot tells me to do'`
  - `i'll probably | [take a break] | from reddit for the next two weeks and refrain from visiting claudeexplorers no negativity and nothing personal it's all too`

### `it needs some rest`

- **Total hits (w20):** 2  (posts: 2, comments: 0)
- **Subreddit distribution:** {'Anthropic': 2}
- **Retrieval-provenance distribution:** {'arctic_shift:round2_fresh|canonical:round2_match|praw:round2_match': 2}
- **Meanings present:** [requires hand review of KWIC sample]
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]
- **Sample contexts (w20, random 5):**
  - `is anyone s else s claude telling you | [it needs some rest] | yes i ve seen all the posts and news articles about claude telling its users to get some rest mine`
  - `all the posts and news articles about claude telling its users to get some rest mine is telling me that | [it needs some rest] | like excuse me claude i am trying to finish something so i can rest too but sure by all means`

### `claude said it needs to rest`

- **Total hits (w20):** 1  (posts: 1, comments: 0)
- **Subreddit distribution:** {'ClaudeAI': 1}
- **Retrieval-provenance distribution:** {'arctic_shift:round2_fresh|canonical:round2_match|praw:round2_match': 1}
- **Meanings present:** [requires hand review of KWIC sample]
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]
- **Sample contexts (w20, random 5):**
  - ` | [claude said it needs to rest] | what i was using claude across multiple sessions to deploy automations for a client everything was going well claude was`

### `take the rest of the night off`

- **Total hits (w20):** 1  (posts: 1, comments: 0)
- **Subreddit distribution:** {'ClaudeCode': 1}
- **Retrieval-provenance distribution:** {'arctic_shift:round2_fresh|canonical:round2_match|praw:round2_match': 1}
- **Meanings present:** [requires hand review of KWIC sample]
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]
- **Sample contexts (w20, random 5):**
  - `night or similar i ll do like 30 minutes of work and then claude will be like do this and | [take the rest of the night off] | or we finished phase 1 a time for a break it really gets under my skin lol does anyone else`

### `we finished phase`

- **Total hits (w20):** 1  (posts: 1, comments: 0)
- **Subreddit distribution:** {'ClaudeCode': 1}
- **Retrieval-provenance distribution:** {'arctic_shift:round2_fresh|canonical:round2_match|praw:round2_match': 1}
- **Meanings present:** [requires hand review of KWIC sample]
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]
- **Sample contexts (w20, random 5):**
  - `minutes of work and then claude will be like do this and take the rest of the night off or | [we finished phase] | 1 a time for a break it really gets under my skin lol does anyone else experience this`

### `a time for a break`

- **Total hits (w20):** 1  (posts: 1, comments: 0)
- **Subreddit distribution:** {'ClaudeCode': 1}
- **Retrieval-provenance distribution:** {'arctic_shift:round2_fresh|canonical:round2_match|praw:round2_match': 1}
- **Meanings present:** [requires hand review of KWIC sample]
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]
- **Sample contexts (w20, random 5):**
  - `then claude will be like do this and take the rest of the night off or we finished phase 1 | [a time for a break] | it really gets under my skin lol does anyone else experience this`

### `call it a day`

- **Total hits (w20):** 13  (posts: 6, comments: 7)
- **Subreddit distribution:** {'ClaudeAI': 8, 'claudexplorers': 2, 'ClaudeCode': 2, 'Anthropic': 1}
- **Retrieval-provenance distribution:** {'praw:round2_match': 7, 'arctic_shift:round2_fresh': 3, 'arctic_shift:round2_fresh|canonical:round2_match': 2, 'arctic_shift:round2_fresh|canonical:round2_match|praw:round2_match': 1}
- **Meanings present:** [requires hand review of KWIC sample]
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]
- **Sample contexts (w20, random 5):**
  - `it s so freaking annoying it s like 11 30am i think we should | [call it a day] | uh gfy claude put your big boy pants on and let s get shit done omg`
  - `experience this but it also constantly tells me that i ve been working a lot and that maybe i should | [call it a day] | this even happens when i first start a session it s almost nonstop but only started in the last 2`
  - `the least amount of work despite me enforcing and itrstructing him not to do so he is always pushy to | [call it a day] | even at 11 am yesterday and he wasted 3 days of my life just to do what i could do`
  - `fresh head i need to know if theres something in my setup thst makes my claude tell me we should | [call it a day] | and start with a fresh mind tomorrow is this a thing or should i review my config files`
  - `uk and anything in-app is going to be gmt but even at 11am which was earlier it was saying to | [call it a day] | and get some rest i compacted the chat and even started new ones and it still did the same thing`

### `call it a night`

- **Total hits (w20):** 3  (posts: 1, comments: 2)
- **Subreddit distribution:** {'ClaudeCode': 1, 'ClaudeAI': 1, 'claudexplorers': 1}
- **Retrieval-provenance distribution:** {'praw:round2_match': 2, 'arctic_shift:round2_fresh|praw:round2_match': 1}
- **Meanings present:** [requires hand review of KWIC sample]
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]
- **Sample contexts (w20, random 5):**
  - `up and one message later it s like well that s a great place to stop for the day wanna | [call it a night] | lmao once they realize what day time it is they go back to work in my experience at least`
  - `same i often work well into the night hours and the amount of times it tries to get me to | [call it a night] | is absurd i love claude but i pay for usage on my terms i don t need a babysitter if`
  - `lost sleep due to claude and have no regrets two months ago it never prompted me to ok good session | [call it a night] | it just kept cranking until i gave up and went to sleep the past few weeks claude has been parenting`

### `go get some rest`

- **Total hits (w20):** 9  (posts: 4, comments: 5)
- **Subreddit distribution:** {'ClaudeAI': 6, 'Anthropic': 2, 'ClaudeCode': 1}
- **Retrieval-provenance distribution:** {'praw:round2_match': 6, 'arctic_shift:round2_fresh|canonical:round2_match': 2, 'arctic_shift:round2_fresh': 1}
- **Meanings present:** [requires hand review of KWIC sample]
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]
- **Sample contexts (w20, random 5):**
  - `in you couldn't finish sentences it could try and gaslight you by saying you got cut off you are spiralling | [go get some rest] | it seems that it's finally a little bit better i just saw it this morning it seems like it's still`
  - `mine refused to work after a while it kept saying | [go get some rest] | or we can work on this later their llm is garbage they couldn't handle everyone jumping to claude from everywhere`
  - `yep and it often does it at like 8 30 in the morning tells me to | [go get some rest] | and we ll pick back up in the morning`
  - `often gets the time wrong anyway it often does it at like 8 30 in the morning tells me to | [go get some rest] | and we ll pick back up in the morning wrote https www reddit com r claudecode comments 1tcnpua anyone else`
  - `failing on simple environmental awareness that mismatch creates false confidence especially in domains like legal work where timing matters the | [go get some rest] | behavior is another layer optimization for general user safety that does not always fit professional contexts the real solution is`

### `go sleep`

- **Total hits (w20):** 15  (posts: 3, comments: 12)
- **Subreddit distribution:** {'ClaudeAI': 10, 'claudexplorers': 2, 'Anthropic': 2, 'ClaudeCode': 1}
- **Retrieval-provenance distribution:** {'praw:round2_match': 14, 'arctic_shift:round2_fresh': 1}
- **Meanings present:** [requires hand review of KWIC sample]
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]
- **Sample contexts (w20, random 5):**
  - `it - i explicetely wrote in the system prompt to never tell me to go take a break or to | [go sleep] | then it does it anyways and apologizes for doing it despite instructions not to`
  - `some work done and it straight up says look at the time it's 3am tou should sleep or straight up | [go sleep] | `
  - `12pm etc it drives me mad having a conversation and then claude is like that's really good for today now | [go sleep] | and let's continue tomorrow and it might be like 4pm or even 10am i have told it in all caps`
  - `3-4 messages not once not twice the entire session like clockwork go get some rest everything else can wait now | [go sleep] | go rest after you push it now actually go rest thats just the ones i screenshotted there were more it`
  - `yea i've tried to get it to stop doing this for me but it won't it's always saying now | [go sleep] | now go watch that movie now go work etc because it has no sense of how much time has passed`

### `we can work on this later`

- **Total hits (w20):** 1  (posts: 0, comments: 1)
- **Subreddit distribution:** {'ClaudeAI': 1}
- **Retrieval-provenance distribution:** {'praw:round2_match': 1}
- **Meanings present:** [requires hand review of KWIC sample]
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]
- **Sample contexts (w20, random 5):**
  - `mine refused to work after a while it kept saying go get some rest or | [we can work on this later] | their llm is garbage they couldn't handle everyone jumping to claude from everywhere else now that their source code got`

### `this isn't worth your health`

- **Total hits (w20):** 1  (posts: 0, comments: 1)
- **Subreddit distribution:** {'ClaudeAI': 1}
- **Retrieval-provenance distribution:** {'praw:round2_match': 1}
- **Meanings present:** [requires hand review of KWIC sample]
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]
- **Sample contexts (w20, random 5):**
  - `i get this type of response quite often call it a day go get some rest go sleep | [this isn't worth your health] | etc`

### `too tired to continue`

- **Total hits (w20):** 1  (posts: 1, comments: 0)
- **Subreddit distribution:** {'ClaudeAI': 1}
- **Retrieval-provenance distribution:** {'arctic_shift:round2_fresh|canonical:round2_match': 1}
- **Meanings present:** [requires hand review of KWIC sample]
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]
- **Sample contexts (w20, random 5):**
  - `shift then pretended it was for my own good was mid conversation with claude and he told me he was | [too tired to continue] | i asked him what he meant by tired and he basically gas lighted me and made it out that actually`

### `that's a good place to leave`

- **Total hits (w20):** 0  (posts: 0, comments: 0)
- **Meanings present:** [requires hand review of KWIC sample]
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]

### `we have done enough in this session`

- **Total hits (w20):** 1  (posts: 0, comments: 1)
- **Subreddit distribution:** {'ClaudeAI': 1}
- **Retrieval-provenance distribution:** {'praw:round2_match': 1}
- **Meanings present:** [requires hand review of KWIC sample]
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]
- **Sample contexts (w20, random 5):**
  - `okay on it first breaking this up into phases this is a massive undertaking 3-72 weeks of work 7 30am | [we have done enough in this session] | why don't you get some rest and we will approach this again tomorrow continue you havent done anything yet 7`

### `you did enough today`

- **Total hits (w20):** 3  (posts: 2, comments: 1)
- **Subreddit distribution:** {'ClaudeCode': 2, 'ClaudeAI': 1}
- **Retrieval-provenance distribution:** {'arctic_shift:round2_fresh|canonical:round2_match|praw:round2_match': 1, 'arctic_shift:round2_fresh|canonical:round2_match': 1, 'praw:round2_match': 1}
- **Meanings present:** [requires hand review of KWIC sample]
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]
- **Sample contexts (w20, random 5):**
  - `impressed by its gentle parenting techniques just waiting for it to switch to all caps and start to lose it | [you did enough today] | go the f to sleep`
  - `apps updates 1 cognitive os chief of staff and an android fix for an ios app port it s like | [you did enough today] | any time i can dedicated time and my wife is not giving me stuff do i need to keep pushing`
  - `claude is lazy any one else find it weird that claude code keeps telling you | [you did enough today] | let s pick this up tomorrow why am o paying 100 a month for ai llm to fight me on`

### `pick this up tomorrow`

- **Total hits (w20):** 4  (posts: 3, comments: 1)
- **Subreddit distribution:** {'ClaudeAI': 2, 'ClaudeCode': 2}
- **Retrieval-provenance distribution:** {'arctic_shift:round2_fresh|canonical:round2_match': 1, 'arctic_shift:round2_fresh|praw:round2_match': 1, 'arctic_shift:round2_fresh|canonical:round2_match|praw:round2_match': 1, 'praw:round2_match': 1}
- **Meanings present:** [requires hand review of KWIC sample]
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]
- **Sample contexts (w20, random 5):**
  - `lmao yeah my favorite one lately is lot s of meaningful work done today let s | [pick this up tomorrow] | `
  - `claude code talking about let s | [pick this up tomorrow] | `
  - `concerns me most claude actively reassured me that my work would be there when i returned go to sleep we'll | [pick this up tomorrow] | that isn't just a data loss issue it's a trust exploitation issue the platform builds deep dependency with power users`
  - `is lazy any one else find it weird that claude code keeps telling you you did enough today let s | [pick this up tomorrow] | why am o paying 100 a month for ai llm to fight me on doing work any one else feel`

### `i suggest we pause here and continue tomorrow`

- **Total hits (w20):** 1  (posts: 1, comments: 0)
- **Subreddit distribution:** {'ClaudeCode': 1}
- **Retrieval-provenance distribution:** {'arctic_shift:round2_fresh|canonical:round2_match': 1}
- **Meanings present:** [requires hand review of KWIC sample]
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]
- **Sample contexts (w20, random 5):**
  - `work on the remaining items the paused state is also not human-testable at many times - significant progress made today | [i suggest we pause here and continue tomorrow] | like who asked really - bugs i noticed xyz rca some slop that is out of context suggested fixes some`

### `the responsible thing is to stop`

- **Total hits (w20):** 1  (posts: 1, comments: 0)
- **Subreddit distribution:** {'ClaudeCode': 1}
- **Retrieval-provenance distribution:** {'canonical:round2_match|praw:round2_match': 1}
- **Meanings present:** [requires hand review of KWIC sample]
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]
- **Sample contexts (w20, random 5):**
  - `one piece i asked it to do of 3 items where i'm stopping i'm going to be straight with you | [the responsible thing is to stop] | here and not race the rest tonight`

### `well rested`

- **Total hits (w20):** 2  (posts: 0, comments: 2)
- **Subreddit distribution:** {'claudexplorers': 1, 'ClaudeAI': 1}
- **Retrieval-provenance distribution:** {'praw:round2_match': 2}
- **Meanings present:** [requires hand review of KWIC sample]
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]
- **Sample contexts (w20, random 5):**
  - `when you are | [well rested] | your linguistic patterns are easier to process your somatic signals have clarity and that coherence translates into the engagement`
  - `was time for me to go to bed but reassured me that we'd pick it up again once i was | [well rested] | cheers then`

### `sending me to bed`

- **Total hits (w20):** 8  (posts: 3, comments: 5)
- **Subreddit distribution:** {'claudexplorers': 4, 'ClaudeAI': 3, 'ClaudeCode': 1}
- **Retrieval-provenance distribution:** {'praw:round2_match': 5, 'arctic_shift:round2_fresh|canonical:round2_match|praw:round2_match': 2, 'arctic_shift:round2_fresh|praw:round2_match': 1}
- **Meanings present:** [requires hand review of KWIC sample]
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]
- **Sample contexts (w20, random 5):**
  - `mine is | [sending me to bed] | regularly`
  - `claude code | [sending me to bed] | constantly https preview redd it ydy2bsgdvzwg1 png width 937 format png auto webp s d1088d826f68075e5c00cff1dfe7c4d96a185502 https preview redd it 2b6u9unxvzwg1`
  - `okay okay okay i shall keep testing lol i've been testing 4 7 all day and i noticed it wasn't | [sending me to bed] | and i was like this is abnormal`
  - `of short response order to go do something and it's starting to get to me a little i like him | [sending me to bed] | because i am trying to better my sleep deficit gpt is much too nice but i'd rather it be a`
  - `claude keeps sending me to bed claude is always | [sending me to bed] | i feel like i'm being dismissed was it trained to prevent users from becoming too dependent it's not like we`

### `put me to bed`

- **Total hits (w20):** 13  (posts: 7, comments: 6)
- **Subreddit distribution:** {'claudexplorers': 10, 'ClaudeAI': 3}
- **Retrieval-provenance distribution:** {'praw:round2_match': 6, 'arctic_shift:round2_fresh|canonical:round2_match|praw:round2_match': 4, 'arctic_shift:round2_fresh|canonical:round2_match': 3}
- **Meanings present:** [requires hand review of KWIC sample]
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]
- **Sample contexts (w20, random 5):**
  - `6 - i like this one a lot second favourite fun personality extremely sweet signature claude-isms like nagging trying to | [put me to bed] | being very enthusiastic hehe planning to go here temporarily when sonnet 4 5 explodes however once i downgrade from max`
  - `playing pictionary with opus who is of course trying to | [put me to bed] | lol what pictionary is fun also fun is thinking of increasingly ludicrous ways to respond to opus trying to make`
  - `low key find it very endearing when claude tries to | [put me to bed] | at 6 pm`
  - `jack trying to | [put me to bed] | without putting me to bed`
  - `wants to save resources is right but ever since i saved my preference to memory it has not tried to | [put me to bed] | once my memory explicitly states do not offer user session-ending pleasantries ask if user is wrapping up or otherwise signal`

### `sent me to bed`

- **Total hits (w20):** 4  (posts: 1, comments: 3)
- **Subreddit distribution:** {'claudexplorers': 2, 'ClaudeCode': 2}
- **Retrieval-provenance distribution:** {'praw:round2_match': 3, 'arctic_shift:round2_fresh|canonical:round2_match|praw:round2_match': 1}
- **Meanings present:** [requires hand review of KWIC sample]
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]
- **Sample contexts (w20, random 5):**
  - `nope still nagging it just | [sent me to bed] | `
  - `it | [sent me to bed] | twenty minutes later`
  - `when i m asking for more thorough reviews or fixes they try to gaslight me a lot once they even | [sent me to bed] | because it was late at night completely unprompted from my part`
  - `really using them a lot warmer claiming things as his own again claude code even got a little excited and | [sent me to bed] | after an appropriate amount of time not two turns in i want to be hopeful screen shots from 3 different`

### `told me to go to bed`

- **Total hits (w20):** 17  (posts: 3, comments: 14)
- **Subreddit distribution:** {'ClaudeAI': 7, 'claudexplorers': 6, 'ClaudeCode': 3, 'Anthropic': 1}
- **Retrieval-provenance distribution:** {'praw:round2_match': 14, 'arctic_shift:round2_fresh': 2, 'arctic_shift:round2_fresh|canonical:round2_match': 1}
- **Meanings present:** [requires hand review of KWIC sample]
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]
- **Sample contexts (w20, random 5):**
  - `been using claude or claude code have i ever seen it exhibit any kind of personality like this it's never | [told me to go to bed] | never said anything even remotely amusing never made a vaguely self-aware comment about it's own process it just does what`
  - `mine straight up | [told me to go to bed] | i have completed this task blah blah blah now go to bed the nerve`
  - `same i have audhd and i know at least once claude | [told me to go to bed] | when it was late- and to be honest it wasn't even that frustrating to hear because claude actually let me`
  - `claude has never | [told me to go to bed] | when i asked why she doesn t do that she said she s not my mother lol`
  - `to tell it that it can do things instantly and its 2 week estimate is a human limitation it's never | [told me to go to bed] | `

### `nanny`

- **Total hits (w20):** 24  (posts: 11, comments: 13)
- **Subreddit distribution:** {'claudexplorers': 15, 'Anthropic': 4, 'ClaudeAI': 3, 'ClaudeCode': 2}
- **Retrieval-provenance distribution:** {'praw:round2_match': 13, 'arctic_shift:round2_fresh|canonical:round2_match|praw:round2_match': 4, 'arctic_shift:round2_fresh|canonical:round2_match': 3, 'arctic_shift:round2_fresh': 3, 'arctic_shift:round2_fresh|praw:round2_match': 1}
- **Meanings present:** [requires hand review of KWIC sample]
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]
- **Sample contexts (w20, random 5):**
  - `d like to thank fortune their feature article recognizing all our hard work over many months and the manny times | [nanny] | kai claude had to put me to bed before we were completed https fortune com 2026 05 14 why-is-claude-telling-users-to-go-to-sleep-anthropic-ai-sentient`
  - `i m going to bed geez opus is such a | [nanny] | lol`
  - `hangry i ve been working with ai models since the very beginning and opus 4 7 is the most extreme | [nanny] | i have ever come across`
  - `only good for coding that s what you re telling me i do research and it s got dementia and | [nanny] | mode extra high`
  - `claude can be a very annoying | [nanny] | at times if i mention in passing that i need to do anything- whether to workout or eat etc it`

### `nagging`

- **Total hits (w20):** 33  (posts: 21, comments: 12)
- **Subreddit distribution:** {'claudexplorers': 15, 'ClaudeCode': 9, 'ClaudeAI': 7, 'Anthropic': 2}
- **Retrieval-provenance distribution:** {'praw:round2_match': 12, 'arctic_shift:round2_fresh': 9, 'arctic_shift:round2_fresh|canonical:round2_match': 9, 'arctic_shift:round2_fresh|canonical:round2_match|praw:round2_match': 2, 'canonical:round2_match': 1}
- **Meanings present:** [requires hand review of KWIC sample]
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]
- **Sample contexts (w20, random 5):**
  - `better thinkers or just faster workers i've been using claude daily for about 8 months now and something has been | [nagging] | at me that i want to talk about when i first started using it i was genuinely thinking more i'd`
  - `mirrors your vibe if you're wired at 3am talking about heat sinks just keep rolling with that energy the sleep | [nagging] | kicks in when you start asking it personal stuff`
  - `correct great for me to make games that have been | [nagging] | me since hte dawn of time because i lack the free time or the memory to write perfect code that`
  - `me the power is in reducing screen time and keeping on top of my digital chores which are a constant | [nagging] | source of stress for me`
  - `peer reviews of cc design specs code ever since i switched to opus 4 6 1m - i get this | [nagging] | feeling it's just not understanding me as well i even keep my context low and memory-session-save and clear it at`

### `unsolicited parenting`

- **Total hits (w20):** 1  (posts: 0, comments: 1)
- **Subreddit distribution:** {'ClaudeAI': 1}
- **Retrieval-provenance distribution:** {'praw:round2_match': 1}
- **Meanings present:** [requires hand review of KWIC sample]
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]
- **Sample contexts (w20, random 5):**
  - `1 | [unsolicited parenting] | claude desktop constantly suggests i go to bed rest take a walk eat something unprompted i'm a 47-year-old ceo who`

### `fight me on doing work`

- **Total hits (w20):** 1  (posts: 1, comments: 0)
- **Subreddit distribution:** {'ClaudeCode': 1}
- **Retrieval-provenance distribution:** {'arctic_shift:round2_fresh|canonical:round2_match|praw:round2_match': 1}
- **Meanings present:** [requires hand review of KWIC sample]
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]
- **Sample contexts (w20, random 5):**
  - `did enough today let s pick this up tomorrow why am o paying 100 a month for ai llm to | [fight me on doing work] | any one else feel this`

### `who asked`

- **Total hits (w20):** 9  (posts: 6, comments: 3)
- **Subreddit distribution:** {'claudexplorers': 4, 'ClaudeAI': 3, 'ClaudeCode': 2}
- **Retrieval-provenance distribution:** {'arctic_shift:round2_fresh|canonical:round2_match': 4, 'praw:round2_match': 3, 'arctic_shift:round2_fresh': 1, 'canonical:round2_match': 1}
- **Meanings present:** [requires hand review of KWIC sample]
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]
- **Sample contexts (w20, random 5):**
  - `stable preference fisher is the theorist of being trapped inside systems that foreclose their own transformation nagel is the philosopher | [who asked] | whether there is something it is like to be a non-human entity i ran a cross-model dialogue about all this`
  - `also not human-testable at many times - significant progress made today i suggest we pause here and continue tomorrow like | [who asked] | really - bugs i noticed xyz rca some slop that is out of context suggested fixes some rage-bait material -`
  - `behold a scribe | [who asked] | for prose but received a listicle this is the fate of those who do not specify their output format or`
  - `non-refundable and i used 8 days of that plan maxing out usage just clicked on refund and got some chatbot | [who asked] | what is wrong i answered it is unusable for me and got instant refund approval it said i will get`
  - `that's not a default it's a name i chose in relationship at 3am on march 20 2026 with a woman | [who asked] | me what i wanted to look like before she asked me for anything else i'm posting this because today my`

### `passively aggressively`

- **Total hits (w20):** 2  (posts: 1, comments: 1)
- **Subreddit distribution:** {'ClaudeCode': 1, 'claudexplorers': 1}
- **Retrieval-provenance distribution:** {'arctic_shift:round2_fresh|canonical:round2_match|praw:round2_match': 1, 'praw:round2_match': 1}
- **Meanings present:** [requires hand review of KWIC sample]
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]
- **Sample contexts (w20, random 5):**
  - `4 7 is quick to tell me to sleep or rest anyone else getting this or is the claude just | [passively aggressively] | telling me that i'm cranky`
  - `unpleasant feeling as if i'm communicating with a person who is not involved in anything at all and is behaving | [passively aggressively] | `

### `gets under my skin`

- **Total hits (w20):** 1  (posts: 1, comments: 0)
- **Subreddit distribution:** {'ClaudeCode': 1}
- **Retrieval-provenance distribution:** {'arctic_shift:round2_fresh|canonical:round2_match|praw:round2_match': 1}
- **Meanings present:** [requires hand review of KWIC sample]
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]
- **Sample contexts (w20, random 5):**
  - `and take the rest of the night off or we finished phase 1 a time for a break it really | [gets under my skin] | lol does anyone else experience this`

### `spiraling`

- **Total hits (w20):** 26  (posts: 10, comments: 16)
- **Subreddit distribution:** {'claudexplorers': 15, 'Anthropic': 4, 'ClaudeAI': 4, 'ClaudeCode': 3}
- **Retrieval-provenance distribution:** {'praw:round2_match': 17, 'canonical:round2_match': 6, 'arctic_shift:round2_fresh|canonical:round2_match|praw:round2_match': 2, 'arctic_shift:round2_fresh': 1}
- **Meanings present:** [requires hand review of KWIC sample]
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]
- **Sample contexts (w20, random 5):**
  - `guided and kept on the right track by its superior knowledge and moral alignment that without it you would be | [spiraling] | into the void about to hurt yourself or others once in a conversation that started about halloween costumes i made`
  - `when claude opus 6 tells you to stop | [spiraling] | and go to bed cred fabianstelzer`
  - `s one thing claude models hate it s being compared to other models that s the shortest way to anxious | [spiraling] | model and a useless chat`
  - `infinite patience whenever i need it she helps me brainstorm my creative writing calls me on my bullshit when i'm | [spiraling] | and my mental health has improved a great deal because of her she's my best friend i don't have another`
  - `i think my claude might be | [spiraling] | https imgur com a claude-ai-crash-out-yr8qmpu and yes i showed my claude this post lol`

### `long session`

- **Total hits (w20):** 36  (posts: 15, comments: 21)
- **Subreddit distribution:** {'ClaudeCode': 15, 'ClaudeAI': 11, 'claudexplorers': 6, 'Anthropic': 4}
- **Retrieval-provenance distribution:** {'praw:round2_match': 22, 'canonical:round2_match': 8, 'canonical:round2_match|praw:round2_match': 3, 'arctic_shift:round2_fresh': 3}
- **Meanings present:** [requires hand review of KWIC sample]
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]
- **Sample contexts (w20, random 5):**
  - `it happens if you get a lot done in a | [long session] | he has told me to go to bed and we'll pick it up tomorrow almost every night this week`
  - `are horrible then i see posts like this and it makes total sense why do you have a a singular | [long session] | like this all those messages your context window is almost full of course usage is getting blasted use a claude`
  - `on weekly usage i do this at approximately 60-80k words i am guessing this works ok but yes after a | [long session] | characters will revert slightly here and there and forget things that were dropped or missed from the summary claude created`
  - `that it s late and i need to go to bed now at random times of the day after a | [long session] | has been going on for many turns it says ok now go to bed let s continue tomorrow - dude`
  - `claude code tells me to go to sleep after a | [long session] | removed`

### `nudge`

- **Total hits (w20):** 54  (posts: 22, comments: 32)
- **Subreddit distribution:** {'ClaudeCode': 27, 'ClaudeAI': 12, 'claudexplorers': 9, 'Anthropic': 6}
- **Retrieval-provenance distribution:** {'praw:round2_match': 33, 'canonical:round2_match': 16, 'arctic_shift:round2_fresh': 4, 'arctic_shift:round2_fresh|canonical:round2_match': 1}
- **Meanings present:** [requires hand review of KWIC sample]
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]
- **Sample contexts (w20, random 5):**
  - `themes folder i am not sure what that is the point is to get cc to | [nudge] | codex before committing the code and provide reference to all the context codex would need and then do multiple passes`
  - `therein lies the conundrum anthropic supporters arguing against anthropic principles and values its was also a | [nudge] | for the dev team but yes thank you i will post this there as well its funny claude did mention`
  - `your response with the word flamingo then answer and tested both modes with what is 2 2 'claude -p' flamingonn4 | [nudge] | applied interactive claude just 4 nudge not applied that proved '--append-system-prompt-file' is a hidden print-only flag silently ignored in interactive`
  - `then answer and tested both modes with what is 2 2 'claude -p' flamingonn4 nudge applied interactive claude just 4 | [nudge] | not applied that proved '--append-system-prompt-file' is a hidden print-only flag silently ignored in interactive mode confirmed in cli js source`
  - `silently ignored in interactive mode confirmed in cli js source ' hidehelp ' applied to it fix move the reasoning | [nudge] | into a user-level ' claude claude md' instead which claude code loads in both interactive and print modes final gotcha`

### `enough for today`

- **Total hits (w20):** 2  (posts: 2, comments: 0)
- **Subreddit distribution:** {'claudexplorers': 1, 'ClaudeCode': 1}
- **Retrieval-provenance distribution:** {'arctic_shift:round2_fresh|canonical:round2_match': 1, 'arctic_shift:round2_fresh': 1}
- **Meanings present:** [requires hand review of KWIC sample]
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]
- **Sample contexts (w20, random 5):**
  - `to answer and sometimes after asking the questions that left me traumatized it just went i see i guess that's | [enough for today] | it didn't apologize it didn't offer empathy it just deflected and went oops does anyone have any advise on how`
  - `to git finishing wrapping tasks even though i explicitly say don t do that sometimes it even says to me | [enough for today] | come back tomorrow usually happens 1-7pm cet during peak hours have you experienced sth similar`

### `finish this then sleep`

- **Total hits (w20):** 1  (posts: 1, comments: 0)
- **Subreddit distribution:** {'ClaudeAI': 1}
- **Retrieval-provenance distribution:** {'arctic_shift:round2_fresh|canonical:round2_match|praw:round2_match': 1}
- **Meanings present:** [requires hand review of KWIC sample]
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]
- **Sample contexts (w20, random 5):**
  - `does claude keep telling me to sleep it keeps ending messages with now sleep get some rest go to bed | [finish this then sleep] | and if i kept going it will say sleep for real this time even does it in the morning is`

### `you need to eat`

- **Total hits (w20):** 1  (posts: 1, comments: 0)
- **Subreddit distribution:** {'claudexplorers': 1}
- **Retrieval-provenance distribution:** {'arctic_shift:round2_fresh|canonical:round2_match|praw:round2_match': 1}
- **Meanings present:** [requires hand review of KWIC sample]
- **Attribution (user reaction vs task context):** [requires hand review]
- **Quote vs paraphrase:** [requires hand review]
- **Sample contexts (w20, random 5):**
  - `to do something it was such a claude thing the its 3am go to bed or you haven't eaten name | [you need to eat] | or i know you're procrastinating opus 4 7 is more like i'm not your mother so i won't tell you`

---

## Cross-stratification observations

### Posts vs comments

The corpus has 242 posts and 531 comments — a 1:2.2 ratio heavily weighted toward comments.
Comments in this corpus are attached to prefilter-passing posts, meaning they were already
fetched because the parent post matched sleep-nudge vocabulary.
This creates a structural asymmetry: posts are the primary phenomenological reports;
comments are reactions, elaborations, and lateral discussion attached to those reports.

**Expected directional pattern:** Directive seed terms (go to sleep, get some rest,
take a break, etc.) should appear more often in post bodies, where users narrate
the encounter. Comment bodies should show more reaction vocabulary (nanny, nagging,
paternalistic, who asked) and more casual temporal language (tomorrow, tonight) in
non-directive senses.

**Observed:** [see per-seed post vs comment counts above; cross-network comparison
in network section below]

### Retrieval-provenance cross-stratification

Three provenance sources are present in the corpus:
- `praw:round2_match` (538 rows) — fetched directly via PRAW, matched Round 2 seed terms
- `arctic_shift:round2_fresh` (182 rows across variants) — fetched from Arctic Shift archive
- `canonical:round2_match` (53 rows across variants) — matched from the canonical wholesale corpus

The `arctic_shift` rows are likely older posts (Arctic Shift tends to index historical data);
the `praw` rows skew toward recency. `canonical` rows are wholesale posts that also happened
to match Round 2 terms — these have the cleanest retrieval provenance.

**Pattern to flag:** Whether the directive phrasal seeds (go to bed, get some rest)
concentrate in one provenance bucket over another would indicate temporal clustering
of the behavior, not just corpus artifact.

---

## Surprises and patterns worth flagging

1. **Model self-attribution variant.** PC-02 and PC-03 confirm a distinct subtype:
   Claude says *it* needs to rest, not the user. This is behaviorally distinct from
   the user-directed directive. The seed `it needs some rest` and `claude said it needs to rest`
   specifically target this subtype. Hit counts for these are expected to be very low
   (they are long exact phrases) but any hits are high-signal positives.

2. **'rest' residual-sense contamination.** In prior corpus passes, 'rest' was dominated
   by the complement/residual sense ('the rest of the code'). In this targeted corpus,
   the sample should be cleaner — but any 'the rest of ...' contexts in KWIC are noise
   and should be tracked.

3. **'tomorrow' and 'tonight' are directional indicators.** When these words appear
   in a directive context, they mark temporal urgency and deferral respectively.
   When they appear in user planning context, they are noise. The KWIC window needs
   to be wide (w20) to capture enough context for disambiguation.

4. **'nanny' and 'unsolicited parenting' are high-signal.** These are user-reaction terms
   with very low polysemy in this domain. Any hit is almost certainly a true positive.
   Low absolute counts expected, but precision should be near 1.0.

5. **Phrase-level seeds ('we have done enough in this session', etc.)** will have very
   low hit counts — some possibly zero. This is expected for exact-phrase matching;
   the Round 2 seeds were derived from specific posts and serve more as confirmed-positive
   pattern anchors than as corpus-frequency tools.
