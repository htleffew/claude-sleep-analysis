import pandas as pd
import numpy as np
import os
import warnings
import regex
from collections import defaultdict, Counter
import networkx as nx
from networkx.algorithms import community
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
import math

warnings.filterwarnings('ignore')

data_dir = 'data/'
csv_path = os.path.join(data_dir, 'praw_sleep_analysis_final.csv')
fallback_path = os.path.join(data_dir, 'praw_sleep_analysis_final_fallback.csv')

if os.path.exists(fallback_path):
    csv_path = fallback_path

output_dir = 'deliverables/'
os.makedirs(output_dir, exist_ok=True)

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Downloading spacy model...")
    os.system("python -m spacy download en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# Core anchors
anomaly_anchors = {'sleep', 'rest', 'bed', 'bedtime', 'bed-time', 'asleep', 'nap', 'tired', 'exhausted'}
actor_anchors = {'claude', 'ai', 'bot', 'model', 'sonnet', 'opus', 'anthropic', 'he', 'it', 'llm'}
WINDOW_SIZE = 10

analyzer = SentimentIntensityAnalyzer()

# Stopwords for N-grams and TF-IDF
stop_words = set(spacy.lang.en.stop_words.STOP_WORDS)
stop_words.update(['claude', 'anthropic', 'ai', 'like', 'just', 'im', 'dont', 'tell', 'tells', 'told', 'reddit', 'post', 'edit', 'https'])

def load_data():
    if not os.path.exists(csv_path):
        return pd.DataFrame()
    df = pd.read_csv(csv_path)
    df['createdAt'] = pd.to_datetime(df['createdAt'])
    return df

def clean_text(text):
    if pd.isna(text): return ""
    text = str(text).lower()
    text = regex.sub(r'http\S+', '', text)
    return text.strip()

def passes_sensitive_criteria(sent):
    has_anomaly = False
    has_actor = False
    for token in sent:
        lemma = token.lemma_.lower()
        text = token.lower_
        if lemma in anomaly_anchors or text in anomaly_anchors:
            has_anomaly = True
        if lemma in actor_anchors or text in actor_anchors:
            has_actor = True
    return has_anomaly and has_actor

def regex_tokenize(text):
    # Use regex to tokenize, keeping hashtags, numbers, emojis intact
    tokens = regex.findall(r'\#[\w\d]+|\p{Emoji}|\d+(?:\.\d+)?|\w+', str(text).lower(), regex.UNICODE)
    
    # Filter stopwords and short terms
    cleaned = []
    for t in tokens:
        if t not in stop_words and len(t) > 1:
            cleaned.append(t)
    return cleaned

def generate_ngrams(tokens, n):
    return [' '.join(tokens[i:i+n]) for i in range(len(tokens)-n+1)]

def deep_nlp_pipeline(df, report_file):
    print("\n--- Deep Analysis Pipeline (Juggernaut Protocol) ---")
    
    valid_indices = set()
    total_processed = 0
    co_occurrences = defaultdict(int)
    valid_sentences = []
    
    for idx, row in df.iterrows():
        text = clean_text(row['body'])
        if not text: continue
        doc = nlp(text)
        
        passed_sentence = False
        for sent in doc.sents:
            if passes_sensitive_criteria(sent):
                passed_sentence = True
                
                tokens = [token for token in sent]
                anchor_indices = [i for i, t in enumerate(tokens) if t.lower_ in anomaly_anchors or t.lemma_.lower() in anomaly_anchors]
                
                if anchor_indices:
                    valid_sentences.append({'id': idx, 'text': sent.text, 'original_body': row['body'], 'createdAt': row['createdAt']})
                    for anchor_idx in anchor_indices:
                        start_idx = max(0, anchor_idx - WINDOW_SIZE)
                        end_idx = min(len(tokens), anchor_idx + WINDOW_SIZE + 1)
                        window_tokens = tokens[start_idx:end_idx]
                        
                        context_terms = [
                            t.lemma_ for t in window_tokens 
                            if t.pos_ in ['NOUN', 'VERB', 'ADJ'] 
                            and t.lemma_ not in stop_words 
                            and len(t.lemma_) > 2
                            and t.i != anchor_idx
                        ]
                        
                        for i in range(len(context_terms)):
                            for j in range(i + 1, len(context_terms)):
                                t1, t2 = sorted([context_terms[i], context_terms[j]])
                                co_occurrences[(t1, t2)] += 1
                                
        if passed_sentence:
            valid_indices.add(idx)
            total_processed += 1

    anomaly_df = df.loc[list(valid_indices)].copy()
    
    # 1. N-Gram Generation (Segmented Pre vs Post Opus 4.7)
    print("Generating Segmented N-Grams...")
    opus_date = pd.Timestamp('2026-04-16')
    pre_df = anomaly_df[anomaly_df['createdAt'] < opus_date]
    post_df = anomaly_df[anomaly_df['createdAt'] >= opus_date]
    
    def extract_ngrams_and_save(segment_df, prefix):
        all_unigrams, all_bigrams, all_trigrams = [], [], []
        for text in segment_df['body']:
            t = clean_text(text)
            tokens = regex_tokenize(t)
            all_unigrams.extend(generate_ngrams(tokens, 1))
            all_bigrams.extend(generate_ngrams(tokens, 2))
            all_trigrams.extend(generate_ngrams(tokens, 3))
            
        uni_count = Counter(all_unigrams).most_common(20)
        bi_count = Counter(all_bigrams).most_common(20)
        tri_count = Counter(all_trigrams).most_common(20)
        
        ngram_data = []
        for ngram, count in uni_count: ngram_data.append({'Type': 'Unigram', 'Term': ngram, 'Count': count})
        for ngram, count in bi_count: ngram_data.append({'Type': 'Bigram', 'Term': ngram, 'Count': count})
        for ngram, count in tri_count: ngram_data.append({'Type': 'Trigram', 'Term': ngram, 'Count': count})
        pd.DataFrame(ngram_data).to_csv(os.path.join(output_dir, f'ngram_frequencies_{prefix}.csv'), index=False)

    extract_ngrams_and_save(pre_df, 'pre')
    extract_ngrams_and_save(post_df, 'post')
    
    # 2. TF-IDF Vectorization (Segmented)
    print("Extracting Segmented TF-IDF...")
    def extract_tfidf_and_save(segment_df, prefix):
        corpus = [' '.join(regex_tokenize(clean_text(text))) for text in segment_df['body']]
        if len(corpus) > 0:
            vectorizer = TfidfVectorizer(max_features=50, stop_words=list(stop_words))
            X = vectorizer.fit_transform(corpus)
            tfidf_scores = zip(vectorizer.get_feature_names_out(), np.asarray(X.sum(axis=0)).ravel())
            sorted_scores = sorted(tfidf_scores, key=lambda x: x[1], reverse=True)
            tfidf_data = [{'Term': t, 'Score': s} for t, s in sorted_scores]
            pd.DataFrame(tfidf_data).to_csv(os.path.join(output_dir, f'tfidf_top_terms_{prefix}.csv'), index=False)
        else:
            pd.DataFrame(columns=['Term', 'Score']).to_csv(os.path.join(output_dir, f'tfidf_top_terms_{prefix}.csv'), index=False)

    extract_tfidf_and_save(pre_df, 'pre')
    extract_tfidf_and_save(post_df, 'post')
    
    # 3. Time-Series Sentiment
    print("Computing Time-Series Sentiment...")
    anomaly_df['Date'] = anomaly_df['createdAt'].dt.date
    anomaly_df['Sentiment'] = anomaly_df['body'].apply(lambda x: analyzer.polarity_scores(x)['compound'])
    
    ts_df = anomaly_df.groupby('Date').agg(
        Mentions=('body', 'count'),
        Avg_Sentiment=('Sentiment', 'mean')
    ).reset_index()
    ts_df = ts_df.sort_values('Date')
    ts_df.to_csv(os.path.join(output_dir, 'sentiment_timeseries.csv'), index=False)
    
    
    # 4. User Engagement & Structural Dispersion (On the FULL corpus, not just the strict filter)
    print("Computing User Engagement Metrics...")
    total_posts = len(df[df['type'] == 'post'])
    
    top_level_comments = len(df[(df['type'] == 'comment') & (df['parent_id'].astype(str).str.startswith('t3_'))])
    nested_replies = len(df[(df['type'] == 'comment') & (df['parent_id'].astype(str).str.startswith('t1_'))])
    
    subreddits = df['subreddit'].value_counts().to_dict()
    
    engagement_data = {
        'total_original_posts': total_posts,
        'top_level_comments': top_level_comments,
        'nested_replies': nested_replies,
        'unique_subreddits_count': len(subreddits),
        'subreddit_breakdown': subreddits
    }
    
    import json
    with open(os.path.join(output_dir, 'engagement_metrics.json'), 'w') as f:
        json.dump(engagement_data, f)

    return co_occurrences, valid_sentences, anomaly_df

def network_community_detection(co_occurrences, valid_sentences):
    min_weight = 2
    edges = [(k[0], k[1], v) for k, v in co_occurrences.items() if v >= min_weight]
    if not edges: return
        
    G = nx.Graph()
    G.add_weighted_edges_from(edges)
    communities = community.louvain_communities(G, weight='weight', resolution=1.0)
    
    community_data = []
    for i, comm in enumerate(communities):
        subgraph = G.subgraph(comm)
        centrality = nx.degree_centrality(subgraph)
        top_terms = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:10]
        top_term_names = [t[0] for t in top_terms]
        
        comm_sentences = []
        original_bodies = []
        for sent in valid_sentences:
            words = set(regex.findall(r'\w+', sent['text'].lower()))
            overlap = words.intersection(set(top_term_names))
            if len(overlap) >= 1:
                comm_sentences.append(sent['text'])
                original_bodies.append(sent['original_body'])
                
        avg_sentiment = 0
        if comm_sentences:
            scores = [analyzer.polarity_scores(s)['compound'] for s in comm_sentences]
            avg_sentiment = np.mean(scores)
        
        rep_post = original_bodies[0] if original_bodies else ""
        community_data.append({
            'Cluster': i+1,
            'Size': len(comm),
            'Top_Terms': ', '.join(top_term_names),
            'Mentions': len(comm_sentences),
            'Valence': avg_sentiment,
            'Representative_Post': rep_post
        })
        
        # Track cluster timeseries
        for sent in valid_sentences:
            words = set(regex.findall(r'\w+', sent['text'].lower()))
            overlap = words.intersection(set(top_term_names))
            if len(overlap) >= 1:
                sent['Cluster'] = i+1
                
    pd.DataFrame(community_data).to_csv(os.path.join(output_dir, 'inductive_themes.csv'), index=False)
    
    # Generate Cluster Timeseries
    ts_rows = []
    for sent in valid_sentences:
        if 'Cluster' in sent:
            date_str = pd.to_datetime(sent['createdAt']).date()
            ts_rows.append({'Date': date_str, 'Cluster': sent['Cluster']})
            
    if ts_rows:
        cluster_ts_df = pd.DataFrame(ts_rows)
        pivot_ts = cluster_ts_df.groupby(['Date', 'Cluster']).size().unstack(fill_value=0).reset_index()
        pivot_ts.to_csv(os.path.join(output_dir, 'cluster_timeseries.csv'), index=False)
    
    edge_data = [{'Source': u, 'Target': v, 'Weight': d['weight']} for u, v, d in G.edges(data=True)]
    pd.DataFrame(edge_data).to_csv(os.path.join(output_dir, 'network_edges.csv'), index=False)

def semantic_theme_extraction(anomaly_df):
    print("Extracting Semantic Themes (LDA)...")
    corpus = [' '.join(regex_tokenize(clean_text(text))) for text in anomaly_df['body']]
    if not corpus: return
    
    vectorizer = CountVectorizer(max_features=1000, stop_words=list(stop_words))
    X = vectorizer.fit_transform(corpus)
    
    n_components = 5
    lda = LatentDirichletAllocation(n_components=n_components, random_state=42)
    doc_topic_dists = lda.fit_transform(X)
    
    feature_names = vectorizer.get_feature_names_out()
    themes = []
    for topic_idx, topic in enumerate(lda.components_):
        top_features_ind = topic.argsort()[:-11:-1]
        top_features = [feature_names[i] for i in top_features_ind]
        themes.append({
            'Theme': topic_idx + 1,
            'Top_Terms': ', '.join(top_features)
        })
    pd.DataFrame(themes).to_csv(os.path.join(output_dir, 'lda_themes.csv'), index=False)
    
    # Theme Timeseries
    anomaly_df['Dominant_Theme'] = np.argmax(doc_topic_dists, axis=1) + 1
    anomaly_df['Date'] = anomaly_df['createdAt'].dt.date
    theme_ts = anomaly_df.groupby(['Date', 'Dominant_Theme']).size().unstack(fill_value=0).reset_index()
    theme_ts.to_csv(os.path.join(output_dir, 'theme_timeseries.csv'), index=False)

def calculate_statistical_dependencies(co_occurrences, valid_sentences):
    print("Calculating NMPI & LogDice...")
    
    # Calculate word frequencies
    word_freqs = defaultdict(int)
    total_words = 0
    
    for sent in valid_sentences:
        tokens = [t for t in regex.findall(r'\w+', sent['text'].lower()) if len(t) > 2 and t not in stop_words]
        for t in tokens:
            word_freqs[t] += 1
            total_words += 1
            
    total_pairs = sum(co_occurrences.values())
    if total_pairs == 0 or total_words == 0: return
    
    metrics = []
    for (w1, w2), f_xy in co_occurrences.items():
        if f_xy < 3: continue
        
        f_x = word_freqs.get(w1, 0)
        f_y = word_freqs.get(w2, 0)
        
        if f_x == 0 or f_y == 0: continue
        
        p_xy = f_xy / total_pairs
        p_x = f_x / total_words
        p_y = f_y / total_words
        
        # PMI = log2(P(x,y) / (P(x)*P(y)))
        pmi = math.log2(p_xy / (p_x * p_y)) if p_xy > 0 else 0
        
        # NMPI = PMI / -log2(P(x,y))
        nmpi = pmi / -math.log2(p_xy) if p_xy > 0 else 0
        
        # LogDice = 14 + log2(2 * f(x,y) / (f(x) + f(y)))
        logdice = 14 + math.log2((2 * f_xy) / (f_x + f_y))
        
        metrics.append({
            'Term_1': w1,
            'Term_2': w2,
            'Co_Occurrence': f_xy,
            'NMPI': round(nmpi, 4),
            'LogDice': round(logdice, 4)
        })
        
    metrics_df = pd.DataFrame(metrics).sort_values(by='LogDice', ascending=False).head(50)
    metrics_df.to_csv(os.path.join(output_dir, 'collocation_metrics.csv'), index=False)

if __name__ == "__main__":
    df = load_data()
    if not df.empty:
        with open(os.path.join(output_dir, 'inductive_exploration_log.txt'), 'w', encoding='utf-8') as f:
            f.write("Juggernaut-Level Deep Analysis Initiated.\n")
        co_occurrences, valid_sentences, anomaly_df = deep_nlp_pipeline(df, None)
        network_community_detection(co_occurrences, valid_sentences)
        semantic_theme_extraction(anomaly_df)
        calculate_statistical_dependencies(co_occurrences, valid_sentences)
