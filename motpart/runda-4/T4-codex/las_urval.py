"""Endast metadata: fryst urvalsregel för T4. Inga videor eller mätutfall läses."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SEED = 202611204
SOURCE = ROOT / "motpart/runda-4/1-datagrund/urval.json"
OLD = ROOT / "motpart/runda-3-opus/D-medielager/urval.json"
pool = json.loads(SOURCE.read_text(encoding="utf-8"))["valda"]
old = json.loads(OLD.read_text(encoding="utf-8"))
excluded = {x["klipp"].rsplit("-", 1)[0] for x in old["urval"] + old["holdout"]}
excluded |= {x.rsplit("-", 1)[0] for x in old["utvecklingsklipp"]}
excluded |= {"duepiani", "spanjorskansthlm", "kennysgelato2.0", "gelatonova"}
used = set()

def key(stage, kind, clip_id):
    return hashlib.sha256(f"{SEED}|{stage}|{kind}|{clip_id}".encode("utf-8")).hexdigest()

def draw(stage, kind, count):
    out = []
    for row in sorted((x for x in pool if x["typ"] == kind), key=lambda x: (key(stage, kind, x["id"]), x["id"])):
        if row["konto"] in used or row["konto"] in excluded:
            continue
        out.append({k: row[k] for k in ("id", "konto", "typ")})
        used.add(row["konto"])
        if len(out) == count:
            return out
    raise RuntimeError(f"Otillräckligt urval: {stage}, {kind}, {count}")

pairs = [draw("S3", kind, 2) for kind in (
    "direkt_tilltal", "direkt_tilltal", "matporr_och_process", "matporr_och_process",
    "relaterbar_sketch", "vardens_provsmakning")]
s2 = []
for kind, count in (("direkt_tilltal", 3), ("matporr_och_process", 3),
                    ("relaterbar_sketch", 2), ("vardens_provsmakning", 2), ("annat", 2)):
    s2.extend(draw("S2", kind, count))
refs = sorted(x["id"] for x in pool if x["konto"] not in used)
lines = SOURCE.read_text(encoding="utf-8").splitlines()
line_map = {x["id"]: next(i for i, line in enumerate(lines, 1) if f'"{x["id"]}"' in line) for x in pool}
result = {
    "seed": SEED,
    "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "old_selection_sha256": hashlib.sha256(OLD.read_bytes()).hexdigest(),
    "excluded_test_accounts": sorted(excluded),
    "step2": s2,
    "step3_pairs": pairs,
    "reference_ids": refs,
    "reference_account_count": len({x["konto"] for x in pool if x["konto"] not in used}),
    "source_lines": {x["id"]: line_map[x["id"]] for x in s2 + [r for p in pairs for r in p]},
}
assert len(used) == 24
print(json.dumps(result, ensure_ascii=False, indent=2))
