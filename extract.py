#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import re
import argparse
from dataclasses import dataclass
from typing import List, Optional


RE_OVERALL = re.compile(r"overall_confidence\s*=\s*([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)")
RE_ID = re.compile(r"(?:^|[,\s])id\s*=\s*(\d+)(?:$|[,\s])")


@dataclass
class Record:
    header: str
    seq: str
    overall: float
    rec_id: Optional[int] = None


def parse_fasta_like(text: str) -> List[Record]:
    """Parse LigandMPNN FASTA-like records containing overall_confidence."""
    records: List[Record] = []
    cur_header: Optional[str] = None
    cur_seq_parts: List[str] = []

    def flush():
        nonlocal cur_header, cur_seq_parts, records
        if cur_header is None:
            return
        seq = "".join(cur_seq_parts).replace(" ", "").replace("\t", "").strip()
        m = RE_OVERALL.search(cur_header)
        if m and seq:
            overall = float(m.group(1))
            mid = RE_ID.search(cur_header)
            rec_id = int(mid.group(1)) if mid else None
            records.append(Record(header=cur_header, seq=seq, overall=overall, rec_id=rec_id))

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith(">"):
            flush()
            cur_header = line[1:].strip()
            cur_seq_parts = []
        else:
            cur_seq_parts.append(line)

    flush()
    return records


def unique_top_records(records: List[Record], top_n: int) -> List[Record]:
    records = sorted(records, key=lambda r: r.overall, reverse=True)
    seen = set()
    unique_records = []
    for record in records:
        if record.seq in seen:
            continue
        seen.add(record.seq)
        unique_records.append(record)
        if len(unique_records) >= top_n:
            break
    return unique_records


def main():
    parser = argparse.ArgumentParser(
        description="Extract top-N unique-sequence overall_confidence records from LigandMPNN FASTA output."
    )
    parser.add_argument("-i", "--input", default="-", help="Input file path, or '-' for STDIN.")
    parser.add_argument("-n", "--top", type=int, default=5, help="Number of top unique sequences.")
    args = parser.parse_args()

    if args.input == "-":
        text = sys.stdin.read()
    else:
        with open(args.input, "r", encoding="utf-8") as handle:
            text = handle.read()

    records = parse_fasta_like(text)
    if not records:
        print("No records with overall_confidence found.", file=sys.stderr)
        sys.exit(1)

    top_records = unique_top_records(records, max(0, args.top))
    if not top_records:
        print("No unique records found.", file=sys.stderr)
        sys.exit(1)

    for rank, record in enumerate(top_records, start=1):
        record_id = "NA" if record.rec_id is None else str(record.rec_id)
        print(f"{rank}\t{record.overall:.6f}\t{record_id}\t{record.seq}")


if __name__ == "__main__":
    main()
