from pathlib import Path
from io import BytesIO
from openpyxl import Workbook
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 page=b.new_page(viewport={'width':1550,'height':1080});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://127.0.0.1:8000',wait_until='networkidle');page.click('nav [data-page="data"]')
 text='DateTime,WS,WS,WD\n,80m,100m,80m\n,m/s,m/s,deg\n2024-01-01 00:00,6,7,270\n2024-01-01 01:00,7,8,280'
 page.set_input_files('[data-single-stage="raw"]',{'name':'厂家多行.csv','mimeType':'text/csv','buffer':text.encode()})
 page.wait_for_function('realDatasets.raw!==null')
 assert page.evaluate('realDatasets.raw.channels.map(c=>c.height)')==[80,100]
 assert page.evaluate('realDatasets.raw.standardHeaders[1].original')=='WS'
 assert page.evaluate('realDatasets.raw.standardHeaders[1].headerParts')==['WS','80m','m/s']
 # UTF16 Excel-text variant with a whitespace-delimited timestamp.
 wide='DateTime  WS80m  WD80m\n2024-01-01 00:00  6  270\n2024-01-01 01:00  7  280'
 page.set_input_files('[data-single-stage="qc"]',{'name':'Unicode.txt','mimeType':'text/plain','buffer':wide.encode('utf-16')})
 page.wait_for_function('realDatasets.qc!==null');assert page.evaluate('uploadTasks.get("qc").encoding')=='utf-16le'
 # A pre-recognition failure has a repair button and can proceed to mandatory mapping.
 dup=b'time,WS80m,WS80m\n2024-01-01 00:00,6,7\n2024-01-01 01:00,7,8'
 page.set_input_files('[data-single-stage="final"]',{'name':'repeat.csv','mimeType':'text/csv','buffer':dup})
 page.wait_for_function('uploadTasks.get("final").status==="error"')
 page.click('[data-repair-stage="final"]');assert 'WS80m' in page.locator('#repairPreview').inner_text()
 page.check('#repairDuplicates');page.select_option('#repairDelimiter',',');page.click('#applyParseRepair')
 page.wait_for_selector('#channelMappingDialog[open]')
 page.uncheck('[data-modal-column="2"] [data-modal-field="primary"]')
 page.click('#confirmChannelMapping');page.wait_for_function('realDatasets.final!==null')
 assert page.evaluate('realDatasets.final.channels.length')==1
 # Locale date format can be corrected after a normalization failure.
 locale=b'time,WS80m\n31/12/2024 00:00,6\n31/12/2024 01:00,8'
 page.set_input_files('[data-single-stage="mesoscale"]',{'name':'date.csv','mimeType':'text/csv','buffer':locale})
 page.wait_for_function('uploadTasks.get("mesoscale").status==="error"')
 page.click('[data-map-stage="mesoscale"]');page.select_option('#dialogDateFormat','dmy');page.click('#confirmChannelMapping')
 page.wait_for_function('realDatasets.mesoscale!==null')
 assert page.evaluate('WindData.fmt(realDatasets.mesoscale.start,8)')=='2024-12-31 00:00:00'
 # Duplicate Excel labels must reach mapping instead of failing before a table exists.
 wb=Workbook();ws=wb.active;ws.append(['time','WS80m','WS80m']);ws.append(['2024-01-01 00:00',6,7]);ws.append(['2024-01-01 01:00',7,8]);buf=BytesIO();wb.save(buf)
 page.set_input_files('[data-single-stage="raw"]',{'name':'repeat.xlsx','mimeType':'application/octet-stream','buffer':buf.getvalue()})
 page.wait_for_selector('#channelMappingDialog[open]');page.uncheck('[data-modal-column="2"] [data-modal-field="primary"]');page.click('#confirmChannelMapping')
 page.wait_for_function('realDatasets.raw.file==="repeat.xlsx"')
 assert page.evaluate('realDatasets.raw.channels.length')==1
 assert not errors,errors
 b.close();print('PASS: automatic multirow and UTF16 space TXT, raw source header provenance, parsing repair before mapping, duplicate primary selection and date-format recovery.')
