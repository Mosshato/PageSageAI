import json
import random
import os
# v2 — suporta JSON array SI JSONL

# ─────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────
INPUT_FILE  = "data.jsonl"       # fisierul tau original
OUTPUT_FILE = "data_converted.jsonl"

INSTRUCTION = (
    "You are a ManimCE expert. Given an animation description, "
    "generate complete, valid ManimCE Python code using the Community Edition API. "
    "Output only the Python class definition, no explanations or markdown."
)

# ─────────────────────────────────────────
# 1. CITIRE — suporta ambele formate
#    - JSON array:  [ {...}, {...} ]
#    - JSONL:       {...}\n{...}\n
# ─────────────────────────────────────────
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    content = f.read().strip()

if content.startswith("["):
    rows = json.loads(content)
    print(f"✅ Format detectat: JSON array")
else:
    rows = [json.loads(line) for line in content.splitlines() if line.strip()]
    print(f"✅ Format detectat: JSONL")

print(f"✅ Citite: {len(rows)} rows")

# ─────────────────────────────────────────
# 2. VALIDARE — verifica ca fiecare row are 'input' si 'label'
# ─────────────────────────────────────────
missing = [i for i, r in enumerate(rows) if "input" not in r or "label" not in r]
if missing:
    print(f"⚠️  {len(missing)} rows fara 'input' sau 'label': {missing[:10]}")
    rows = [r for r in rows if "input" in r and "label" in r]
    print(f"   → Ramase dupa filtrare: {len(rows)} rows")

# ─────────────────────────────────────────
# 3. CONVERSIE
# ─────────────────────────────────────────
converted = []
for row in rows:
    converted.append({
        "instruction": INSTRUCTION,
        "input":       row["input"].strip(),
        "output":      row["label"].strip(),
    })

print(f"✅ Convertite: {len(converted)} rows")

# ─────────────────────────────────────────
# 4. SHUFFLE RANDOM (important pentru split corect)
# ─────────────────────────────────────────
random.seed(42)  # seed fix → rezultate reproductibile
random.shuffle(converted)

# ─────────────────────────────────────────
# 5. SPLIT 80 / 10 / 10
# ─────────────────────────────────────────
n     = len(converted)
n_tr  = int(n * 0.80)
n_val = int(n * 0.10)

train = converted[:n_tr]
val   = converted[n_tr : n_tr + n_val]
test  = converted[n_tr + n_val :]

print(f"\n📊 Split:")
print(f"   Train : {len(train)} rows  (80%)")
print(f"   Val   : {len(val)}  rows  (10%)")
print(f"   Test  : {len(test)} rows  (10%)")

# ─────────────────────────────────────────
# 6. SALVARE
# ─────────────────────────────────────────
def save_jsonl(data, path):
    with open(path, "w", encoding="utf-8") as f:
        for row in data:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"   💾 Salvat: {path}  ({os.path.getsize(path) / 1024:.1f} KB)")

save_jsonl(converted, OUTPUT_FILE)        # tot dataset-ul convertit
save_jsonl(train,     "train.jsonl")
save_jsonl(val,       "val.jsonl")
save_jsonl(test,      "test.jsonl")

# ─────────────────────────────────────────
# 7. VERIFICARE — afiseaza primul row
# ─────────────────────────────────────────
print("\n🔍 Preview primul row din train:")
first = train[0]
print(f"  KEYS       : {list(first.keys())}")
print(f"  INSTRUCTION: {first['instruction'][:80]}...")
print(f"  INPUT      : {first['input'][:120]}...")
print(f"  OUTPUT     : {first['output'][:120]}...")

print("\n✅ Conversie completa!")