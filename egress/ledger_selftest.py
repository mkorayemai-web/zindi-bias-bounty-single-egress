"""Self-test of numbers_ledger.py: proves the ledger can FAIL. Corrupts a copy of the draft in known places (and, separately, one quoted value inside a copy of the ledger),
runs the ledger in test mode (outputs go to a scratch directory, never into the lane) and requires that exactly the expected checks change status and nothing else.
usage: python ledger_selftest.py   -> prints 'SELFTEST PASS' or the differences; exit code 1 on failure."""
import os, sys, subprocess, tempfile, shutil
import pandas as pd
import os as _os; sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from common import LANE
SCRIPT = f"{LANE}/egress/numbers_ledger.py"; TMP = tempfile.mkdtemp(dir=os.environ.get("TMPDIR"))
orig = open(f"{LANE}/DISCOVERY_DRAFT.md").read()
def run(draft_text, script=SCRIPT, tag="x"):
    d = f"{TMP}/{tag}"; os.makedirs(d); p = f"{d}/draft.md"; open(p, "w").write(draft_text)
    subprocess.run([sys.executable, script], env=dict(os.environ, LEDGER_TEST_DRAFT=p, LEDGER_TEST_OUT=d), capture_output=True, text=True)
    return {r.id: r.status for r in pd.read_csv(f"{d}/numbers_ledger.csv").itertuples() if r.status != "OK"}
MUT = [("17.0 M dwellings", "17.1 M dwellings", ["F1.01"]), ("**2.15x**", "**2.16x**", ["W.03"]), ("95 % CI 1.86-2.57, resampling", "95 % CI 1.86-2.58, resampling", ["W.04", "W.05", "W.06", "W.07", "W.08"]),
       ("98.3 % of S30 dwellings", "98.9 % of S30 dwellings", ["I.11"]), ("Buildings of 35 m2+", "Buildings of 50 m2+", ["P.01", "P.02"]), ("(E. Washington about 1 minute)", "(E. Washington about 5 minutes)", ["R.02"])]
mut = orig; expect = set()
for a, b, ids in MUT:
    assert orig.count(a) == 1, f"mutation anchor not unique in the draft: {a!r}"; mut = mut.replace(a, b); expect |= set(ids)
base = run(orig, tag="base"); got = run(mut, tag="mut"); changed = {k for k in got if base.get(k) != got[k]} | {k for k in base if k not in got}
ok1 = changed == expect and all(got[k] == "DRAFT-TEXT-MISSING" for k in expect)
print(f"text corruption: {len(MUT)} edits in the draft -> expected failing checks {sorted(expect)}\n  newly failing: {sorted(changed)}  => {'detected exactly' if ok1 else 'MISMATCH BETWEEN EXPECTED AND OBSERVED'}")
src = open(SCRIPT).read(); a = 'add("F1.03", "21.3 % reach the arterial network", 21.3,'; assert src.count(a) == 1
open(f"{TMP}/ledger_wrong_value.py", "w").write(src.replace(a, a.replace("21.3,", "21.4,")))
got2 = run(orig, script=f"{TMP}/ledger_wrong_value.py", tag="wrong"); new2 = {k: v for k, v in got2.items() if base.get(k) != v}; ok2 = new2 == {"F1.03": "MISMATCH"}
print(f"value corruption: quoted 21.4 instead of 21.3 in a copy of the ledger -> newly failing {new2}  => {'detected' if ok2 else 'NOT DETECTED'}")
print("baseline failures on the unmodified draft (should be empty once PREFLIGHT_eastern-wa.txt exists):", sorted(base))
shutil.rmtree(TMP, ignore_errors=True); print("SELFTEST PASS" if (ok1 and ok2) else "SELFTEST FAIL"); sys.exit(0 if (ok1 and ok2) else 1)
