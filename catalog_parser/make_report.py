"""Рисует HTML-витрину результата парсера (для скриншота в портфолио)."""
import html
import json
from pathlib import Path

d = json.loads(Path('books.json').read_text(encoding='utf-8'))
mx = max(s['count'] for s in d['summary'])
bars = ''.join(
    f'<div class="bar"><span class="lbl">{html.escape(s["category"])}</span>'
    f'<span class="track"><i style="width:{s["count"] / mx * 100:.0f}%"></i></span>'
    f'<b>{s["count"]}</b></div>' for s in d['summary'][:10])
rows = ''.join(
    f'<tr><td class="t">{html.escape(b["title"][:46])}</td><td>{html.escape(b["category"])}</td>'
    f'<td class="n">{b["price_rub"]:,} ₽</td><td class="r r{b["rating"]}">{"★" * b["rating"]}</td>'
    f'<td class="n">{b["stock"]}</td></tr>'.replace(',', ' ') for b in d['top'])
page = f"""<!doctype html><html lang="ru"><head><meta charset="utf-8"><title>Парсер каталога</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Onest:wght@400;600;800&family=JetBrains+Mono:wght@400;600&display=swap');
*{{box-sizing:border-box;margin:0}} body{{font-family:Onest,system-ui,sans-serif;background:#0d1117;color:#e6edf3;width:1440px;height:900px;padding:44px 52px;overflow:hidden}}
h1{{font-size:46px;font-weight:800;letter-spacing:-.02em}} .sub{{color:#8b949e;font-size:18px;margin-top:8px}}
.grid{{display:grid;grid-template-columns:520px 1fr;gap:28px;margin-top:30px}}
.card{{background:#161b22;border:1px solid #30363d;border-radius:16px;padding:22px}}
.kpis{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-top:26px}} .kpi b{{font-size:34px;display:block;font-weight:800}} .kpi span{{color:#8b949e;font-size:14px}}
pre{{font-family:'JetBrains Mono',monospace;font-size:13px;line-height:1.55;color:#c9d1d9;white-space:pre-wrap}} .k{{color:#ff7b72}} .f{{color:#d2a8ff}} .s{{color:#a5d6ff}} .c{{color:#8b949e}} .ok{{color:#3fb950}}
.bar{{display:grid;grid-template-columns:150px 1fr 34px;align-items:center;gap:10px;margin:7px 0;font-size:14px}} .lbl{{color:#c9d1d9;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.track{{height:10px;background:#21262d;border-radius:6px;overflow:hidden}} .track i{{display:block;height:100%;background:linear-gradient(90deg,#1f6feb,#58a6ff);border-radius:6px}}
table{{width:100%;border-collapse:collapse;font-size:14px}} th{{text-align:left;color:#8b949e;font-weight:600;padding:8px 6px;border-bottom:1px solid #30363d}} td{{padding:9px 6px;border-bottom:1px solid #21262d}}
td.n{{text-align:right;font-variant-numeric:tabular-nums}} .r{{color:#e3b341;letter-spacing:1px}} .xl{{display:flex;gap:10px;align-items:center;margin-bottom:12px;color:#3fb950;font-weight:600}}
.xl i{{width:26px;height:26px;border-radius:6px;background:#1d6f42;display:grid;place-items:center;color:#fff;font-style:normal;font-size:14px}}
h3{{font-size:16px;color:#8b949e;font-weight:600;margin-bottom:10px}}
</style></head><body>
<h1>Парсер каталога → Excel-отчёт</h1>
<div class="sub">Асинхронный сбор {d['total']} карточек товаров за {d['seconds']:.0f} секунд · Python, httpx, BeautifulSoup, openpyxl</div>
<div class="kpis">
<div class="card kpi"><b>{d['total']}</b><span>товаров собрано</span></div>
<div class="card kpi"><b>{d['categories']}</b><span>категорий</span></div>
<div class="card kpi"><b>{str(d['avg_rub'])[:-3]+' '+str(d['avg_rub'])[-3:]} ₽</b><span>средняя цена</span></div>
<div class="card kpi"><b>{d['seconds']:.0f} с</b><span>на весь каталог</span></div>
</div>
<div class="grid">
<div class="card"><pre><span class="c"># 8 параллельных запросов, повторы при ошибках</span>
<span class="k">async def</span> <span class="f">crawl</span>(concurrency):
    sem = asyncio.Semaphore(concurrency)
    <span class="k">async with</span> httpx.AsyncClient() <span class="k">as</span> client:
        links = <span class="k">await</span> <span class="f">collect_links</span>(client, sem)
        pages = <span class="k">await</span> asyncio.gather(*(
            <span class="f">get</span>(client, u, sem) <span class="k">for</span> u <span class="k">in</span> links))
        <span class="k">return</span> [<span class="f">parse_book</span>(h, u) <span class="k">for</span> h, u <span class="k">in</span> zip(pages, links)]

<span class="c">$ python parser.py --out books.xlsx</span>
<span class="ok">✓ {d['total']} товаров, {d['categories']} категорий за {d['seconds']:.0f} с</span>
<span class="ok">✓ books.xlsx: лист «Товары» + «Сводка» с графиком</span></pre>
<h3 style="margin-top:18px">Товаров по категориям</h3>{bars}</div>
<div class="card"><div class="xl"><i>X</i>books.xlsx — лист «Товары»: фильтры, закреплённая шапка, цвет по рейтингу</div>
<table><tr><th>Название</th><th>Категория</th><th style="text-align:right">Цена</th><th>Рейтинг</th><th style="text-align:right">Остаток</th></tr>{rows}</table>
<h3 style="margin-top:20px">Что ещё умеет</h3>
<div style="color:#c9d1d9;font-size:15px;line-height:1.7">Запуск по расписанию · выгрузка в Google Таблицы · уведомления в Telegram об изменении цен и остатков · обход пагинации и фильтров · прокси и лимиты запросов</div></div>
</div></body></html>"""
Path('report.html').write_text(page, encoding='utf-8')
print('report.html')
