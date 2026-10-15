"""QA-only harness: runs figure scripts with Figure.savefig replaced by (text-overlap / out-of-figure check, NO write), so nothing on disk changes.
usage: qa_figures.py script1.py script2.py ...   (scripts live in the egress folder)"""
import sys, runpy, matplotlib
matplotlib.use("Agg")
import matplotlib.figure as mf
import os as _os; sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from figlabels import qa
def _sv(self, fname, *a, **k):
    qa(self, str(fname).split("/")[-1])
mf.Figure.savefig = _sv
for s in sys.argv[1:]:
    print("== running", s)
    runpy.run_path(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), s), run_name="__main__")
