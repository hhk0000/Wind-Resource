"""V0.7 four-row upload, programmatic matching and mandatory manual mapping dialog."""
from pathlib import Path
from datetime import datetime,timedelta
from tempfile import TemporaryDirectory
import json
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with TemporaryDirectory(prefix='wind-flow-') as temp:
 d=Path(temp)
 def fixture(name,start,end,speed):
  p=d/name
  with p.open('w') as f:
   f.write('time,WS_100m_Avg(m/s),WS_100m_Std(m/s),WD_100m(deg),WPD_100m(W/m2)\n')
   while start<end:
    f.write(f'{start:%Y-%m-%d %H:%M},{speed},1,270,100\n');start+=timedelta(days=1)
  return str(p)
 a,z=datetime(2024,1,1),datetime(2025,1,1)
 files=[fixture('原始数据.csv',a,z,6),fixture('删除标记后数据.csv',a,z,6),fixture('结果数据.csv',a,z,7),fixture('中尺度数据.csv',datetime(1995,1,1),z,8)]
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
  page=b.new_page(viewport={'width':1550,'height':1100});errors=[];requests=[]
  page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:requests.append(r.url))
  page.goto('http://127.0.0.1:8000',wait_until='networkidle');page.click('nav [data-page="data"]')
  assert page.locator('[data-upload-row]').count()==4
  page.set_input_files('#batchWindFiles',files)
  page.wait_for_function('Object.values(realDatasets).every(Boolean)',timeout=60000)
  assert not page.locator('#channelMappingDialog').is_visible()
  assert page.evaluate('realDatasets.raw.channels[0].name')=='WS-100m'
  assert page.evaluate('realDatasets.raw.parameterChannels[0].standardName')=='WPD-100m'
  with page.expect_download() as download:page.click('[data-schema-stage="raw"]')
  mapping=json.loads(Path(download.value.path()).read_text());assert mapping['columns'][1]['original']=='WS_100m_Avg(m/s)';assert mapping['columns'][1]['standard']=='WS-100m'
  with page.expect_download() as download:page.click('[data-csv-stage="raw"]')
  assert '"TIME","WS-100m","WS-100m-STD","WD-100m","WPD-100m"' in Path(download.value.path()).read_text()
  page.click('#goRealOverview');assert page.locator('#sourceBadge').inner_text()=='真实数据'
  page.select_option('#realWindow','30');assert '完整覆盖' in page.locator('#v03Composition').inner_text()
  page.click('nav [data-page="data"]');page.click('[data-remove-stage="final"]')
  assert page.evaluate('realDatasets.final') is None
  assert page.evaluate('realDatasets.raw!==null&&realDatasets.qc!==null')
  page.click('#goRealOverview');page.select_option('#previewSource','mesoscale')
  assert page.locator('#sourceBadge').inner_text()=='真实资料 · 待补'
  page.click('nav [data-page="data"]')
  page.set_input_files('[data-single-stage="final"]',{'name':'任意名称.csv','mimeType':'text/csv','buffer':Path(files[2]).read_bytes()})
  page.wait_for_function('realDatasets.final!==null')
  assert page.evaluate('realDatasets.final.file')=='任意名称.csv'
  # A valid batch filename never silently assigns an unknown filename.
  page.set_input_files('#batchWindFiles',{'name':'不知道类型.csv','mimeType':'text/csv','buffer':Path(files[0]).read_bytes()})
  assert '无法唯一识别文件名' in page.locator('#uploadFlowStatus').inner_text()
  assert page.evaluate('realDatasets.final.file')=='任意名称.csv'
  # Unknown fields require an explicit local mapping dialog.
  generic=b'Moment,Signal,Heading,Power,Comment,Temperature10m_degree C\n2024-01-01 00:00,5,270,100,station,-2\n2024-01-01 01:00,7,90,110,station,-1\n'
  page.set_input_files('[data-single-stage="raw"]',{'name':'厂家任意名称.csv','mimeType':'text/csv','buffer':generic})
  page.wait_for_selector('#channelMappingDialog[open]')
  assert page.evaluate('realDatasets.raw.file')=='原始数据.csv'
  page.select_option('#dialogTime','0')
  for i,element in [(1,'wind_speed'),(2,'wind_direction'),(3,'wind_power_density')]:
   page.select_option(f'[data-modal-column="{i}"] [data-modal-field="element"]',element)
   page.fill(f'[data-modal-column="{i}"] [data-modal-field="height"]','100')
  page.select_option('[data-modal-column="4"] [data-modal-field="element"]','ignore')
  assert page.locator('[data-modal-column="1"] .standardNameCell').inner_text()=='WS-100m'
  page.click('#confirmChannelMapping');page.wait_for_function('realDatasets.raw.file==="厂家任意名称.csv"')
  assert not page.locator('#channelMappingDialog').is_visible()
  assert page.evaluate('realDatasets.raw.channels[0].name')=='WS-100m'
  assert page.evaluate('realDatasets.raw.rows[0].values[0].v')==5
  # A failed replacement preserves both the previous dataset and export source.
  page.set_input_files('[data-single-stage="raw"]',{'name':'bad.csv','mimeType':'text/csv','buffer':b'time,WS100m\nbad,6\nwrong,7\n'})
  page.wait_for_function('uploadTasks.get("raw").status==="error"')
  assert page.evaluate('realDatasets.raw.file')=='厂家任意名称.csv'
  with page.expect_download() as download:page.click('[data-csv-stage="raw"]')
  assert ',"5"' in Path(download.value.path()).read_text()
  assert ',"-2"' in Path(download.value.path()).read_text()
  # Delete an unresolved file after deferring the dialog, and upload another file.
  page.set_input_files('[data-single-stage="qc"]',{'name':'unknown.csv','mimeType':'text/csv','buffer':generic})
  page.wait_for_selector('#channelMappingDialog[open]');page.click('#channelMappingDialog [value="close"]')
  page.click('[data-remove-stage="qc"]');assert page.evaluate('realDatasets.qc') is None
  page.set_input_files('[data-single-stage="qc"]',{'name':'重新上传.csv','mimeType':'text/csv','buffer':Path(files[1]).read_bytes()})
  page.wait_for_function('realDatasets.qc!==null')
  page.evaluate("window.scrollTo(0,0);document.querySelector('#toast').style.display='none'")
  page.screenshot(path=str(ROOT/'docs/GUI-V07-四类上传清单.png'),full_page=True)
  page.set_viewport_size({'width':390,'height':844})
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  for stage in ['raw','qc','final','mesoscale']:page.click(f'[data-remove-stage="{stage}"]')
  assert page.locator('#chartSource').input_value()=='imported'
  page.click('nav [data-page="charts"]');assert page.locator('#sourceBadge').inner_text()!='合成示例'
  page.click('nav [data-page="overview"]');page.click('#newProject')
  assert page.evaluate('uploadTasks.size')==0
  assert page.evaluate('Object.values(realDatasets).every(x=>x===null)')
  assert all(url.startswith('http://127.0.0.1:8000/') for url in requests),requests
  assert not errors,errors
  b.close();print('PASS: batch category names, four-row list, independent delete/reupload, arbitrary single filename, mandatory mapping/ignore dialog, WS/WD/WPD aliases, raw header retention, downloads, failure rollback, project isolation and no external requests.')
