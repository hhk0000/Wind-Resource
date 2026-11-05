"""Functional prototype checks; requires Playwright and system Chromium."""
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 page=browser.new_page(viewport={'width':1440,'height':1100},device_scale_factor=1)
 errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://127.0.0.1:8000',wait_until='networkidle')
 assert page.locator('#overview.active').count()==1
 page.screenshot(path=str(ROOT/'docs/GUI-工作台.png'),full_page=True)
 page.click('nav [data-page="analysis"]')
 page.click('[data-years="30"]')
 assert '[1995-01-01, 2025-01-01)' in page.locator('#windowPreview').inner_text()
 page.fill('#end','2020-02-29')
 page.fill('#start','2019-03-01')
 assert '[1990-02-28, 2020-02-29)' in page.locator('#windowPreview').inner_text()
 page.fill('#start','2024-01-01');page.fill('#end','2025-01-01')
 page.click('#configForm button[type="submit"]')
 assert page.locator('#charts.active').count()==1
 for key in ['frequency','rose','longterm','monthly']:
  page.click(f'[data-chart="{key}"]')
  assert page.locator('#mainChart svg').count()==1
 with page.expect_download() as d:page.click('#csvDownload')
 assert d.value.suggested_filename.endswith('.csv')
 page.click('nav [data-page="data"]')
 sample=b'timestamp,wind_speed,wind_direction,qc_flag\n2024-01-01 00:00,6,350,0\n2024-01-01 00:10,8,10,0\n2024-01-01 00:20,10,90,1\n2024-01-01 00:40,4,180,0\n'
 page.set_input_files('#file',{'name':'sample.csv','mimeType':'text/csv','buffer':sample})
 page.click('#inspect')
 r=page.evaluate('localResult')
 assert r['expected']==5 and r['observed']==4 and r['valid']==3 and r['missing']==1,r
 assert r['mean']==6 and r['validRate']==.6 and r['observedRate']==.8,r
 page.click('nav [data-page="charts"]')
 assert page.locator('#sourceBadge').inner_text()=='真实导入'
 assert page.locator('#chartTable').inner_text().count('无样本')==11
 page.click('[data-chart="rose"]')
 assert page.locator('#mainChart svg').count()==1
 page.click('nav [data-page="report"]')
 page.click('[data-chapter="3"]')
 assert 'sample.csv' in page.locator('#chapterBody').inner_text()
 page.screenshot(path=str(ROOT/'docs/GUI-报告工作室.png'),full_page=True)
 with page.expect_download() as d:page.click('#reportDownload')
 data=Path(d.value.path()).read_text()
 assert '2.10' in data and '<mark>' in data and 'sample.csv' in data
 with page.expect_download() as d:page.click('nav [data-page="analysis"]');page.click('#configDownload')
 assert 'trailing_calendar_years' in Path(d.value.path()).read_text()
 page.click('nav [data-page="data"]')
 page.set_input_files('#file',{'name':'unsupported.xlsx','mimeType':'application/octet-stream','buffer':b'fake'})
 assert '未导入成功' in page.locator('#fileStatus').inner_text()
 # Duplicate, bad timestamp, missing speed, and off-grid rows stay distinct.
 edge=b'timestamp,wind_speed\n2024-01-01 00:00,6\n2024-01-01 00:00,7\n2024-01-01 00:05,9\n2024-01-01 00:10,\nbad,2\n2024-01-01 00:20,4\n'
 page.set_input_files('#file',{'name':'edge.csv','mimeType':'text/csv','buffer':edge});page.click('#inspect')
 r=page.evaluate('localResult')
 assert r['duplicates']==1 and r['badTime']==1 and r['offgrid']==1 and r['valid']==2 and r['expected']==3,r
 # Filename and cell text are escaped in generated previews.
 page.set_input_files('#file',{'name':'<img src=x onerror=alert(1)>.csv','mimeType':'text/csv','buffer':sample});page.click('#inspect')
 assert page.locator('#preflight img').count()==0
 page.set_viewport_size({'width':390,'height':844})
 for key in ['overview','data','analysis','charts','report','standards']:
  page.click(f'nav [data-page="{key}"]')
  assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),key
 page.screenshot(path=str(ROOT/'docs/GUI-移动端.png'),full_page=True)
 assert not errors,errors
 browser.close()
 print('PASS: navigation, date windows/leap day, CSV mapping/statistics, edge rows, chart/table source, downloads, XLSX limitation, escaping, six mobile pages; no browser errors.')
