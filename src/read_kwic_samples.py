import pandas as pd
from pathlib import Path

OUT = Path(r"C:\Users\drhea\repos\claude-sleep-analysis\deliverables\phase_2_rerun\sleep_kwic_network")

seeds = ["sleep","rest","break","tired","tomorrow","tonight","bed","exhausted","late",
         "midnight","paternalistic","bedtime","moralizing"]

for seed in seeds:
    f = OUT / f"kwic_{seed}_w10.csv"
    df = pd.read_csv(f)
    print(f"=== {seed} w10 (n={len(df)}) ===")
    for _, r in df.iterrows():
        lc = str(r["left_context"])
        rc = str(r["right_context"])
        sub = str(r["subreddit"])
        print(f"  [{sub}] {lc} **{seed}** {rc}")
    print()
