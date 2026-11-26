"""Writes latest.json: change of each index since the report's last close (Nov 25, 2026). Standard library only."""
import json, math, time, urllib.parse, urllib.request
from datetime import datetime, timezone

BASE = '2026-11-25'
TICKERS = [('spx', '^GSPC'), ('nas', '^IXIC'), ('dow', '^DJI'), ('rut', '^RUT'), ('nvda', 'NVDA'), ('vix', '^VIX')]

def closes(symbol):
    url = f'https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(symbol)}?range=1y&interval=1d'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    for attempt in range(4):
        try:
            r = json.load(urllib.request.urlopen(req, timeout=30))['chart']['result'][0]
            break
        except Exception:
            if attempt == 3:
                raise
            time.sleep(20 * (attempt + 1))
    offset = r['meta']['gmtoffset']
    day = lambda ts: datetime.fromtimestamp(ts + offset, timezone.utc).strftime('%Y-%m-%d')
    out = {day(t): c for t, c in zip(r['timestamp'], r['indicators']['quote'][0]['close']) if c is not None}
    session = r['meta']['currentTradingPeriod']['regular']
    if time.time() < session['end'] + 900:          # the session has not closed yet: leave it out
        out.pop(day(session['start']), None)
    return out

data = {k: closes(s) for k, s in TICKERS}
asof = min(max(v) for v in data.values())           # last date every series has
rows = {}
for k, v in data.items():
    base, last = v[BASE], v[asof]
    assert math.isfinite(base) and math.isfinite(last) and base > 0
    rows[k] = {'base': round(base, 2), 'last': round(last, 2), 'chg': round((last / base - 1) * 100, 2)}
sessions = sum(1 for d in data['spx'] if BASE < d <= asof)
json.dump({'base_date': BASE, 'asof': asof, 'sessions': sessions, 'rows': rows}, open('latest.json', 'w'), indent=1)
print(asof, sessions, {k: r['chg'] for k, r in rows.items()})
