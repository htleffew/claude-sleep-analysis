import json
from pathlib import Path

with open(r"C:\Users\drhea\repos\claude-sleep-analysis\deliverables\phase_2_rerun\sleep_kwic_network\network_stats.json") as f:
    stats = json.load(f)

print("graph_nodes:", stats["graph_nodes"])
print("graph_edges:", stats["graph_edges"])
print("graph_density:", round(stats["graph_density"], 6))
print("lcc_nodes:", stats["lcc_nodes"])
print("lcc_edges:", stats["lcc_edges"])
print("\nlouvain:")
for res, d in stats["louvain"].items():
    nc = d["n_communities"]
    t = d["top10_sizes"]
    print(f"  res={res}: n_communities={nc}, top10_sizes={t}")

print("\nseed_post_hits:")
for s, c in stats["seed_post_hits"].items():
    print(f"  {s}: {c}")

print("\nthreshold_seeds:", stats["threshold_seeds_100"])

print("\nsubgraph_stats:")
for s, d in stats["subgraph_stats"].items():
    print(f"  {s}: {d}")

print("\ntop50 unigrams (first 30):")
items = list(stats["unigram_freq_top50"].items())[:30]
for t, c in items:
    print(f"  {t}: {c}")
