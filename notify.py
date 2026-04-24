"""
Daily stock analysis runner + macOS notification alert.
"""
import io
import sys
import os
import subprocess
from datetime import datetime



def run_analysis() -> str:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    buf = io.StringIO()
    old_stdout, sys.stdout = sys.stdout, buf
    try:
        from analyse import analyze_symbols, cleanup_files
        cleanup_files()
        analyze_symbols()
    except Exception as e:
        sys.stdout = old_stdout
        return f'[ERROR] Analysis failed: {e}'
    finally:
        sys.stdout = old_stdout

    return buf.getvalue()


def build_message(raw: str) -> tuple[str, str]:
    date_str = datetime.now().strftime('%b %d, %Y')
    lines    = [l.strip() for l in raw.splitlines() if l.strip()]
    buys     = [l for l in lines if l.startswith('[BUY')]
    sells    = [l for l in lines if l.startswith('[SELL')]
    errors   = [l for l in lines if 'Error' in l]

    subject = f'Stocks {date_str}: {len(buys)} BUY / {len(sells)} SELL'

    parts = []
    if buys:
        tickers = ', '.join(l.split('-->')[1].split('(')[0].strip() for l in buys)
        parts.append(f'🟢 BUY: {tickers}')
    if sells:
        tickers = ', '.join(l.split('-->')[1].split('(')[0].strip() for l in sells)
        parts.append(f'🔴 SELL: {tickers}')
    if not buys and not sells:
        parts.append('No signals today.')
    if errors:
        parts.append(f'⚠️ {len(errors)} symbol(s) skipped.')

    return subject, '\n'.join(parts)


def send_notification(title: str, body: str):
    title_esc = title.replace('"', '\\"').replace("'", "\\'")
    body_esc  = body.replace('\\', '\\\\').replace('"', '\\"').replace("'", "\\'")
    subprocess.run([
        'osascript', '-e',
        f'display alert "{title_esc}" message "{body_esc}"'
    ])
    print(f'Notification sent: {title}')


if __name__ == '__main__':
    print(f'[{datetime.now():%Y-%m-%d %H:%M}] Running analysis...')
    raw           = run_analysis()
    print(raw)
    subject, body = build_message(raw)
    print(f'Subject : {subject}')
    print(f'Body    :\n{body}')
    send_notification(subject, body)
