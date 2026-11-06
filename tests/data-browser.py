"""Actual browser imports using generated, independently checkable fixtures (not customer data)."""
from pathlib import Path
from datetime import datetime,timedelta
from tempfile import TemporaryDirectory
from openpyxl import Workbook
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with TemporaryDirectory(prefix='wind-input-') as temp:
 d=Path(temp)
 def write(name,start,end,minutes,speed,direction=270,qc=False):
  p=d/name
  with p.open('w') as f:
   f.write('timestamp,WS_125m,WD_125m'+(',qc_flag' if qc else '')+'\n')
   t=start;i=0
   while t<end:
    f.write(f'{t:%Y-%m-%d %H:%M},'+str(speed)+','+str(direction)+(',1' if qc and i%100==0 else ',0' if qc else '')+'\n');t+=timedelta(minutes=minutes);i+=1
  return p
 start,end=datetime(2024,1,1),datetime(2025,1,1)
 raw=write('raw_125m.csv',start,end,10,6)
 qc=write('qc_125m.csv',start,end,10,6,qc=True)
 final=write('final_hub_125m.csv',start,end,60,7)
 meso=write('ERA5_125m.csv',datetime(1995,1,1),end,60,8)
 wb=Workbook();a=wb.active;a.title='说明';a.append(['time','WS_80m']);a.append([datetime(2024,1,1),4]);a.append([datetime(2024,1,1,1),6]);a=wb.create_sheet('数据');a.append(['date','time','WS_125m','WD_125m']);a.append(['2024-01-01','00:00',6,350]);a.append(['2024-01-01','01:00',8,10]);xlsx=d/'raw_excel.xlsx';wb.save(xlsx)
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
  page=b.new_page(viewport={'width':1550,'height':1080});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto('http://127.0.0.1:8000',wait_until='networkidle');page.click('nav [data-page="data"]')
  page.set_input_files('#realFiles',[str(raw),str(qc),str(final),str(meso)])
  page.wait_for_function('importEntries.length===4&&!importBusy',timeout=60000)
  page.click('#commitRealFiles');page.wait_for_function('!importBusy&&realDatasets.final!==null',timeout=90000)
  assert page.locator('#charts.active').count()==1
  assert page.locator('#sourceBadge').inner_text()=='真实数据'
  assert page.evaluate('realDatasets.raw.rows.length')==52704
  assert page.evaluate('realDatasets.final.rows.length')==8784
  for n in [10,20,30]:
   page.select_option('#realWindow',str(n))
   assert page.locator('#v03Composition table').last.locator('tbody tr').count()==n
   assert '完整覆盖' in page.locator('#v03Composition').inner_text()
   vals=page.evaluate('currentRows.map(r=>r[2])');assert all(v=='8.000' for v in vals),n
  with page.expect_download() as download:page.click('#csvDownload')
  csv=Path(download.value.path()).read_text();assert '真实数据' in download.value.suggested_filename and 'ERA5_125m.csv' in csv
  page.select_option('#previewSource','mast')
  assert page.locator('[data-real-series]').count()==4
  assert page.locator('#v03Composition svg').count()==3
  assert page.evaluate('currentRows.length')==366
  assert page.evaluate('currentRows[0].slice(1)')==['6.000','6.000','7.000','8.000']
  page.locator('[data-real-series="1"]').uncheck();assert page.evaluate('v03State.visible[1]') is False
  page.select_option('#realAggregation','hour')
  assert page.evaluate('currentRows.length')==8784
  assert page.evaluate('currentRows[0][1]')=='6.000'
  page.click('nav [data-page="data"]');page.evaluate("window.scrollTo(0,0);document.querySelector('#toast').style.display='none'")
  page.screenshot(path=str(ROOT/'dist/验收-真实文件识别.png'),full_page=True)
  page.click('nav [data-page="charts"]');page.select_option('#previewSource','mesoscale');page.evaluate('window.scrollTo(0,0)')
  page.screenshot(path=str(ROOT/'dist/验收-真实概览.png'),full_page=True)
  # XLSX CRC/deflate/shared-or-inline strings and numeric Excel date handling, multiple sheets.
  page.click('nav [data-page="data"]');page.set_input_files('#realFiles',str(xlsx))
  page.wait_for_function('importEntries.length===1&&!importBusy',timeout=30000)
  page.select_option('[data-field="sheet"]','1');page.wait_for_function('importEntries[0].table.sheet==="数据"')
  page.click('#commitRealFiles');page.wait_for_function('!importBusy')
  assert page.evaluate('realDatasets.raw.rows.length')==2
  assert page.evaluate('realDatasets.raw.channels[0].height')==125
  # Incomplete final year is imported but never declared usable for long-window anchoring.
  short=write('final_short.csv',start,start+timedelta(days=2),60,7)
  page.click('nav [data-page="data"]');page.set_input_files('#realFiles',str(short))
  page.wait_for_function('importEntries.length===1&&!importBusy');page.fill('[data-field="height"]','125')
  page.click('#commitRealFiles');page.wait_for_function('!importBusy')
  assert '日历年' in page.locator('#realImportStatus').inner_text()
  assert page.locator('#sourceBadge').inner_text()=='真实资料 · 待补'
  assert page.locator('#svgDownload').is_disabled()
  # Failed stage mapping never partially replaces a previously committed dataset.
  page.click('nav [data-page="data"]');page.set_input_files('#realFiles',str(raw))
  page.wait_for_function('importEntries.length===1&&!importBusy');page.select_option('[data-field="stage"]','')
  page.click('#commitRealFiles');page.wait_for_function('!importBusy');assert '请选择数据阶段' in page.locator('#realImportStatus').inner_text()
  assert page.evaluate('realDatasets.raw.rows.length')==2
  page.click('nav [data-page="overview"]');page.click('#newProject')
  assert page.evaluate('Object.values(realDatasets).every(x=>x===null)')
  assert not errors,errors
  b.close();print('PASS: actual four-file imports (30-year hourly meso + 10-minute mast), 10/20/30 windows, actual means, four-series/hour-day comparison, CSV provenance, multi-sheet XLSX, invalid final-year block, atomic import and project isolation.')
