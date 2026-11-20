"""Focused read-only analysis of published test-centre throughput, not booking events."""
import json, re, calendar, collections, html, zipfile, hashlib
from pathlib import Path

base=json.loads(Path('Research-data.json').read_text())
a=json.loads(Path('sources/drt122a.json').read_text())
def norm(s):return re.sub('[^a-z0-9]','',s.lower().replace('[z]',''))
f=json.loads(Path('sources/drt122f.json').read_text())
countries={norm(r[2]):r[0] for r in f['DRT122F'][4:] if len(r)>3}
centres=[];centre=None;monthly={}
for r in a['2025-26'][4:]:
    if len(r)==1:
        centre=r[0];monthly={}
    elif len(r)>9 and 'T00:' in str(r[0]):
        monthly[r[0][:7]]=int(r[9]) if isinstance(r[9],(int,float)) else None
    elif len(r)>9 and r[0]==centre and isinstance(r[9],(float,int)):
        country=countries.get(norm(centre))
        if country not in ['England','Wales']:continue
        complete=len(monthly)==12 and all(v is not None for v in monthly.values()) and sum(monthly.values())==r[9]
        peak=[m for m,v in monthly.items() if v==max(monthly.values())] if complete else []
        quiet=[m for m,v in monthly.items() if v==min(monthly.values())] if complete else []
        centres.append(dict(centre=centre,country=country,annual_tests=int(r[9]),monthly_tests=monthly,complete_monthly_series=complete,peak_months=peak,quietest_months=quiet))
assert len(centres)==243
months=[f'2025-{m:02}' for m in range(4,13)]+[f'2026-{m:02}' for m in range(1,4)]
country_months=[]
for m in months:
    eng=next(r['conducted'] for r in base['geo'] if r['area']=='England' and r['month']==m)
    wal=next(r['conducted'] for r in base['geo'] if r['area']=='Wales' and r['month']==m)
    country_months.append(dict(month=m,England=int(eng),Wales=int(wal),England_Wales=int(eng+wal)))
rankings={}
for country in ['England','Wales']:
    pool=[r for r in centres if r['country']==country]
    rankings[country+'_busiest']=sorted(pool,key=lambda r:(-r['annual_tests'],r['centre']))[:20]
    rankings[country+'_quietest']=sorted(pool,key=lambda r:(r['annual_tests'],r['centre']))[:20]
    rankings[country+'_quietest_complete_months']=sorted([r for r in pool if r['complete_monthly_series']],key=lambda r:(r['annual_tests'],r['centre']))[:20]
out={'scope':'Tests conducted, B+B1 as defined by DRT122A; England and Wales; not bookings created or future booked appointments','period':'April 2025 to March 2026','source':'https://assets.publishing.service.gov.uk/media/6a3be0d430b491f55b3c48ac/drt122a-car-driving-test-by-test-centre.ods','country_monthly_source':base['provenance']['g']['url'],'centres':centres,'country_months':country_months,'rankings':rankings,'notes':['Month labels only: arbitrary stored days within ODS date-formatted labels are not daily test observations.','Missing/suppressed monthly counts are null and are never replaced with zero.','Peak and quietest month only calculated when 12 numeric months reconcile to annual total.','Low annual throughput may reflect an intermittent, specialist, relocated or part-year site.','Annual source excludes some single-examiner centres.','Sampled per-test FOI Annex B has no test date and exactly 1048573 data rows plus 3 header lines; possible spreadsheet row-limit truncation. Not used for timing or volume conclusions.']}
Path('Centre-monthly-test-volumes.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
def esc(s):return html.escape(str(s))
def count(x):return '—' if x is None else f'{x:,}'
def ml(ms):return ', '.join(calendar.month_name[int(m[5:])]+f' {m[:4]}' for m in ms) or 'Not established'
def table(headers,rows,id=''):
    return '<div class="scroll"><table'+(' id="'+id+'"' if id else '')+'><thead><tr>'+''.join('<th>'+h+'</th>' for h in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+str(v)+'</td>' for v in r)+'</tr>' for r in rows)+'</tbody></table></div>'
src='<a href="'+out['source']+'">DVSA DRT122A source workbook</a>'
gsrc='<a href="'+out['country_monthly_source']+'">DVSA DRT121G country-month source</a>'
parts=['''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Tests taken at centres: direct answers and monthly counts</title><style>body{font:16px/1.55 system-ui,sans-serif;color:#193547;background:#edf2f5;margin:0}main{max-width:1150px;margin:30px auto;background:white;padding:40px}h1{line-height:1.2;font-size:32px}h2{margin-top:40px;border-top:2px solid #087f83;padding-top:20px}h3{margin-top:30px}a{color:#006c78}table{border-collapse:collapse;width:100%;font-size:13px}td,th{border-bottom:1px solid #ccd9de;padding:9px;text-align:left;vertical-align:top}th{background:#edf4f6}tr:nth-child(even){background:#f8fafb}.scroll{overflow:auto;margin:20px 0}.note{font-size:13px;color:#526c78}.callout{padding:16px;background:#edf6f6;border-left:4px solid #087f83}details{border:1px solid #d1dfe5;margin:16px 0;padding:15px}summary{font-weight:700;cursor:pointer}input{font:inherit;padding:10px;width:100%;max-width:450px}nav{display:flex;gap:20px;flex-wrap:wrap}code{font-size:13px}@media print{body{background:white}main{margin:0;padding:0}input,nav{display:none}h2{break-after:avoid}tr{break-inside:avoid}.scroll{overflow:visible}table{font-size:8px}}@media(max-width:700px){main{padding:20px;margin:0}}</style></head><body><main><p class="note">Focused follow-up · 20 November 2026</p><h1>Tests actually taken at driving test centres</h1><p>England and Wales · Direct answers to the three core questions</p><nav><a href="#answer">What can be answered?</a><a href="#patterns">Peak periods</a><a href="#locations">Busiest/quietest centres</a><a href="#all">Every centre’s monthly counts</a><a href="#additional">Additional evidence</a></nav>''']
parts.append('<h2 id="answer">1. Counts by day, week and month</h2><p class="callout"><strong>Monthly counts and volume rankings: yes, directly available. Exact daily/weekly centre counts and current peak weekdays: not yet verified from an accessible complete dataset.</strong> The previous report gave too much prominence to waiting-time proxies. For your question, the primary measure is tests conducted.</p>')
parts.append(table(['Requirement','Answer','Direct evidence / limitation'],[
['Monthly tests at each centre','Yes',src+' contains monthly Conducted totals, despite its pass-rate title. Latest complete centre year: April 2025–March 2026. Older annual tabs extend to 2007–08.'],
['Daily tests at each centre','Not established from a complete accessible source','The standard centre table is monthly. The additional per-test FOI file inspected has no calendar-date column.'],
['Weekly tests at each centre','Not established from a complete accessible source','Cannot split a month accurately into weeks. Published FOI logs identify relevant previous requests, but their underlying response still needs obtaining.'],
['Monthly/annual busiest and quietest centres','Yes','Rank Conducted totals directly for the selected period. All-centre monthly counts and annual top/bottom 20 lists are supplied below.'],
['Peak months by centre','Yes, for a specified observed year','Calculated below when twelve monthly counts are numeric and reconcile. Multiple years are needed to establish recurrent seasonality.'],
['Peak weekday / busiest individual date / busiest week','Not currently established for E/W centres','Historical GB weekday data exists for 2010–11, but it is not a current E/W centre breakdown.']]))
parts.append('<p><strong>Terminology:</strong> these are tests taken with an outcome. If “bookings” means appointments created on a particular day, that is a different event and requires booking-creation dates. Neither actual tests nor the future-booking stock supplies those dates.</p><p><strong>Scope:</strong> DRT122A’s notes include B and B1. Treat these figures as published car-test volumes; a strict B-only extract requires DVSA confirmation. Suppressed values remain missing. No daily or weekly estimates have been made by dividing monthly or annual totals.</p>')
parts.append('<h2 id="patterns">2. Specific peak-month patterns</h2><p>These are actual country-month counts for the latest complete financial year, using the official country totals rather than adding incomplete/suppressed centre rows. Source: '+gsrc+'.</p>')
parts.append(table(['Test month','England','Wales','England + Wales'],[[r['month'],count(r['England']),count(r['Wales']),count(r['England_Wales'])] for r in country_months]))
parts.append('<p><strong>For this latest complete year:</strong> March 2026 is busiest in both England (173,511) and Wales (9,870). England’s quietest month is April 2025 (126,089); Wales’s is August 2025 (6,506). Combined E/W throughput ranges from 132,962 in April to 183,381 in March. These observed peaks differ from the longer-run seasonal profile below.</p>')
parts.append('<p><strong>Do not confuse one year with recurring seasonality.</strong> In the earlier long-run calculation, October/November were strongest for GB throughput in 2010–19, while December was weakest. For England in 2022–25, November had the highest mean within-year index; for Wales, October did. Those results describe tests delivered, without adjusting for working days, examiner staffing or interventions. '+gsrc+'; <a href="'+base['provenance']['b']['url']+'">DRT121B long-run GB source</a>.</p>')
examples=['Birmingham (Garretts Green)','Goodmayes (London)','Leicester (Wigston)','Cardiff (Llanishen)','Swansea','Bala','Pwllheli']
parts.append('<h3>Centre-specific examples, April 2025–March 2026</h3>')
example_rows=[]
for name in examples:
    r=next(x for x in centres if x['centre']==name)
    example_rows.append([esc(name),count(r['annual_tests']),ml(r['peak_months'])+(' — '+count(r['monthly_tests'][r['peak_months'][0]])) if r['peak_months'] else 'Not established',ml(r['quietest_months'])+(' — '+count(r['monthly_tests'][r['quietest_months'][0]])) if r['quietest_months'] else 'Not established'])
parts.append(table(['Centre','Annual tests','Busiest month, tests','Quietest month, tests'],example_rows))
parts.append('<p>Source: '+src+'. Peak/quietest values are shown only for twelve complete numeric months that reconcile to the published annual total. No significance or repeated seasonal effect is implied.</p>')
parts.append('<h3>What is known about peak days?</h3><p>An official historical DSA response gives GB FY2010–11 counts: Tuesday 326,436; Wednesday 325,923; Thursday 322,965; Monday 276,547; Friday 266,198; Saturday 82,699; Sunday 4,828. Tuesday was highest in that specific old national period. It cannot be used as evidence of the current busiest weekday at an English or Welsh centre. <a href="'+base['provenance']['day']['url']+'">Official FOI IA/01205/11, Annex A</a>.</p>')
parts.append('<h2 id="locations">3. Busiest and quietest centres by tests conducted</h2><p>Period: April 2025–March 2026. These rankings use published annual throughput, not waiting times. Lowest volumes include intermittent, specialist and part-year sites. Wales has 21 centres with numeric annual totals, so its top and bottom 20 lists overlap. Source: '+src+'.</p>')
for country in ['England','Wales']:
    for kind in ['busiest','quietest','quietest_complete_months']:
        title={'busiest':'20 busiest published locations','quietest':'20 quietest published locations, including intermittent sites','quietest_complete_months':'20 lowest-volume locations with twelve complete reported monthly counts'}[kind]
        parts.append('<details open><summary>'+country+' — '+title+'</summary>')
        if kind=='quietest_complete_months':parts.append('<p class="note">An additional comparability view, not proof of all-year opening or full staffing. Eligibility requires 12 numeric months and an exact annual reconciliation. This does not replace the unfiltered published-location ranking.</p>')
        parts.append(table(['Order','Centre','Annual tests','Peak month','Quietest month'],[[i+1,esc(r['centre']),count(r['annual_tests']),ml(r['peak_months']),ml(r['quietest_months'])] for i,r in enumerate(rankings[country+'_'+kind])]))
        parts.append('</details>')
parts.append('<h2 id="all">4. Every centre’s monthly counts</h2><p>Search a centre name or country. “—” means missing or suppressed; it is not zero. Date-formatted source cells are monthly labels: their stored day component must not be interpreted as a daily count. The annual totals include cases where monthly values are suppressed.</p><label for="search">Find a centre</label><br><input id="search" type="search" placeholder="For example: Cardiff, Birmingham or Wales">')
parts.append(table(['Country','Centre','Annual']+[m for m in months],[[r['country'],esc(r['centre']),count(r['annual_tests'])]+[count(r['monthly_tests'].get(m)) for m in months] for r in sorted(centres,key=lambda r:(r['country'],r['centre']))],id='centre-data'))
parts.append('<p class="note">243 locations: 222 England, 21 Wales. These are the published annual centres with numeric totals and a country match, including any historical/part-year locations. National totals can include additional suppressed or omitted centre details.</p>')
parts.append('<h2 id="additional">5. Additional resources checked and the remaining gap</h2>')
parts.append(table(['Resource','What was found','Does it close the daily/weekly gap?'],[
['DVSA DRT122A on GOV.UK','Monthly centre Conducted totals, despite the pass-rate title.','Closes the monthly-count and volume-ranking questions directly.'],
['DVSA FOI 2409-056666 / initial 2408-054341','A public requester-hosted copy of Category B per-test records, nominally 1 April 2023–30 March 2024. I downloaded Annex B. Actual columns: TC_ID, TC_NAME, Test ID, SLOT_TIME, ATTEMPTS, Result.','No calendar test date. The CSV contains exactly 1,048,573 data rows plus three header rows: this matches Excel’s 1,048,576-row sheet limit. Truncation is a serious possibility, so no complete-year volume or timing conclusions were drawn.'],
['DVSA July 2026 FOI log: 2606-113511','Request for 2025/26 per-test metadata explicitly including PERIOD_DATE and SLOT_TIME; marked partially successful on 27 July 2026.','Promising exact-date lead. The log does not show which fields were actually supplied. Need the response and Annex B.'],
['DVSA August 2025 FOI log: 2507-082220','Request for weekly car tests at Salisbury, Basingstoke and Winchester; marked partially successful on 11 August 2025.','Evidence of a directly relevant previous request, not verified weekly data until the response is read.'],
['Data.gov.uk driving-tests collection','Catalogue of official driving-test statistics.','Useful discovery route; no additional complete centre/date table verified here.']]))
parts.append('<p>Public evidence links: <a href="https://www.whatdotheyknow.com/request/driving_test_fault_statistics_by">FOI correspondence and receipt confirmation</a>; <a href="https://github.com/JakeCracknell/dvsa_driving_test_data/tree/a30f0263943b0e060d6dfcc46fb6b0f970e17f92/raw">requester’s preserved raw annexes</a>; <a href="https://www.gov.uk/csv-preview/6af72677ccb3ea58ac8742ad/dvsa-foi-disclosure-log-july-2026.csv">July 2026 GOV.UK disclosure log</a>; <a href="https://www.gov.uk/csv-preview/6972526995ec95e3414fd4c3/dvsa-foi-disclosure-log-august-2025.csv">August 2025 GOV.UK log</a>; <a href="https://www.data.gov.uk/collections/transport/driving-tests">Data.gov.uk collection</a>.</p>')
parts.append('<p><strong>The next evidence step is specific:</strong> obtain DVSA’s existing response 2606-113511 and its annexes, asking whether the complete B-only data includes a test date for each row. If it does, daily, Monday–Sunday weekly, weekday and monthly counts can all be calculated by centre. If it does not, request <em>centre ID/name, test date, and count of Category B tests conducted</em> for the desired period, split into manageable files if needed. There is no need for candidate IDs, fault records or other personal information. This request has not been sent.</p><p>Keep booking activity separate: if the intended measure is bookings created, request <em>creation date, intended test centre, test category and booking count</em>, with a definition of amendments/replacements. Test-date aggregates cannot answer creation-date questions.</p>')
parts.append('<p class="note">Confidence: High in monthly published counts and arithmetic rankings; Medium in representativeness of the lowest-volume comparisons; Low/unestablished for current weekday or daily/weekly patterns. This supplement narrows the original review to the user’s three core questions.</p><script>document.getElementById("search").addEventListener("input",function(){const q=this.value.toLowerCase();document.querySelectorAll("#centre-data tbody tr").forEach(r=>{r.hidden=!r.textContent.toLowerCase().includes(q)});});</script></main></body></html>')
Path('Tests-taken-at-centres-direct-answers.html').write_text('\n'.join(parts))
checks={'centre_count':len(centres),'complete_monthly_series':sum(r['complete_monthly_series'] for r in centres),'monthly_records':sum(len(r['monthly_tests']) for r in centres),'country_peaks':{c:max(country_months,key=lambda r:r[c]) for c in ['England','Wales','England_Wales']},'country_quietest':{c:min(country_months,key=lambda r:r[c]) for c in ['England','Wales','England_Wales']},'examples':example_rows}
Path('Centre-volume-checks.json').write_text(json.dumps(checks,indent=2))
print(json.dumps(checks,indent=2))
