#!/usr/bin/env python3
"""Validate that the Purrtocol History Museum stays bound to Chronicle data."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


class MuseumError(ValueError):
    pass


def validate(chronicle: dict, html: str) -> dict:
    if '<div class="timeline canonical">' not in html:
        raise MuseumError("canonical timeline container missing")
    canonical = html.split('<div class="timeline canonical">', 1)[1].split('</div>\n</section>', 1)[0]

    found = re.findall(r'<article class="event [^"]*" data-pr="(\d+)" data-sha="([0-9a-f]{40})">', canonical)
    museum_rows = [(int(pr), sha) for pr, sha in found]
    expected = [(row['pr'], row['merge_sha']) for row in chronicle['canonical_events']]
    if museum_rows != expected:
        raise MuseumError(f"canonical museum rows differ from Chronicle: {museum_rows!r} != {expected!r}")

    for row in chronicle['canonical_events']:
        if row['chronicle_name'] not in canonical:
            raise MuseumError(f"missing projection label for PR #{row['pr']}")
        if row['title'] not in canonical:
            raise MuseumError(f"missing repository title for PR #{row['pr']}")
        if f"/pull/{row['pr']}" not in canonical:
            raise MuseumError(f"missing source link for PR #{row['pr']}")

    if 'data-pr="73"' in canonical:
        raise MuseumError("apocryphal PR #73 leaked into canonical gallery")
    if 'data-apocrypha-pr="73"' not in html:
        raise MuseumError("apocryphal PR #73 exhibit missing")

    prehistory = html.split('<section class="section prehistory">', 1)[1].split('</section>', 1)[0]
    for row in chronicle.get('prehistory', []):
        if f'data-pr="{row["pr"]}"' not in prehistory or row['merge_sha'] not in prehistory:
            raise MuseumError(f"prehistory PR #{row['pr']} exhibit mismatch")

    publication = chronicle.get('publication_model', {})
    if publication.get('self_reference_acknowledged') is not True:
        raise MuseumError("Chronicle publication model not acknowledged")
    if 'Snapshot ≠ Oracle.' not in html:
        raise MuseumError("museum must display snapshot-not-oracle boundary")

    coverage = chronicle['coverage']
    if str(coverage['through_pr']) not in html or coverage['elapsed_human'] not in html:
        raise MuseumError("coverage boundary is not surfaced")

    return {
        'canonical_exhibits': len(museum_rows),
        'prehistory_exhibits': len(chronicle.get('prehistory', [])),
        'apocrypha_exhibits': 1,
        'coverage_pr': coverage['through_pr'],
        'elapsed_human': coverage['elapsed_human'],
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument('--chronicle', required=True)
    p.add_argument('--museum', required=True)
    args = p.parse_args()
    chronicle = json.loads(Path(args.chronicle).read_text(encoding='utf-8'))
    html = Path(args.museum).read_text(encoding='utf-8')
    print(json.dumps(validate(chronicle, html), ensure_ascii=False, sort_keys=True))


if __name__ == '__main__':
    main()
