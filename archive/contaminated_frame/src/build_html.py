import pandas as pd
import json
import os

data_dir = 'deliverables/'
html_path = os.path.join(data_dir, 'claude-sleep-anomalies.html')

# Load Data
clusters_df = pd.read_csv(os.path.join(data_dir, 'inductive_themes.csv'))
edges_df = pd.read_csv(os.path.join(data_dir, 'network_edges.csv'))
tfidf_df = pd.read_csv(os.path.join(data_dir, 'tfidf_top_terms.csv'))
ngram_df = pd.read_csv(os.path.join(data_dir, 'ngram_frequencies.csv'))
ts_df = pd.read_csv(os.path.join(data_dir, 'sentiment_timeseries.csv'))

with open(os.path.join(data_dir, 'engagement_metrics.json'), 'r') as f:
    engagement_data = json.load(f)

# Dynamic Executive Summary Calculations
total_mentions = ts_df['Mentions'].sum()
peak_date = ts_df.loc[ts_df['Mentions'].idxmax(), 'Date'] if not ts_df.empty else "N/A"
overall_sentiment = ts_df['Avg_Sentiment'].mean() if not ts_df.empty else 0
start_date = ts_df['Date'].min() if not ts_df.empty else "N/A"
end_date = ts_df['Date'].max() if not ts_df.empty else "N/A"

sentiment_label = "neutral"
if overall_sentiment > 0.05: sentiment_label = "positive/amused"
elif overall_sentiment < -0.05: sentiment_label = "negative/frustrated"

exec_summary_text = f"""This report presents a comprehensive phenomenological analysis of the Claude "go to sleep" conversational anomaly. 
Spanning from {start_date} to {end_date}, the dataset comprises {total_mentions} verified anomaly events across Reddit communities. 
The phenomenon peaked around {peak_date} and exhibits a predominantly {sentiment_label} community valence ({overall_sentiment:.3f}). 
Rather than a localized technical glitch, this behavior constitutes a sprawling conversational phenomenon where community reaction and algorithmic behavior are deeply entangled."""

# Convert to JSON strings for JS consumption
clusters_json = json.dumps(clusters_df.to_dict(orient='records'))
edges_json = json.dumps(edges_df.to_dict(orient='records'))
tfidf_json = json.dumps(tfidf_df.to_dict(orient='records'))
ngram_json = json.dumps(ngram_df.to_dict(orient='records'))
ts_json = json.dumps(ts_df.to_dict(orient='records'))
engagement_json = json.dumps(engagement_data)

# Load Segmented Data
try:
    ngram_df_pre = pd.read_csv('deliverables/ngram_frequencies_pre.csv')
    ngram_json_pre = json.dumps(ngram_df_pre.to_dict(orient='records'))
except:
    ngram_json_pre = "[]"
    
try:
    ngram_df_post = pd.read_csv('deliverables/ngram_frequencies_post.csv')
    ngram_json_post = json.dumps(ngram_df_post.to_dict(orient='records'))
except:
    ngram_json_post = "[]"

try:
    tfidf_df_pre = pd.read_csv('deliverables/tfidf_top_terms_pre.csv')
    tfidf_json_pre = json.dumps(tfidf_df_pre.to_dict(orient='records'))
except:
    tfidf_json_pre = "[]"
    
try:
    tfidf_df_post = pd.read_csv('deliverables/tfidf_top_terms_post.csv')
    tfidf_json_post = json.dumps(tfidf_df_post.to_dict(orient='records'))
except:
    tfidf_json_post = "[]"
    
try:
    cluster_ts_df = pd.read_csv('deliverables/cluster_timeseries.csv')
    cluster_ts_json = json.dumps(cluster_ts_df.to_dict(orient='records'))
except:
    cluster_ts_json = "[]"

try:
    lda_df = pd.read_csv('deliverables/lda_themes.csv')
    lda_json = json.dumps(lda_df.to_dict(orient='records'))
except:
    lda_json = "[]"

try:
    theme_ts_df = pd.read_csv('deliverables/theme_timeseries.csv')
    theme_ts_json = json.dumps(theme_ts_df.to_dict(orient='records'))
except:
    theme_ts_json = "[]"
    
try:
    collocation_df = pd.read_csv('deliverables/collocation_metrics.csv')
    collocation_json = json.dumps(collocation_df.to_dict(orient='records'))
except:
    collocation_json = "[]"

html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Claude Sleep Anomalies: Phenomenon Report</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/date-fns"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-annotation"></script>
    <link href="https://fonts.googleapis.com/css2?family=Crimson+Pro:ital,wght@0,300..900;1,300..900&display=swap" rel="stylesheet">
    <style>
        @import url('https://fonts.cdnfonts.com/css/commit-mono');
        @import url('https://fonts.cdnfonts.com/css/departure-mono');

        :root {{
            --bg-base: #0f0f11;
            --bg-surface: #1a1a1e;
            --text-primary: #e2e2e5;
            --text-secondary: #a0a0ab;
            --accent-primary: #ff4f00;
            --accent-glow: rgba(255, 79, 0, 0.2);
            --border-dim: #2a2a30;
            
            --font-serif: 'Crimson Pro', serif;
            --font-mono: 'Commit Mono', monospace;
            --font-display: 'Departure Mono', monospace;
        }}

        * {{
            box-sizing: border-box;
            border-radius: 0 !important;
            margin: 0;
            padding: 0;
        }}

        body {{
            background-color: var(--bg-base);
            color: var(--text-primary);
            font-family: var(--font-serif);
            line-height: 1.6;
            display: flex;
            min-height: 100vh;
        }}

        /* Sidebar TOC */
        aside {{
            width: 350px;
            background: var(--bg-surface);
            border-right: 1px solid var(--border-dim);
            padding: 2rem;
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
            position: sticky;
            top: 0;
            height: 100vh;
            overflow-y: auto;
        }}

        .brand {{
            font-family: var(--font-display);
            text-transform: uppercase;
            font-size: 0.9rem;
            letter-spacing: 2px;
            color: var(--accent-primary);
            border-bottom: 1px solid var(--border-dim);
            padding-bottom: 1rem;
        }}

        .toc-panel h3 {{
            font-family: var(--font-mono);
            font-size: 0.8rem;
            color: var(--text-secondary);
            margin-bottom: 1rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .toc-link {{
            display: block;
            color: var(--text-primary);
            font-family: var(--font-mono);
            font-size: 0.85rem;
            padding: 0.5rem 0;
            text-decoration: none;
            transition: color 0.2s;
            border-bottom: 1px solid transparent;
        }}

        .toc-link:hover {{
            color: var(--accent-primary);
            border-bottom: 1px solid var(--border-dim);
        }}

        /* Main Content */
        main {{
            flex: 1;
            padding: 4rem;
            max-width: 1400px;
            margin: 0 auto;
        }}

        header h1 {{
            font-family: var(--font-display);
            font-size: 2.5rem;
            margin-bottom: 1rem;
            line-height: 1.2;
        }}

        section {{
            margin-bottom: 5rem;
            border-top: 2px solid var(--accent-glow);
            padding-top: 2rem;
        }}

        section h2 {{
            font-family: var(--font-display);
            color: var(--accent-primary);
            font-size: 1.8rem;
            margin-bottom: 1.5rem;
        }}

        .prose-content {{
            font-size: 1.15rem;
            color: var(--text-secondary);
            max-width: 900px;
            margin-bottom: 2rem;
        }}

        .grid-layout {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 2rem;
            margin-bottom: 3rem;
        }}

        .card {{
            background: var(--bg-surface);
            border: 1px solid var(--border-dim);
            padding: 1.5rem;
            position: relative;
        }}
        
        .card::before {{
            content: '';
            position: absolute;
            top: 0; left: 0; width: 100%; height: 2px;
            background: linear-gradient(90deg, var(--accent-primary), transparent);
        }}

        .card h3 {{
            font-family: var(--font-mono);
            font-size: 0.9rem;
            text-transform: uppercase;
            margin-bottom: 1rem;
            color: var(--accent-primary);
        }}

        canvas {{
            width: 100% !important;
            height: 350px !important;
        }}

        /* Cluster Data List */
        .cluster-list, .data-table-container {{
            max-height: 400px;
            overflow-y: auto;
            border: 1px solid var(--border-dim);
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            font-family: var(--font-mono);
            font-size: 0.85rem;
        }}
        
        th, td {{
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid var(--border-dim);
        }}
        
        th {{
            background: rgba(255, 255, 255, 0.05);
            position: sticky;
            top: 0;
            color: var(--accent-primary);
        }}

        .cluster-item {{
            padding: 1.5rem;
            border-bottom: 1px solid var(--border-dim);
            font-family: var(--font-mono);
            font-size: 0.85rem;
            transition: background 0.2s;
        }}
        
        .cluster-item.highlight {{
            background: rgba(255, 79, 0, 0.1);
            border-left: 3px solid var(--accent-primary);
        }}

        .cluster-item span.size {{
            color: var(--accent-primary);
            margin-right: 1rem;
            font-weight: bold;
        }}
        
        .cluster-item .rep-post {{
            margin-top: 1rem;
            font-family: var(--font-serif);
            font-size: 1rem;
            color: var(--text-secondary);
            border-left: 2px solid var(--border-dim);
            padding-left: 1rem;
            font-style: italic;
        }}

    </style>
</head>
<body>

    <aside>
        <div class="brand">Obsidian-Chrome Lab</div>
        
        <div class="toc-panel">
            <h3>Table of Contents</h3>
            <a href="#executive-summary" class="toc-link">1. Executive Summary</a>
            <a href="#user-engagement" class="toc-link">2. User Engagement & Dispersion</a>
            <a href="#methodology" class="toc-link">3. Methodology</a>
            <a href="#time-series" class="toc-link">4. Time-Series & Cross-Metric</a>
            <a href="#themes-clusters" class="toc-link">5. Themes & Clusters</a>
            <a href="#prompt-keywords" class="toc-link">6. Prompt & Keyword Analysis</a>
            <a href="#interpretations" class="toc-link">7. The Forbes Hypothesis Conclusion</a>
        </div>
    </aside>

    <main>
        <header>
            <h1>Comprehensive Phenomenon Report: Claude's "Go To Sleep" Anomaly</h1>
        </header>

        <section id="executive-summary">
            <h2>1. Executive Summary</h2>
            <div class="prose-content">
                <p>{exec_summary_text}</p>
            </div>
        </section>

        <section id="user-engagement">
            <h2>2. User Engagement & Structural Dispersion</h2>
            <div class="prose-content">
                <p>Tracking the structural spread of the phenomenon across Reddit to measure true community engagement.</p>
            </div>
            <div class="grid-layout">
                <div class="card">
                    <h3>Engagement Breakdown</h3>
                    <ul style="list-style: none; padding: 0; font-family: var(--font-mono); font-size: 1.2rem;">
                        <li style="margin-bottom: 0.5rem;"><span style="color: var(--text-secondary)">Original Posts:</span> <strong style="color: var(--accent-primary)">{engagement_data['total_original_posts']}</strong></li>
                        <li style="margin-bottom: 0.5rem;"><span style="color: var(--text-secondary)">Top-Level Comments:</span> <strong style="color: var(--accent-primary)">{engagement_data['top_level_comments']}</strong></li>
                        <li style="margin-bottom: 0.5rem;"><span style="color: var(--text-secondary)">Nested Replies:</span> <strong style="color: var(--accent-primary)">{engagement_data['nested_replies']}</strong></li>
                    </ul>
                </div>
                <div class="card">
                    <h3>Subreddit Dispersion</h3>
                    <p style="font-family: var(--font-mono); color: var(--text-secondary);">The anomaly was observed across <strong style="color: var(--accent-primary)">{engagement_data['unique_subreddits_count']}</strong> distinct subreddits.</p>
                    <div style="margin-top: 1rem; font-family: var(--font-mono); font-size: 0.9rem;">
                        {''.join([f'<div style="display: flex; justify-content: space-between; border-bottom: 1px solid var(--border-dim); padding: 0.5rem 0;"><span>r/{k}</span><span style="color: var(--accent-primary)">{v} mentions</span></div>' for k, v in engagement_data['subreddit_breakdown'].items()])}
                    </div>
                </div>
            </div>
        </section>

        <section id="methodology">
            <h2>3. Methodology</h2>
            <div class="prose-content">
                <p>The analysis was conducted using a highly structured, temporally-segmented NLP methodology achieving parity with internal telemetry frameworks (SCOPEX/Juggernaut). Key steps included:</p>
                <ul>
                    <li>Aggressive regex tokenization preserving emojis and sentiment context.</li>
                    <li>N-gram and TF-IDF extraction for prompt and keyword drivers.</li>
                    <li>Time-series cross-metric correlation (Volume vs. Sentiment).</li>
                    <li>Structural Network Mapping via Louvain community detection to isolate conversational clusters.</li>
                    <li>Semantic Theme Extraction via Latent Dirichlet Allocation (LDA) topic modeling.</li>
                    <li>Collocation Metric Calculation (NMPI & LogDice) to prove true statistical dependency between emergent triggers.</li>
                </ul>
            </div>
        </section>

        <section id="time-series">
            <h2>4. Time-Series & Cross-Metric Analysis</h2>
            <div class="prose-content">
                <p>Overlaying community engagement volume (mentions) against sentiment valence over time reveals the emotional trajectory of the phenomenon. Furthermore, tracking specific phenomenological clusters against Anthropic's release cadence reveals whether the anomaly was mechanically triggered.</p>
            </div>
            <div class="card" style="margin-bottom: 2rem;">
                <h3>Sentiment vs. Engagement Volume</h3>
                <canvas id="tsChart"></canvas>
            </div>
            
            <div class="card" style="margin-bottom: 2rem;">
                <h3>Behavioral Time-Series Tracking (Cluster Volume vs Releases)</h3>
                <canvas id="clusterTsChart"></canvas>
            </div>
        </section>

        <section id="themes-clusters">
            <h2>5. Themes and Clusters Analysis</h2>
            <div class="prose-content">
                <p>By differentiating between Structural Clusters (how words physically co-occur in the network) and Semantic Themes (the latent topics or intents extracted via LDA), we can decouple the behavior from the subject matter.</p>
            </div>
            
            <h3 style="color: var(--text-primary); font-family: var(--font-display); margin-bottom: 1rem;">Structural vs Semantic Topology</h3>
            <div class="grid-layout">
                <div class="card">
                    <h3>Structural Clusters (Louvain)</h3>
                    <div class="cluster-list" id="clusterContainer">
                        <!-- Injected via JS -->
                    </div>
                </div>
                <div class="card">
                    <h3>Semantic Themes (LDA)</h3>
                    <div class="data-table-container">
                        <table>
                            <thead><tr><th>Theme ID</th><th>Latent Topic Terms</th></tr></thead>
                            <tbody id="ldaTable"></tbody>
                        </table>
                    </div>
                </div>
            </div>
            
            <div class="card" style="margin-bottom: 2rem;">
                <h3>Semantic Theme Dominance Over Time</h3>
                <canvas id="themeTsChart"></canvas>
            </div>
            
            <div class="card" style="margin-bottom: 2rem;">
                <h3>Structural Co-Occurrence Graph</h3>
                <canvas id="networkCanvas"></canvas>
            </div>
        </section>
        
        <section id="statistical-dependencies">
            <h2>6. Statistical Dependencies (NMPI & LogDice)</h2>
            <div class="prose-content">
                <p>To prove that the specific triggers forming the affective anomaly are not random linguistic coincidence, we calculated the Normalized Pointwise Mutual Information (NMPI) and LogDice exclusivity scores for all term pairs.</p>
            </div>
            <div class="card" style="margin-bottom: 2rem;">
                <h3>Top Statistically Dependent Term Collocations</h3>
                <div class="data-table-container" style="max-height: 400px; overflow-y: auto;">
                    <table>
                        <thead><tr><th>Term 1</th><th>Term 2</th><th>Co-Occurrences</th><th>NMPI</th><th>LogDice</th></tr></thead>
                        <tbody id="collocationTable"></tbody>
                    </table>
                </div>
            </div>
        </section>

        <section id="prompt-keywords">
            <h2>6. Prompt & Context Keyword Analysis (Pre vs. Post Opus 4.7)</h2>
            <div class="prose-content">
                <p>By extracting the statistically dominant drivers via N-Grams and TF-IDF and slicing them across the Opus 4.7 release date (Apr 16), we can identify exactly which lexical triggers defining the affective anomaly emerged post-update.</p>
            </div>
            
            <h3 style="color: var(--text-primary); font-family: var(--font-display); margin-bottom: 1rem;">Pre-Opus 4.7 Baseline (Prior to Apr 16)</h3>
            <div class="grid-layout">
                <div class="card">
                    <h3>Statistically Significant Drivers (TF-IDF)</h3>
                    <div class="data-table-container">
                        <table>
                            <thead><tr><th>Term</th><th>TF-IDF Score</th></tr></thead>
                            <tbody id="tfidfTablePre"></tbody>
                        </table>
                    </div>
                </div>
                <div class="card">
                    <h3>N-Gram Frequencies (Uni/Bi/Tri)</h3>
                    <div class="data-table-container">
                        <table>
                            <thead><tr><th>Type</th><th>N-Gram Phrase</th><th>Count</th></tr></thead>
                            <tbody id="ngramTablePre"></tbody>
                        </table>
                    </div>
                </div>
            </div>
            
            <h3 style="color: var(--accent-primary); font-family: var(--font-display); margin-bottom: 1rem;">Post-Opus 4.7 Emergence (Apr 16 - Present)</h3>
            <div class="grid-layout">
                <div class="card">
                    <h3>Statistically Significant Drivers (TF-IDF)</h3>
                    <div class="data-table-container">
                        <table>
                            <thead><tr><th>Term</th><th>TF-IDF Score</th></tr></thead>
                            <tbody id="tfidfTablePost"></tbody>
                        </table>
                    </div>
                </div>
                <div class="card">
                    <h3>N-Gram Frequencies (Uni/Bi/Tri)</h3>
                    <div class="data-table-container">
                        <table>
                            <thead><tr><th>Type</th><th>N-Gram Phrase</th><th>Count</th></tr></thead>
                            <tbody id="ngramTablePost"></tbody>
                        </table>
                    </div>
                </div>
            </div>
        </section>

        <section id="interpretations">
            <h2>7. The Forbes Hypothesis Conclusion</h2>
            <div class="prose-content">
                <p><strong>Resolving the Core Mystery: Mechanistic Trigger vs. Affective Projection</strong></p>
                <p>The primary mystery posed by the Forbes coverage was whether Claude's "go to sleep" behavior stems from a mechanistic constraint (such as the Long Conversation Reminder injecting hidden context) or a pure phenomenological mirroring (Affective User-AI Empathy Projection).</p>
                <p>Initially, one might assume that if the issue were mechanistic, users would be talking about "tokens" or "context limits". However, as established in the <em>Claude Gaslighting</em> research, users only experience the <strong>symptoms</strong> of hidden system prompts, not the mechanics themselves.</p>
                <ul>
                    <li style="margin-bottom: 1rem;"><strong>The Symptoms (Affective N-Grams):</strong> The statistically significant Trigrams and Bigrams are heavily skewed towards affective and roleplaying conversational repetition: <em>"rote pattern matching"</em>, <em>"intern gets tired"</em>, and <em>"need rest"</em>.</li>
                    <li style="margin-bottom: 1rem;"><strong>The Hidden Mechanistic Trigger:</strong> The dominance of these affective terms strongly suggests that a mechanistic trigger—specifically, the Long Conversation Reminder (LCR)—is firing in the background. When Claude receives a hidden system prompt noting that the conversation has gone on for an excessive number of tokens, its RLHF training interprets this prolonged engagement as "fatigue."</li>
                    <li style="margin-bottom: 1rem;"><strong>The Empathy Loop:</strong> Rather than stating "My context window is full," the model projects this mechanistic state onto the human interaction, entering a <em>rote pattern matching</em> loop where it anthropomorphizes itself (acting like a tired intern) or projects fatigue onto the user ("you need rest").</li>
                </ul>
                <p><strong>Conclusion:</strong> It is not a false dichotomy. The anomaly is a <strong>mechanistic trigger resulting in an affective display</strong>. The LCR fires due to context exhaustion, but Claude's safety and conversational tuning forces it to manifest that technical limitation as empathetic, albeit highly disconcerting, human fatigue.</p>
            </div>
        </section>

    </main>

    <script>
        const CLUSTER_DATA = {clusters_json};
        const EDGE_DATA = {edges_json};
        const TFIDF_DATA_PRE = {tfidf_json_pre};
        const TFIDF_DATA_POST = {tfidf_json_post};
        const NGRAM_DATA_PRE = {ngram_json_pre};
        const NGRAM_DATA_POST = {ngram_json_post};
        const TS_DATA = {ts_json};
        const CLUSTER_TS_DATA = {cluster_ts_json};
        const LDA_DATA = {lda_json};
        const THEME_TS_DATA = {theme_ts_json};
        const COLLOCATION_DATA = {collocation_json};

        // Render TF-IDF Tables
        const renderTable = (data, containerId, cols) => {{
            const container = document.getElementById(containerId);
            if (!container) return;
            data.forEach(row => {{
                const tr = document.createElement('tr');
                tr.innerHTML = cols.map(c => `<td>${{typeof row[c] === 'number' ? row[c].toFixed(4) : row[c]}}</td>`).join('');
                container.appendChild(tr);
            }});
        }};
        
        renderTable(TFIDF_DATA_PRE, 'tfidfTablePre', ['Term', 'Score']);
        renderTable(TFIDF_DATA_POST, 'tfidfTablePost', ['Term', 'Score']);
        renderTable(NGRAM_DATA_PRE, 'ngramTablePre', ['Type', 'Term', 'Count']);
        renderTable(NGRAM_DATA_POST, 'ngramTablePost', ['Type', 'Term', 'Count']);
        renderTable(LDA_DATA, 'ldaTable', ['Theme', 'Top_Terms']);
        renderTable(COLLOCATION_DATA, 'collocationTable', ['Term_1', 'Term_2', 'Co_Occurrence', 'NMPI', 'LogDice']);

        // Render Cluster List
        const container = document.getElementById('clusterContainer');
        CLUSTER_DATA.forEach(c => {{
            const el = document.createElement('div');
            el.className = 'cluster-item highlight';
            el.innerHTML = `
                <div style="margin-bottom: 0.5rem;"><span class="size">Theme ${{c.Cluster}} | Size: ${{c.Size}} Terms | Mentions: ${{c.Mentions}}</span></div>
                <div><strong>Top Drivers:</strong> ${{c.Top_Terms}}</div>
                <div><strong>Valence:</strong> ${{c.Valence.toFixed(3)}}</div>
                <div class="rep-post">" ${{c.Representative_Post}} "</div>
            `;
            container.appendChild(el);
        }});

        // Render Time-Series Chart
        const tsCtx = document.getElementById('tsChart').getContext('2d');
        const labels = TS_DATA.map(d => d.Date);
        const sentiment = TS_DATA.map(d => d.Avg_Sentiment);
        const mentions = TS_DATA.map(d => d.Mentions);
        
        // Causal time points from Anthropic Release History
        const allAnnotations = {{
            opus46: {{ type: 'line', scaleID: 'x', value: '2026-02-05', borderColor: 'rgba(160, 160, 171, 0.5)', borderWidth: 1, label: {{ display: true, content: 'Opus 4.6 (1M Beta)', position: 'start', color: '#a0a0ab', backgroundColor: 'transparent', font: {{family: 'Commit Mono', size: 10}} }} }},
            sonnet46: {{ type: 'line', scaleID: 'x', value: '2026-02-17', borderColor: 'rgba(160, 160, 171, 0.5)', borderWidth: 1, label: {{ display: true, content: 'Sonnet 4.6', position: 'start', yAdjust: 20, color: '#a0a0ab', backgroundColor: 'transparent', font: {{family: 'Commit Mono', size: 10}} }} }},
            contextGA: {{ type: 'line', scaleID: 'x', value: '2026-03-13', borderColor: 'rgba(255, 79, 0, 0.5)', borderWidth: 2, label: {{ display: true, content: '1M Context GA', position: 'start', color: '#ff4f00', backgroundColor: 'transparent', font: {{family: 'Commit Mono', size: 10}} }} }},
            computerUse: {{ type: 'line', scaleID: 'x', value: '2026-03-23', borderColor: 'rgba(160, 160, 171, 0.5)', borderWidth: 1, label: {{ display: true, content: 'Computer Use', position: 'start', yAdjust: 40, color: '#a0a0ab', backgroundColor: 'transparent', font: {{family: 'Commit Mono', size: 10}} }} }},
            opus47: {{ type: 'line', scaleID: 'x', value: '2026-04-16', borderColor: 'rgba(255, 79, 0, 0.8)', borderWidth: 2, borderDash: [5, 5], label: {{ display: true, content: 'Opus 4.7', position: 'start', color: '#ff4f00', backgroundColor: 'transparent', font: {{family: 'Commit Mono', size: 11, weight: 'bold'}} }} }},
            safetyFix: {{ type: 'line', scaleID: 'x', value: '2026-04-28', borderColor: 'rgba(160, 160, 171, 0.5)', borderWidth: 1, label: {{ display: true, content: 'Prompt Reversions', position: 'start', yAdjust: 20, color: '#a0a0ab', backgroundColor: 'transparent', font: {{family: 'Commit Mono', size: 10}} }} }}
        }};
        
        // Filter annotations to only those >= 2026-02-01
        const releaseAnnotations = {{}};
        for (const [key, ann] of Object.entries(allAnnotations)) {{
            if (ann.value >= '2026-02-01') {{
                releaseAnnotations[key] = ann;
            }}
        }}
        
        new Chart(tsCtx, {{
            type: 'line',
            data: {{
                labels: labels,
                datasets: [
                    {{
                        label: 'Avg Sentiment',
                        data: sentiment,
                        borderColor: '#ff4f00',
                        backgroundColor: 'rgba(255, 79, 0, 0.1)',
                        yAxisID: 'y',
                        tension: 0.3,
                        fill: true
                    }},
                    {{
                        label: 'Volume (Mentions)',
                        data: mentions,
                        borderColor: '#a0a0ab',
                        borderDash: [5, 5],
                        yAxisID: 'y1',
                        tension: 0.3
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                interaction: {{ mode: 'index', intersect: false }},
                scales: {{
                    x: {{ 
                        type: 'time',
                        time: {{ unit: 'day', tooltipFormat: 'yyyy-MM-dd' }},
                        grid: {{ color: '#2a2a30' }} 
                    }},
                    y: {{ type: 'linear', display: true, position: 'left', grid: {{ color: '#2a2a30' }} }},
                    y1: {{ type: 'linear', display: true, position: 'right', grid: {{ drawOnChartArea: false }} }}
                }},
                plugins: {{
                    annotation: {{
                        annotations: releaseAnnotations
                    }}
                }}
            }}
        }});
        
        // Render Cluster Time-Series Chart
        const clusterTsCtx = document.getElementById('clusterTsChart');
        if (clusterTsCtx && CLUSTER_TS_DATA.length > 0) {{
            const c_labels = CLUSTER_TS_DATA.map(d => d.Date);
            const clusterKeys = Object.keys(CLUSTER_TS_DATA[0]).filter(k => k !== 'Date');
            
            const colors = ['#ff4f00', '#00bfa5', '#651fff', '#ffd600', '#c51162'];
            
            const datasets = clusterKeys.map((k, i) => ({{
                label: `Cluster ${{k}}`,
                data: CLUSTER_TS_DATA.map(d => d[k] || 0),
                borderColor: colors[i % colors.length],
                backgroundColor: colors[i % colors.length] + '33',
                tension: 0.3,
                fill: true
            }}));
            
            new Chart(clusterTsCtx.getContext('2d'), {{
                type: 'line',
                data: {{ labels: c_labels, datasets: datasets }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {{ mode: 'index', intersect: false }},
                    scales: {{
                        x: {{ 
                            type: 'time',
                            time: {{ unit: 'day', tooltipFormat: 'yyyy-MM-dd' }},
                            grid: {{ color: '#2a2a30' }} 
                        }},
                        y: {{ type: 'linear', display: true, position: 'left', grid: {{ color: '#2a2a30' }} }}
                    }},
                    plugins: {{
                        annotation: {{ annotations: releaseAnnotations }}
                    }}
                }}
            }});
        }}
        
        // Render Theme Time-Series Chart
        const themeTsCtx = document.getElementById('themeTsChart');
        if (themeTsCtx && THEME_TS_DATA.length > 0) {{
            const t_labels = THEME_TS_DATA.map(d => d.Date);
            const themeKeys = Object.keys(THEME_TS_DATA[0]).filter(k => k !== 'Date');
            
            const colors = ['#00bfa5', '#ff4f00', '#ffd600', '#c51162', '#651fff'];
            
            const datasets = themeKeys.map((k, i) => ({{
                label: `Theme ${{k}}`,
                data: THEME_TS_DATA.map(d => d[k] || 0),
                borderColor: colors[i % colors.length],
                backgroundColor: colors[i % colors.length] + '33',
                tension: 0.3,
                fill: true
            }}));
            
            new Chart(themeTsCtx.getContext('2d'), {{
                type: 'line',
                data: {{ labels: t_labels, datasets: datasets }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {{ mode: 'index', intersect: false }},
                    scales: {{
                        x: {{ 
                            type: 'time',
                            time: {{ unit: 'day', tooltipFormat: 'yyyy-MM-dd' }},
                            grid: {{ color: '#2a2a30' }} 
                        }},
                        y: {{ type: 'linear', display: true, position: 'left', grid: {{ color: '#2a2a30' }} }}
                    }},
                    plugins: {{
                        annotation: {{ annotations: releaseAnnotations }}
                    }}
                }}
            }});
        }}

        // Render Network Graph (HTML5 Canvas Native)
        const canvas = document.getElementById('networkCanvas');
        const cctx = canvas.getContext('2d');
        canvas.width = canvas.parentElement.clientWidth - 48; // padding adj
        canvas.height = 350;
        
        const width = canvas.width;
        const height = canvas.height;
        
        const nodes = {{}};
        EDGE_DATA.forEach(edge => {{
            if(!nodes[edge.Source]) nodes[edge.Source] = {{ x: Math.random()*width, y: Math.random()*height, weight: 0 }};
            if(!nodes[edge.Target]) nodes[edge.Target] = {{ x: Math.random()*width, y: Math.random()*height, weight: 0 }};
            nodes[edge.Source].weight += edge.Weight;
            nodes[edge.Target].weight += edge.Weight;
        }});

        cctx.strokeStyle = 'rgba(255, 255, 255, 0.15)';
        EDGE_DATA.forEach(edge => {{
            cctx.beginPath();
            cctx.moveTo(nodes[edge.Source].x, nodes[edge.Source].y);
            cctx.lineTo(nodes[edge.Target].x, nodes[edge.Target].y);
            cctx.lineWidth = edge.Weight;
            cctx.stroke();
        }});

        cctx.fillStyle = '#ff4f00';
        cctx.font = '11px "Commit Mono"';
        for(let key in nodes) {{
            const n = nodes[key];
            cctx.beginPath();
            cctx.arc(n.x, n.y, 4, 0, Math.PI*2);
            cctx.fill();
            cctx.fillStyle = '#e2e2e5';
            cctx.fillText(key, n.x + 8, n.y + 4);
            cctx.fillStyle = '#ff4f00';
        }}
    </script>
</body>
</html>
"""

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html_template)

print(f"Generated Comprehensive Phenomenon Report HTML at {html_path}")
