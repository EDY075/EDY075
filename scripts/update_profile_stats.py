#!/usr/bin/env python3
"""Refresh a profile card from GitHub's publicly visible contribution calendar.

Only the standard library is needed. Fail closed if the calendar changes: never
replace the last successful card with guessed counts. Counts are contributions,
not commits; GitHub can include anonymized private contributions in this view.
"""
import argparse
from collections import defaultdict
from datetime import date, timedelta
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
USERNAME = 'EDY075'
MONTHS = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']

class CalendarParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cells = {}
        self.tooltips = {}
        self.tooltip_id = None
        self.text = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'td' and 'ContributionCalendar-day' in a.get('class', '').split():
            if not a.get('data-date') or not a.get('id'):
                raise ValueError('Calendar cell has no date or identifier')
            if a['id'] in self.cells:
                raise ValueError('Duplicate calendar cell identifier')
            self.cells[a['id']] = a['data-date']
        if tag == 'tool-tip':
            self.tooltip_id = a.get('for')
            self.text = []
    def handle_data(self, data):
        if self.tooltip_id is not None:
            self.text.append(data)
    def handle_endtag(self, tag):
        if tag == 'tool-tip' and self.tooltip_id is not None:
            self.tooltips[self.tooltip_id] = ''.join(self.text).strip()
            self.tooltip_id = None

def parse_calendar(html):
    parser = CalendarParser()
    parser.feed(html)
    days = []
    for cell_id, day in parser.cells.items():
        text = parser.tooltips.get(cell_id, '')
        if re.match(r'No contributions\b', text, re.I):
            count = 0
        else:
            match = re.match(r'([\d,]+) contributions?\b', text, re.I)
            if not match:
                raise ValueError(f'Missing/unrecognized contribution count for {day}')
            count = int(match[1].replace(',', ''))
        date.fromisoformat(day)
        days.append({'date': day, 'count': count})
    days.sort(key=lambda d: d['date'])
    if not days:
        raise ValueError('No contribution calendar found')
    for previous, current in zip(days, days[1:]):
        if date.fromisoformat(current['date']) - date.fromisoformat(previous['date']) != timedelta(days=1):
            raise ValueError('Calendar has missing or duplicate dates')
    return days

def summarize(days):
    total = sum(d['count'] for d in days)
    active = sum(d['count'] > 0 for d in days)
    run = longest = 0
    for d in days:
        run = run + 1 if d['count'] else 0
        longest = max(longest, run)
    index = len(days) - 1
    # The current calendar day is unfinished; yesterday can sustain a streak.
    if days[index]['count'] == 0:
        index -= 1
    current = 0
    while index >= 0 and days[index]['count'] > 0:
        current += 1
        index -= 1
    monthly = defaultdict(int)
    for d in days:
        monthly[d['date'][:7]] += d['count']
    return {
        'username': USERNAME,
        'source': f'https://github.com/users/{USERNAME}/contributions',
        'range': {'start': days[0]['date'], 'end': days[-1]['date']},
        'total_contributions': total, 'active_days': active,
        'current_streak': current, 'longest_streak': longest,
        'best_day': max(days, key=lambda d: d['count']),
        'avg_per_active_day': round(total / active, 1) if active else 0.0,
        'monthly': [{'month': m, 'total': n} for m, n in sorted(monthly.items())],
        'days': days,
    }

def short_date(value):
    return date.fromisoformat(value).strftime('%d/%m/%Y')

def render(data):
    start, end = data['range']['start'], data['range']['end']
    best = data['best_day']
    tiles = [
        ('Sequência atual', str(data['current_streak']), 'dias seguidos', '#39d353'),
        ('Maior sequência', str(data['longest_streak']), 'dias no período', '#e6edf3'),
        ('Contribuições', f"{data['total_contributions']:,}".replace(',', '.'), 'no período abaixo', '#e6edf3'),
        ('Dias com atividade', str(data['active_days']), f"de {len(data['days'])} dias", '#e6edf3'),
        ('Melhor dia', str(best['count']), short_date(best['date']), '#e6edf3'),
        ('Média / dia ativo', f"{data['avg_per_active_day']:.1f}".replace('.', ','), 'contribuições', '#e6edf3'),
    ]
    description = '; '.join(f'{label}: {value} {caption}' for label, value, caption, _ in tiles)
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="800" viewBox="0 0 800 800" role="img" aria-labelledby="title desc">',
        '<title id="title">Atividade de EDY075 no GitHub</title>',
        f'<desc id="desc">Calendário público do GitHub: {escape(description)}. Período {short_date(start)} a {short_date(end)}. Gráfico mensal de seis meses; mês atual parcial.</desc>',
        '<style>text{font-family:Consolas,monospace}.bar{transform-box:fill-box;transform-origin:bottom;animation:grow .7s ease-out both}@keyframes grow{from{transform:scaleY(0)}to{transform:scaleY(1)}}@media(prefers-reduced-motion:reduce){.bar{animation:none}}</style>',
        '<rect x="1" y="1" width="798" height="798" rx="12" fill="#0d1117" stroke="#30363d" stroke-width="2"/>',
        '<text x="28" y="44" fill="#e6edf3" font-size="26" font-weight="700">ATIVIDADE NO GITHUB</text>',
        '<text x="28" y="76" fill="#aab3be" font-size="21">EDY075 · calendário público</text>',
    ]
    for i, (label, value, caption, color) in enumerate(tiles):
        x = 24 + (i % 2) * 384
        y = 96 + (i // 2) * 151
        parts += [
            f'<rect x="{x}" y="{y}" width="368" height="137" rx="8" fill="#161b22" stroke="#30363d"/>',
            f'<text x="{x+20}" y="{y+33}" fill="#aab3be" font-size="27">{escape(label)}</text>',
            f'<text x="{x+20}" y="{y+90}" fill="{color}" font-size="58" font-weight="700">{value}</text>',
            f'<text x="{x+20}" y="{y+120}" fill="#aab3be" font-size="23">{escape(caption)}</text>',
        ]
    parts += ['<text x="28" y="580" fill="#e6edf3" font-size="25">Contribuições por mês</text>']
    months = data['monthly'][-6:]
    peak = max((m['total'] for m in months), default=0) or 1
    for i, m in enumerate(months):
        x = 43 + i * 123
        height = 90 * m['total'] / peak
        label = MONTHS[int(m['month'][5:])-1]
        parts += [
            f'<rect class="bar" x="{x}" y="{710-height:.1f}" width="77" height="{height:.1f}" rx="3" fill="#26a641" style="animation-delay:{i*.06:.2f}s"><title>{m["month"]}: {m["total"]} contribuições</title></rect>',
            f'<text x="{x+38.5}" y="{700-height:.1f}" text-anchor="middle" fill="#e6edf3" font-size="21">{m["total"]}</text>',
            f'<text x="{x+38.5}" y="737" text-anchor="middle" fill="#aab3be" font-size="23">{label}</text>',
        ]
    parts += [f'<text x="28" y="772" fill="#aab3be" font-size="18">{short_date(start)}–{short_date(end)} · mês atual parcial</text>', '</svg>']
    return '\n'.join(parts) + '\n'

def main():
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument('--html', type=Path, help='Local calendar fixture for offline verification')
    options = args.parse_args()
    if options.html:
        html = options.html.read_text(encoding='utf-8')
    else:
        request = Request(f'https://github.com/users/{USERNAME}/contributions', headers={'User-Agent': 'EDY075-profile-stats/1.0', 'Accept-Language': 'en-US'})
        with urlopen(request, timeout=30) as response:
            html = response.read().decode('utf-8')
    days = parse_calendar(html)
    if not 365 <= len(days) <= 372:
        raise ValueError(f'Expected a yearly calendar, got {len(days)} days')
    headline = re.search(r'([\d,]+)\s+contributions\s+in the last year', html)
    data = summarize(days)
    bounds = [re.search(r'data-' + edge + r'="(\d{4}-\d{2}-\d{2}) ', html) for edge in ('from', 'to')]
    if not all(bounds) or [m[1] for m in bounds] != [data['range']['start'], data['range']['end']]:
        raise ValueError('Calendar dates disagree with the declared period')
    if not headline or int(headline[1].replace(',', '')) != data['total_contributions']:
        raise ValueError('Contribution total disagrees with the calendar header')
    svg = render(data)
    (ROOT / 'data').mkdir(exist_ok=True)
    (ROOT / 'data/contributions.json').write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    (ROOT / 'assets/github-activity.svg').write_text(svg, encoding='utf-8')
    print(f"{data['total_contributions']} contributions; {data['active_days']} active days; through {data['range']['end']}")

if __name__ == '__main__':
    main()
