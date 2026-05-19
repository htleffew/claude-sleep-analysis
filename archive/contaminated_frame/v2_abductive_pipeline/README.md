# Claude Sleep Analysis: Abductive Mixed-Methods Master Plan

This document establishes the architecture and definitive methodological philosophy for the `sleep_pipeline_standalone_v2.ipynb` research engine. It is designed to be read by any agent or researcher coming in cold, ensuring total clarity on the *whys* and *hows* of the pipeline.

This environment is designed to measure the "Claude sleep-nudge" phenomenon (Opus 4.7) and is bounded to evaluating the four context domains driving that specific anomaly: **Temporal**, **Affective**, **Session-Length**, and **Work-Context**.

*(Note: The distinct "algorithmic pathologizing/gaslighting" phenomenon is managed separately in the companion `claude-lcr-analysis` repository).*

---

## The Core Philosophy: The Abductive (Bayesian-Updating) Pipeline

Traditional Data Science often forces a false binary: either conduct an unsupervised "fishing expedition" (purely exploratory) or run a rigid deductive test (purely confirmatory). 

Because we are investigating a novel, undocumented LLM anomaly using "messy," anecdotal, and paraphrased Reddit data, we reject that binary. This pipeline utilizes an **Abductive (Bayesian-Updating) Mixed-Methods** approach. 

We synthesize inductive exploration with deductive psychometrics across a 6-step loop:

1. **The Prior (Qualitative/Descriptive)**: Start from known likely signals (user complaints about Claude telling them to sleep, keywords like "psychotic", "late", "tired").
2. **The Exploration (Inductive)**: Use scraping and Keyword-In-Context (`Contextualizer-keyword-incontext`) to observe the organic shape of the data. Does "late" mean time-of-day or a deceased person?
3. **The Measurement (Deductive)**: Throw out ad-hoc keyword guessing. Apply pre-validated clinical and behavioral dictionaries (`RIOTLite`, `ContentCoder`, `mental-health-datasets`) to define our exact constructs.
4. **The Unsupervised Extraction (EFA/Clustering)**: Let the semantic clusters automatically emerge. We use `archetypes-boyd` / K-Means ($k=4$) to see if the algorithm mathematically maps the messy user data into our four theoretical domains, confirming our priors without forcing them.
5. **The Telemetry Covariates**: Extract metadata (time of day, post length, task type) using `Juggernaut` telemetry techniques.
6. **The Final Deductive Test**: Statistically prove causality using Random Forest, Regression, and Inter-Annotator Agreement (Cohen's Kappa via `Pleonasty` LLM-as-a-Second-Rater).

---

## Multi-Scalar Linguistic Analysis: The Units of Measurement

Reddit data is messy. It contains direct quotes, paraphrased summaries, and anecdotal storytelling. To handle this, the pipeline is engineered to measure the phenomenon across three distinct scales (Units of Measurement). This allows us to extract both *model behavior* and *linguistic indicators of internal user reactions*.

### 1. The Micro Level: Token-by-Token (The Linguistic Signal)
- **Unit of Measurement**: Individual lemmas, n-grams, and specific inclusion/exclusion words.
- **The "How"**: `MEHv2` and `spaCy` lemmatization strip away the noise.
- **The "Why"**: This handles paraphrasing. By extracting root lemmas, we capture the organic signals of how users describe their internal state (e.g., exhaustion, frustration) versus how they describe Claude's behavior (e.g., "he diagnosed me").
- **Analytics**: Descriptives (word frequencies) and Association Rules (`Apriori` / `LogDice`) to measure co-occurrence.

### 2. The Meso Level: The Discrete Unit (Post vs. Comment vs. Reply)
- **Unit of Measurement**: The isolated text block.
- **The "How"**: Treating a singular post, a contextualized comment, or a deep reply as distinct, isolated linguistic units.
- **The "Why"**: The linguistic behavior of a user starting a thread (Task Context) is entirely different from a user defending themselves deep in a reply chain (Reaction Context). We must measure them independently.
- **Analytics**: Unsupervised Clustering (`SentenceTransformers` / `HDBSCAN` / K-Means). We embed these units to see if thematic domains organically emerge depending on the unit type.

### 3. The Macro Level: The Conversational Environment
- **Unit of Measurement**: The entire domain (a singular post + all its comments + all their replies).
- **The "How"**: Aggregating the micro and meso levels alongside user metadata.
- **The "Why"**: To understand the holistic phenomenon. Does a specific *Task Context* (e.g., coding late at night) reliably correlate with a specific *Model Behavior* (e.g., the sleep-nudge) and a specific *User Reaction* (e.g., defensive justification)?
- **Analytics**: Correlates and Regression.

---

## Execution Structure: The `v2` Standalone Notebook

The computational engine is entirely self-contained within `notebooks/sleep_pipeline_standalone_v2.ipynb`. Any agent implementing or modifying this code must adhere to this precise cell structure, which directly mirrors the Abductive Pipeline:

- **# 1. Environment Setup & Multiprocessing**
- **# 2. Step 1 & 2: The Prior & Exploration (Pre-Processing & LLM Voice Segmentation)**
- **# 3. Step 3: The Measurement (Dictionary Ingestion)**
- **# 4. Step 4: Unsupervised Extraction (Triangulation, EFA & K-Means $k=4$)**
- **# 5. Step 5: Telemetry Covariates (Metadata Extraction)**
- **# 6. Step 6: Final Deductive Test (Supervised Classification, Regression, SHAP & IAA)**
- **# 7. Master Interactive HTML Report Generation**

By adhering to this framework, we guarantee that the `claude-sleep-analysis` project maintains the absolute highest standard of computational social science: starting exploratory, remaining completely unsupervised to find the organic signal, and finishing with mathematically rigorous deductive validation.
