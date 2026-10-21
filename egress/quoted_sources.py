"""The nine quoted-document checks, separate from computational reproduction.

No network. --sources DIR accepts the documented ext/ layout below, or the same
three leaf filenames directly in DIR. Without an override, use repo/ext.
Missing documents retain SKIPPED-NO-SOURCE; supplied documents are checked using
the original ledger needles/patterns, never counted as computational passes.
"""
from pathlib import Path
import re

CHECKS = (
    ('Q.01', '4.0 persons per occupied second-home or visitor unit', 'q_sources/mammoth_eagle_lodge_deir_s3-8.txt', r'person/unit occupancy of 4\.0 was applied to all remaining visitor, second home', 'Mammoth Lakes Eagle Lodge Draft EIR s3.8 (SOURCES.md row 9)'),
    ('Q.02', 'occupied 49 % of the year', 'q_sources/mammoth_eagle_lodge_deir_s3-8.txt', r'occupied about 25\.7\s+weeks on average, or 49% of the year', 'Mammoth Lakes Eagle Lodge Draft EIR s3.8 (SOURCES.md row 9)'),
    ('Q.03', '34,265 persons', 'q_sources/mammoth_eagle_lodge_deir_s3-8.txt', r'average peak PAOT in 2004 was 34,265', 'Mammoth Lakes Eagle Lodge Draft EIR s3.8 (SOURCES.md row 9)'),
    ('Q.04', '7,259 residents', 'q_sources/mammoth_eagle_lodge_deir_s3-8.txt', r'approximately 7,259 people were\s+residents', 'Mammoth Lakes Eagle Lodge Draft EIR s3.8 (SOURCES.md row 9)'),
    ('Q.05', '51-64 % for condominiums and 43-75 % for mobile homes', 'q_sources/collier_lee_hes1987.htm', r'Condominium \(Conventional\) 51\.0 64\.0 Mobile Home 43\.0 75\.0', 'SW Florida RPC Hurricane Evacuation Study Update 1987 (SOURCES.md row 10)'),
    ('I.04', '927 occupied housing units per egress lane', 'nist_tn2252.txt', r'In Paradise, the OHU/Egress Lane ratio is 927', 'NIST TN 2252 (SOURCES.md row 5)'),
    ('Q.09', '(Eagle Lodge Draft EIR, 2006)', 'q_sources/mammoth_eagle_lodge_deir_s3-8.txt', r'Draft Environmental Impact Report.{0,400}2006|September 2006|2006012041', 'Mammoth EIR carries the year 2006'),
    ('Q.10', 'A 1987 Southwest Florida hurricane evacuation study', 'q_sources/collier_lee_hes1987.htm', r'1987', 'HES document is the 1987 update'),
    ('P.12', 'in the 2018 Camp Fire (NIST TN 2252)', 'nist_tn2252.txt', r'Camp Fire.{0,2000}2018|2018.{0,2000}Camp Fire', 'NIST TN 2252 is the 2018 Camp Fire case study'),
)
SOURCE_IDS = frozenset(c[0] for c in CHECKS)
BY_ID = {c[0]: c for c in CHECKS}


def document_path(relative, default_root, sources=None):
    root = Path(sources) if sources is not None else Path(default_root)
    nested, flat = root / relative, root / Path(relative).name
    return nested if nested.is_file() or not flat.is_file() else flat


def check_one(cid, draft, default_root, sources=None):
    _, needle, relative, pattern, source = BY_ID[cid]
    path = document_path(relative, default_root, sources)
    row = dict(id=cid, draft_text=needle, quoted=float('nan'), recomputed=float('nan'),
               tolerance=float('nan'), source=source, status='SKIPPED-NO-SOURCE')
    if not path.is_file():
        row['source'] = source + ' [source document not distributed with the repository: fetch it as listed in SOURCES.md]'
        return row
    try:
        text = re.sub(r'<[^>]+>', ' ', path.read_text(errors='ignore'))
        text = re.sub(r'\s+', ' ', text)
        okay = re.search(pattern, text, re.S) is not None
        row.update(recomputed=float(okay), status='OK' if needle in draft and okay else
                   ('DRAFT-TEXT-MISSING' if needle not in draft else 'MISMATCH'))
    except OSError as e:
        row.update(status='UNREADABLE-SOURCE', source=source + f' [{type(e).__name__}: {e}]')
    return row


def evaluate_sources(draft, default_root, sources=None):
    return [check_one(cid, draft, default_root, sources) for cid, *_ in CHECKS]


def summarize(rows):
    rows = list(rows)
    statuses = [r['status'] for r in rows]
    passed, skipped = statuses.count('OK'), statuses.count('SKIPPED-NO-SOURCE')
    return dict(total=len(rows), passed=passed, failed=len(rows)-passed-skipped,
                unverified=skipped, all_pass=bool(rows) and passed==len(rows))


def split_ledger(table):
    """Classify by explicit check IDs, NEVER by SKIPPED status or Q-prefix.

    Q.06-Q.08 are computed occupancy arithmetic and stay in HEADLINE. A skipped
    computational check also stays in HEADLINE and prevents a computational PASS.
    """
    if not table.id.is_unique or set(table.id) & SOURCE_IDS != SOURCE_IDS:
        raise ValueError('full ledger must contain each of the nine quoted-source IDs exactly once')
    mask = table.id.isin(SOURCE_IDS)
    return table.loc[~mask].copy(), table.loc[mask].copy()
