"""Build the public discovery snapshot from arXiv and Crossref metadata."""

from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta, timezone
import hashlib
import html
import json
from pathlib import Path
import re
import sys
import time
from urllib.parse import quote, urlparse
import xml.etree.ElementTree as ET

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts' / 'lib'))
from features.citation import format_apa, format_bibtex, format_gb7714
from schema import Paper

CST = timezone(timedelta(hours=8))
NS = {'a': 'http://www.w3.org/2005/Atom', 'x': 'http://arxiv.org/schemas/atom'}
TOPICS = [
    {'id': 'agents', 'label': 'AI 与 Agent', 'note': '语言、推理与智能体'},
    {'id': 'vision', 'label': '计算机视觉', 'note': '图像与多模态'},
    {'id': 'robotics', 'label': '机器人', 'note': '从感知到行动'},
    {'id': 'health', 'label': '医学与健康', 'note': '医学影像与机器学习'},
    {'id': 'human', 'label': '人机交互', 'note': '人与 AI 的相处方式'},
]
FEEDS = [
    ('arxiv-agents', 'agents', 'arXiv', 'cat:cs.AI OR cat:cs.CL'),
    ('arxiv-vision', 'vision', 'arXiv', 'cat:cs.CV'),
    ('arxiv-robotics', 'robotics', 'arXiv', 'cat:cs.RO'),
    ('crossref-health', 'health', 'Crossref', 'medical imaging machine learning'),
    ('crossref-human', 'human', 'Crossref', 'human AI interaction'),
]


def clean(value: str | None) -> str:
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', value or ''))).strip()


def safe_url(value: str | None) -> str:
    value = (value or '').replace('http://arxiv.org/', 'https://arxiv.org/')
    parsed = urlparse(value)
    return value if parsed.scheme == 'https' and parsed.netloc and not parsed.username else ''


def partial_date(parts: list) -> str:
    try:
        values = list(map(int, parts[:3]))
        if not values or not 1900 <= values[0] <= 2200:
            return ''
        date(values[0], values[1] if len(values) > 1 else 1,
             values[2] if len(values) > 2 else 1)
        return '-'.join([str(values[0])] + [f'{v:02d}' for v in values[1:]])
    except (TypeError, ValueError):
        return ''


def finish_record(record: dict, topic: str, feed_id: str) -> dict:
    record['title'] = clean(record.get('title'))
    record['abstract'] = clean(record.get('abstract'))
    record['authors'] = [clean(a) for a in record.get('authors', []) if clean(a)]
    record['venue'] = clean(record.get('venue'))
    record['doi'] = (record.get('doi') or '').strip()
    record['url'] = safe_url(record.get('url'))
    record['pdf_url'] = safe_url(record.get('pdf_url'))
    if not record['title'] or not record['url']:
        raise ValueError('Missing paper title or safe source URL')
    key = record['doi'].lower() or record.get('arxiv_id') or record['url']
    record['id'] = hashlib.sha256(key.encode()).hexdigest()[:20]
    record['topics'] = [topic]
    record['feeds'] = [feed_id]
    record['year'] = int(record['published'][:4]) if record.get('published') else None
    paper = Paper(title=record['title'], authors=record['authors'], year=record['year'],
                  abstract=record['abstract'], doi=record['doi'] or None,
                  url=record['url'], source=record['source'], venue=record['venue'],
                  volume=record.get('volume'), issue=record.get('issue'), pages=record.get('pages'))
    apa = format_apa(paper)
    if paper.venue:
        journal = paper.venue + (f', {paper.volume}' if paper.volume else '')
        # The web clipboard contains plain text, rather than Markdown italics.
        apa = apa.replace(f' *{journal}*', f' {journal}', 1)
    bib = format_bibtex(paper)
    gb = format_gb7714(paper)
    if record['kind'] == 'preprint':
        names = ', '.join(paper.authors[:3]) or 'Unknown author'
        if len(paper.authors) > 3:
            names += ', et al.'
        gb = f"{names}. {paper.title}[EB/OL]. arXiv, {paper.year or 'n.d.'}. {paper.url}."
        if not paper.doi:
            apa += f' {paper.url}'
        arxiv_id = record['arxiv_id']
        # A stable identifier also avoids colliding BibTeX keys for the same author/year.
        bib = '\n'.join([
            f"@misc{{arxiv{arxiv_id.replace('.', '')},",
            f'  title = {{{paper.title}}},',
            f"  author = {{{' and '.join(paper.authors) or 'Unknown'}}},",
            f'  year = {{{paper.year or "n.d."}}},',
            f'  eprint = {{{arxiv_id}}},',
            '  archivePrefix = {arXiv},',
            f'  url = {{{paper.url}}}', '}',
        ])
    else:
        bib = re.sub(r'^@article\{[^,]+,', f"@article{{papercash{record['id']},", bib)
    record['citations'] = {'gb7714': gb, 'apa': apa, 'bibtex': bib}
    return record


def parse_arxiv(payload: str, topic: str, feed_id: str) -> list[dict]:
    root = ET.fromstring(payload)
    papers = []
    for entry in root.findall('a:entry', NS):
        raw_id = entry.findtext('a:id', '', NS).split('/abs/')[-1]
        arxiv_id = re.sub(r'v\d+$', '', raw_id)
        if not re.fullmatch(r'(?:\d{4}\.\d{4,5}|[a-z-]+(?:\.[A-Z]{2})?/\d{7})', arxiv_id):
            continue
        papers.append(finish_record({
            'title': entry.findtext('a:title', '', NS),
            'authors': [a.findtext('a:name', '', NS) for a in entry.findall('a:author', NS)],
            'abstract': entry.findtext('a:summary', '', NS),
            'doi': entry.findtext('x:doi', '', NS), 'arxiv_id': arxiv_id,
            'url': f'https://arxiv.org/abs/{arxiv_id}',
            'pdf_url': f'https://arxiv.org/pdf/{arxiv_id}',
            'published': entry.findtext('a:published', '', NS)[:10],
            'updated': entry.findtext('a:updated', '', NS)[:10],
            'venue': 'arXiv', 'source': 'arXiv', 'kind': 'preprint',
            'keywords': [c.get('term', '') for c in entry.findall('a:category', NS)],
        }, topic, feed_id))
    return papers


def parse_crossref(payload: dict, topic: str, feed_id: str) -> list[dict]:
    papers = []
    for item in payload.get('message', {}).get('items', []):
        titles = item.get('title') or []
        doi = (item.get('DOI') or '').strip()
        if not titles or not doi:
            continue
        published = ''
        for key in ('published-online', 'published-print', 'published'):
            dates = (item.get(key) or {}).get('date-parts') or []
            if dates:
                published = partial_date(dates[0])
            if published:
                break
        authors = [' '.join(filter(None, [a.get('given'), a.get('family')]))
                   or a.get('name', '') for a in item.get('author', [])]
        papers.append(finish_record({
            'title': titles[0], 'authors': authors,
            'abstract': item.get('abstract', ''), 'doi': doi,
            'url': f'https://doi.org/{quote(doi, safe="/():;._-")}', 'pdf_url': '',
            'published': published, 'updated': '',
            'venue': (item.get('container-title') or [''])[0],
            'source': 'Crossref', 'kind': 'journal', 'keywords': item.get('subject') or [],
            'volume': item.get('volume'), 'issue': item.get('issue'), 'pages': item.get('page'),
        }, topic, feed_id))
    return papers


def merge_papers(papers: list[dict]) -> list[dict]:
    merged = {}
    for paper in papers:
        # DOI/arXiv identifiers are safer than titles such as "Editorial".
        identity = paper['id']
        if identity not in merged:
            merged[identity] = dict(paper)
        else:
            current = merged[identity]
            for key in ('topics', 'feeds'):
                current[key] = sorted(set(current[key] + paper[key]))
            if not current.get('abstract') and paper.get('abstract'):
                current['abstract'] = paper['abstract']
    return sorted(merged.values(), key=lambda p: (p.get('published', ''), p['title']), reverse=True)


def build_snapshot(previous: dict | None = None, *, fetch=requests.get,
                   now: datetime | None = None, pause=time.sleep, limit: int = 12) -> dict:
    now = now or datetime.now(CST)
    stamp = now.isoformat(timespec='seconds')
    previous = previous or {}
    papers = []
    feeds = []
    previous_feeds = {f['id']: f for f in previous.get('feeds', [])}
    headers = {'User-Agent': 'PaperCash/2.0 (+https://github.com/Jesseovo/PaperCash)'}
    arxiv_called = False
    for feed_id, topic, source, query in FEEDS:
        entry = {'id': feed_id, 'topic': topic, 'source': source, 'checked_at': stamp}
        try:
            if source == 'arXiv':
                if arxiv_called:
                    pause(3.1)
                arxiv_called = True
                response = fetch('https://export.arxiv.org/api/query', params={
                    'search_query': query, 'start': 0, 'max_results': limit,
                    'sortBy': 'submittedDate', 'sortOrder': 'descending',
                }, headers=headers, timeout=30)
                response.raise_for_status()
                batch = parse_arxiv(response.text, topic, feed_id)
            else:
                response = fetch('https://api.crossref.org/works', params={
                    'query.title': query, 'rows': limit, 'sort': 'relevance',
                    'filter': f'type:journal-article,from-pub-date:{(now.date()-timedelta(days=365)).isoformat()},until-pub-date:{now.date().isoformat()}',
                    'select': 'DOI,title,author,published,published-online,published-print,abstract,container-title,subject,type,volume,issue,page',
                }, headers=headers, timeout=30)
                response.raise_for_status()
                batch = parse_crossref(response.json(), topic, feed_id)
            if not batch:
                # An empty feed must not silently replace a useful snapshot.
                raise ValueError('No valid paper records returned')
            entry.update(status='ok', updated_at=stamp, count=len(batch))
        except (requests.RequestException, ET.ParseError, ValueError, TypeError, KeyError) as exc:
            batch = [dict(p) for p in previous.get('papers', []) if feed_id in p.get('feeds', [])]
            entry.update(status='stale' if batch else 'unavailable', count=len(batch),
                         updated_at=previous_feeds.get(feed_id, {}).get('updated_at'),
                         error=type(exc).__name__)
        papers.extend(batch)
        feeds.append(entry)
        print(f"{feed_id}: {entry['status']} ({len(batch)} papers)", flush=True)
    merged = merge_papers(papers)
    if not merged:
        raise RuntimeError('All paper sources failed and no previous snapshot is available')
    return {'schema_version': 1, 'generated_at': stamp,
            'topics': TOPICS, 'feeds': feeds, 'papers': merged}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'docs' / 'data' / 'papers.json')
    parser.add_argument('--limit', type=int, default=12)
    args = parser.parse_args()
    if not 1 <= args.limit <= 30:
        parser.error('--limit must be between 1 and 30')
    previous = json.loads(args.output.read_text(encoding='utf-8')) if args.output.exists() else None
    snapshot = build_snapshot(previous, limit=args.limit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix('.tmp')
    temporary.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(args.output)
    print(f"Saved {len(snapshot['papers'])} real papers to {args.output}")


if __name__ == '__main__':
    main()
