import pandas as pd
import matplotlib.pyplot as plt
import os

os.makedirs('figures', exist_ok=True)

# 1. Time-series
df_daily = pd.read_csv('deliverables/daily_aggregates.csv')
df_daily['Date'] = pd.to_datetime(df_daily['Date'])
df_daily = df_daily.sort_values('Date')

plt.figure(figsize=(10, 6))
plt.plot(df_daily['Date'], df_daily['N'], label='Total Posts', color='#2c3e50')
plt.plot(df_daily['Date'], df_daily['Nudges'], label='Sleep Nudge Detections', color='#e74c3c')
plt.title('Daily Reddit Discourse Volume & Sleep Nudge Detections (Apr-May 2026)')
plt.xlabel('Date')
plt.ylabel('Post Count')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('figures/daily_volume.png', dpi=300)
plt.close()

# 2. Bar chart of Violation Types
df_coded = pd.read_csv('deliverables/cases_coded_combined.csv')
counts = df_coded['code_violation_type'].value_counts()

plt.figure(figsize=(10, 6))
counts.plot(kind='bar', color='#3498db')
plt.title('Distribution of Sleep Nudge Role-Violation Types')
plt.xlabel('Violation Type')
plt.ylabel('Frequency')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig('figures/violation_types.png', dpi=300)
plt.close()

print("Generated Sleep figures in figures/")
