"""Compare the two pilot runs with what is known about their records.

Pilot A holds the 24 test-set studies: every one should be Include or Maybe.
Pilot B holds 25 records screened by hand during strategy work; agreement is reported per record.
"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def results(name):
    path = HERE / f"{name}.results.jsonl"
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


a = results("pilot_A_test_set")
lost = [r for r in a if r["decision"] == "Exclude"]
print(f"Pilot A: {len(a)} test-set studies; excluded {len(lost)}")
for r in lost:
    print(f"    {r['id']} {r['code']}: {r['reasoning']}")

hand = json.loads((HERE / "pilot_B_hand_decisions.json").read_text(encoding="utf-8"))
short = {"Include": "I", "Maybe": "M", "Exclude": "E"}
b = results("pilot_B_hand_coded")
agree = sum((short[r["decision"]] == "E") == (hand[r["id"]] == "E") for r in b)
print(f"Pilot B: {len(b)} records; agree on exclude vs keep for {agree}")
for r in b:
    llm, human = short[r["decision"]], hand[r["id"]]
    if llm != human:
        print(f"    {r['id']} hand {human} / LLM {llm} {r.get('code') or ''}: {r['reasoning']}")
