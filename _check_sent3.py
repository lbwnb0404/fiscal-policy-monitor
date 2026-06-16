"""Check sorted sentiment after fix"""
import json, glob
for path in sorted(glob.glob("data/reports/*.json")):
    with open(path, encoding="utf-8") as f:
        r = json.load(f)
    ss = r["sentiment_summary"]
    print(f'{r["report_id"]}: avg={ss["average_score"]:.2f} positive={ss["positive_count"]} neutral={ss["neutral_count"]} cautious={ss["cautious_count"]}')
    totals = {"积极": 0, "中性": 0, "谨慎": 0}
    for a in r.get("articles", []):
        an = a.get("analysis", {})
        totals[an.get("sentiment_label", "中性")] += 1
    print(f'  totals: {totals}')
