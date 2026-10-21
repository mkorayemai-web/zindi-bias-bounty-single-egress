"""Coverage classification for declared ledger inventory counts, not measurements.
Does not add ledger rows or change any analytical value/tolerance.
"""
import re
from quoted_sources import SOURCE_IDS

PATTERN = re.compile(r'all (?P<offline>\d+) offline ledger checks of printed\s+numbers pass at their printed precision \(the other (?P<quoted>\d+) quote external documents\)')


def coverage_metadata(draft, ledger_ids):
    ids=list(ledger_ids)
    counts={'offline':sum(cid not in SOURCE_IDS for cid in ids),
            'quoted':sum(cid in SOURCE_IDS for cid in ids)}
    meanings={'offline':'offline computational/source/parameter check inventory',
              'quoted':'externally quoted-document check inventory'}
    rows=[]
    for m in PATTERN.finditer(draft):
        for name in ('offline','quoted'):
            rows.append(dict(token=m.group(name),start=m.start(name),end=m.end(name),
                             kind='metadata/check-count (not a measured value)',meaning=meanings[name],
                             registered_count=counts[name],matches=int(m.group(name))==counts[name]))
    return rows


def platform_identifier_spans(draft):
    """Numeric fragments of architecture IDs are identifiers, not measurements."""
    spans=[]
    for m in re.finditer(r'\b(?:aarch64|arm64|x86(?:_64)?)\b',draft):
        for digits in re.finditer(r'\d+',m.group()):
            spans.append((m.start()+digits.start(),m.start()+digits.end()))
    return spans
