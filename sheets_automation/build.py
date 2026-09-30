"""Мок Google Таблиц: учёт заказов с формулами + Apps Script -> sheets.html"""
import random

random.seed(4)
goods = [('Кофемолка ручная', 1890, 1120), ('Турка медная 350 мл', 2490, 1380), ('Френч-пресс 600 мл', 1590, 820),
         ('Зерно Эфиопия 250 г', 890, 410), ('Воронка V60', 1290, 690), ('Весы с таймером', 2990, 1710), ('Чайник-гусь', 3490, 2050)]
chans = ['Ozon', 'WB', 'Сайт', 'Авито']
fee = {'Ozon': .19, 'WB': .23, 'Сайт': .035, 'Авито': .06}
rows = []
for i in range(18):
    g, p, c = random.choice(goods)
    ch = random.choice(chans)
    q = random.choice([1, 1, 1, 2, 3])
    rev = p * q
    com = round(rev * fee[ch])
    marg = rev - c * q - com
    st = random.choice(['Доставлен', 'Доставлен', 'В пути', 'Собран', 'Возврат']) if i > 2 else 'Новый'
    rows.append((f'{24:02d}.09' if i < 6 else f'{25 + i // 6:02d}.09', f'#{48210 + i}', ch, g, q, rev, com, marg, st))

cells = ''
for r, row in enumerate(rows, start=2):
    d, n, ch, g, q, rev, com, marg, st = row
    stc = {'Доставлен': '#d7f5dd', 'В пути': '#e2ebff', 'Собран': '#fff2cc', 'Возврат': '#fde2e1', 'Новый': '#efe3ff'}[st]
    mc = '#137333' if marg > 0 else '#c5221f'
    pct = marg / rev * 100
    cells += (f'<tr><td class="rn">{r}</td><td>{d}</td><td>{n}</td><td>{ch}</td><td class="l">{g}</td><td class="r">{q}</td>'
              f'<td class="r">{rev:,}</td><td class="r">{com:,}</td><td class="r{" sel" if r == 5 else ""}" style="color:{mc}">{marg:,}</td>'
              f'<td class="r"><div class="db"><i style="width:{max(pct, 0):.0f}%"></i></div>{pct:.0f}%</td>'
              f'<td><span class="st" style="background:{stc}">{st}</span></td></tr>').replace(',', ' ')
tot_rev = sum(r[5] for r in rows)
tot_m = sum(r[7] for r in rows)
script = '''function syncOrders() {
  const sh = SpreadsheetApp.getActive().getSheetByName('Заказы');
  const known = new Set(sh.getRange('B2:B').getValues().flat());
  const fresh = [...ozonOrders(), ...wbOrders(), ...siteOrders()]
    .filter(o => !known.has(o.number));
  fresh.forEach(o => {
    sh.appendRow([o.date, o.number, o.channel, o.item, o.qty, o.price * o.qty]);
    const r = sh.getLastRow();
    sh.getRange(r, 7, 1, 2).setFormulas([[
      `=F${r}*VLOOKUP(C${r},Комиссии!A:B,2,0)`,
      `=F${r}-E${r}*VLOOKUP(D${r},Товары!A:C,3,0)-G${r}`]]);
  });
  if (fresh.length) notify(`Новых заказов: ${fresh.length}`);
}

function notify(text) {
  UrlFetchApp.fetch(`https://api.telegram.org/bot${TOKEN}/sendMessage`,
    {method: 'post', payload: {chat_id: CHAT, text}});
}'''
esc = script.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
html = f'''<!doctype html><html lang="ru"><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&family=Roboto+Mono&display=swap" rel="stylesheet">
<style>*{{margin:0;box-sizing:border-box}}body{{width:1700px;height:1000px;background:#f8f9fa;font-family:Roboto;font-size:14px;color:#202124;display:grid;grid-template-rows:auto auto 1fr auto}}
.top{{display:flex;align-items:center;gap:14px;padding:10px 16px;background:#fff}}.ic{{width:34px;height:40px;background:#0f9d58;border-radius:4px;position:relative}}.ic:after{{content:'';position:absolute;inset:12px 8px;border:2px solid #fff;border-radius:1px}}
.t{{font-size:18px}}.menu{{color:#5f6368;font-size:14px;margin-top:3px}}.fx{{display:flex;gap:10px;padding:6px 16px;border-top:1px solid #e0e0e0;border-bottom:1px solid #e0e0e0;background:#fff;font-family:'Roboto Mono';font-size:13px}}
.fx b{{color:#5f6368;font-weight:400;width:40px}}.main{{display:grid;grid-template-columns:1fr 640px;overflow:hidden}}
table{{border-collapse:collapse;background:#fff;width:100%;font-size:15px}}td,th{{border:1px solid #e2e3e3;padding:5px 8px;height:40px;white-space:nowrap}}
th{{background:#f8f9fa;color:#5f6368;font-weight:500}}.hd td{{background:#1e3a5f;color:#fff;font-weight:500}}
.rn{{background:#f8f9fa;color:#5f6368;text-align:center;width:40px}}.r{{text-align:right}}.l{{max-width:190px;overflow:hidden}}
.st{{padding:2px 10px;border-radius:10px;font-size:13px}}.db{{display:inline-block;width:46px;height:8px;background:#eee;border-radius:4px;margin-right:6px;vertical-align:middle;overflow:hidden}}.db i{{display:block;height:100%;background:#34a853}}
.sel{{outline:2px solid #1a73e8;outline-offset:-2px}}
.side{{background:#fff;border-left:1px solid #e0e0e0;display:flex;flex-direction:column}}.sh{{padding:14px 18px;border-bottom:1px solid #e0e0e0;font-weight:500;font-size:15px;display:flex;gap:10px;align-items:center}}
.sh i{{width:22px;height:22px;background:#1a73e8;border-radius:4px}}pre{{padding:16px 18px;font:12.5px/1.6 'Roboto Mono';color:#37474f;white-space:pre}}
.kpi{{display:grid;grid-template-columns:1fr 1fr;gap:10px;padding:14px 18px;border-top:1px solid #e0e0e0;margin-top:auto}}.kpi div{{background:#f1f3f4;border-radius:8px;padding:10px 12px}}.kpi b{{font-size:22px;display:block}}
.tabs{{display:flex;gap:2px;padding:0 16px;background:#f1f3f4;border-top:1px solid #e0e0e0}}.tabs span{{padding:9px 18px;color:#5f6368}}.tabs .a{{background:#fff;color:#188038;font-weight:500;border-bottom:3px solid #188038}}</style></head><body>
<div class="top"><div class="ic"></div><div><div class="t">Учёт заказов — кофейные аксессуары</div><div class="menu">Файл · Правка · Вид · Вставка · Формат · Данные · Инструменты · Расширения</div></div></div>
<div class="fx"><b>H5</b><span>=F5-E5*ВПР(D5;Товары!A:C;3;0)-G5</span></div>
<div class="main"><div style="overflow:hidden"><table>
<tr><th></th><th>A</th><th>B</th><th>C</th><th>D</th><th>E</th><th>F</th><th>G</th><th>H</th><th>I</th><th>J</th></tr>
<tr class="hd"><td class="rn" style="background:#f8f9fa;color:#5f6368">1</td><td>Дата</td><td>Заказ</td><td>Канал</td><td>Товар</td><td>Кол.</td><td>Выручка, ₽</td><td>Комиссия, ₽</td><td>Маржа, ₽</td><td>Маржа, %</td><td>Статус</td></tr>
{cells}</table></div>
<div class="side"><div class="sh"><i></i>Apps Script — sync.gs</div><pre>{esc}</pre>
<div class="kpi"><div><b>{tot_rev:,} ₽</b>выручка за 4 дня</div><div><b>{tot_m:,} ₽</b>маржа после комиссий</div><div><b>4</b>канала в одной таблице</div><div><b>15 мин</b>автообновление</div></div></div></div>
<div class="tabs"><span class="a">Заказы</span><span>Сводка</span><span>Товары</span><span>Комиссии</span><span>Остатки</span></div>
</body></html>'''
html = html.replace(f'{tot_rev:,} ₽', f'{tot_rev:,} ₽'.replace(',', ' ')).replace(f'{tot_m:,} ₽', f'{tot_m:,} ₽'.replace(',', ' '))
open('sheets.html', 'w', encoding='utf-8').write(html)
print('ok')
