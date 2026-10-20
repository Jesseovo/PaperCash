"""Offline checks for public metadata, attribution, and failed-feed retention."""

from datetime import datetime
import sys
from pathlib import Path

import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import build_discovery as discovery


ATOM = '''<feed xmlns="http://www.w3.org/2005/Atom">
<entry><id>http://arxiv.org/abs/2610.12345v2</id>
<title> A real &amp; useful paper </title><author><name>Jane Doe</name></author>
<summary>One paragraph.\nAnother line.</summary><published>2026-10-19T12:00:00Z</published>
<updated>2026-10-20T12:00:00Z</updated><category term="cs.AI"/></entry></feed>'''


def crossref_item(doi='10.1234/example', title='A research paper'):
    return {'DOI': doi, 'title': [title], 'author': [{'given': 'Jane', 'family': 'Doe'}],
            'published': {'date-parts': [[2026, 7]]}, 'container-title': ['Journal of Testing'],
            'abstract': '<jats:p>A &amp; B.</jats:p>', 'volume': '2', 'page': '10-20'}


def parse_crossref(item):
    return discovery.parse_crossref({'message': {'items': [item]}}, 'health', 'crossref-health')[0]


def test_arxiv_preserves_attribution_and_marks_preprint():
    paper = discovery.parse_arxiv(ATOM, 'agents', 'arxiv-agents')[0]
    assert paper['arxiv_id'] == '2610.12345'
    assert paper['url'] == 'https://arxiv.org/abs/2610.12345'
    assert paper['published'] == '2026-10-19'
    assert paper['kind'] == 'preprint'
    assert '[EB/OL]' in paper['citations']['gb7714']
    assert '@misc{arxiv261012345,' in paper['citations']['bibtex']
    assert paper['url'] in paper['citations']['apa']
    assert paper['abstract'] == 'One paragraph. Another line.'


def test_partial_dates_are_not_invented_and_invalid_dates_rejected():
    assert discovery.partial_date([2026]) == '2026'
    assert discovery.partial_date([2026, 7]) == '2026-07'
    assert discovery.partial_date([2026, 2, 30]) == ''
    assert parse_crossref(crossref_item())['published'] == '2026-07'


def test_crossref_uses_doi_source_and_strips_markup():
    item = crossref_item()
    item['URL'] = 'javascript:alert(1)'
    paper = parse_crossref(item)
    assert paper['url'] == 'https://doi.org/10.1234/example'
    assert paper['abstract'] == 'A & B.'
    assert paper['authors'] == ['Jane Doe']
    assert '*Journal of Testing' not in paper['citations']['apa']
    assert discovery.safe_url('javascript:alert(1)') == ''
    assert discovery.safe_url('https://user:password@example.org') == ''


def test_missing_authors_and_abstract_are_not_fabricated():
    item = crossref_item()
    item.pop('author'); item.pop('abstract')
    paper = parse_crossref(item)
    assert paper['authors'] == []
    assert paper['abstract'] == ''


def test_dedupes_same_doi_and_preserves_all_topics():
    first = parse_crossref(crossref_item(doi='10.1234/EXAMPLE'))
    second = parse_crossref(crossref_item())
    second['topics'] = ['human']; second['feeds'] = ['crossref-human']
    merged = discovery.merge_papers([first, second])
    assert len(merged) == 1
    assert merged[0]['topics'] == ['health', 'human']
    assert merged[0]['feeds'] == ['crossref-health', 'crossref-human']


def test_same_title_different_doi_is_not_silently_dropped():
    first = parse_crossref(crossref_item('10.1234/one', 'Editorial'))
    second = parse_crossref(crossref_item('10.1234/two', 'Editorial'))
    assert len(discovery.merge_papers([first, second])) == 2
    assert first['citations']['bibtex'].splitlines()[0] != second['citations']['bibtex'].splitlines()[0]


def test_failure_retains_last_good_data_and_original_update_time():
    paper = discovery.parse_arxiv(ATOM, 'agents', 'arxiv-agents')[0]
    old_stamp = '2026-10-19T08:20:00+08:00'
    previous = {'papers': [paper], 'feeds': [{'id': 'arxiv-agents', 'updated_at': old_stamp}]}
    def unavailable(*args, **kwargs):
        raise requests.Timeout()
    snapshot = discovery.build_snapshot(previous, fetch=unavailable,
        now=datetime(2026, 10, 20, 8, 20, tzinfo=discovery.CST), pause=lambda _: None)
    assert snapshot['papers'][0]['id'] == paper['id']
    assert snapshot['feeds'][0]['status'] == 'stale'
    assert snapshot['feeds'][0]['updated_at'] == old_stamp
    assert snapshot['feeds'][1]['status'] == 'unavailable'
    assert snapshot['generated_at'] != old_stamp


def test_failure_without_snapshot_is_not_reported_as_success():
    def unavailable(*args, **kwargs):
        raise requests.ConnectionError()
    with pytest.raises(RuntimeError, match='All paper sources failed'):
        discovery.build_snapshot(fetch=unavailable, pause=lambda _: None)
