"""V0.4 workspace, archival isolation and A–D visualization checks."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 context=b.new_context(viewport={'width':1550,'height':1080});page=context.new_page();errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://127.0.0.1:8000',wait_until='networkidle')
 assert page.locator('nav button').count()==5
 assert page.locator('#overview #projectForm').count()==0
 assert page.locator('#analysis #projectForm').count()==1
 page.click('#newProject');page.fill('#projectName','山地项目 · 归档验收');page.fill('#region','示例地区')
 page.fill('#capacity','75');page.fill('#turbineCount','12');page.fill('#height','125')
 page.click('#projectForm button[type=submit]')
 assert page.evaluate('projectRecords.length')==1
 page.click('#configForm button[type=submit]')
 assert page.locator('#charts.active').count()==1
 assert page.locator('[data-board]').count()==4
 assert page.locator('[data-chart]').count()==2
 page.click('[data-board="A"]');assert page.locator('#v03Composition svg').count()==2
 before=page.evaluate('currentRows[0][1]')
 page.select_option('#vizObject','hub')
 assert page.evaluate('currentRows[0][1]')!=before
 page.fill('#previewStart','2024-01-01');page.fill('#previewEnd','2025-01-01');page.click('#applyPreview')
 assert page.evaluate('currentRows.length')==12
 page.select_option('#previewSource','mast')
 assert page.locator('[data-v04-series]').count()==4
 assert page.locator('#v03Composition svg').count()==3
 page.locator('[data-v04-series="1"]').uncheck()
 assert page.evaluate('v03State.visible[1]') is False
 page.click('[data-board="B"]')
 assert page.locator('[data-chart]').count()==1
 assert '参证气象站资料：未提供' in page.locator('#v03Composition').inner_text()
 page.check('#stationDemo')
 assert page.locator('#v03Composition svg').count()==2
 assert page.locator('#v03Composition table').count()==2
 page.uncheck('#stationDemo');assert page.locator('#v03Composition table').count()==1
 page.click('[data-board="C"]');page.select_option('#v03SectorCount','12')
 n_before=page.evaluate('correlationPoints().length')
 page.fill('#previewStart','2024-06-01');page.fill('#previewEnd','2024-07-01');page.click('#applyPreview')
 assert 1<page.evaluate('correlationPoints().length')<n_before
 page.fill('#previewStart','2026-01-01');page.fill('#previewEnd','2026-02-01');page.click('#applyPreview')
 assert '不足' in page.locator('#v03Composition').inner_text()
 page.fill('#previewStart','2024-01-01');page.fill('#previewEnd','2025-01-01');page.click('#applyPreview')
 page.select_option('#v03Baseline','10');assert '近10年' in page.locator('.inlineFormula').inner_text()
 page.click('[data-board="D"]')
 ids=page.locator('[data-chart]').evaluate_all('(es)=>es.map(e=>e.dataset.chart)')
 assert ids==['shear','turbulence','monthly','daily','frequency','weibull','rose','energyRose']
 for key in ids:
  page.click(f'[data-chart="{key}"]');assert page.locator('#v03Composition svg,#mainChart svg').count()>0,key
  assert page.evaluate("""()=>{const r=document.querySelector('#v03Composition');if(!r)return true;const g=r.querySelector('svg'),t=r.querySelector('table'),rules=r.querySelector('.presentationRules');return !!rules&&(!t||(g.compareDocumentPosition(t)&Node.DOCUMENT_POSITION_FOLLOWING)&&(t.compareDocumentPosition(rules)&Node.DOCUMENT_POSITION_FOLLOWING));}"""),key
 page.click('[data-board="A"]');page.evaluate("window.scrollTo(0,0);document.querySelector('#toast').style.display='none'")
 page.screenshot(path=str(ROOT/'dist/验收-图表看板.png'),full_page=True)
 page.click('nav [data-page="data"]')
 sample=b'timestamp,wind_speed,wind_direction,qc_flag\n2024-01-01 00:00,6,350,0\n2024-01-01 00:10,8,10,0\n2024-01-01 00:20,10,90,1\n2024-01-01 00:40,4,180,0\n'
 page.set_input_files('#file',{'name':'sample.csv','mimeType':'text/csv','buffer':sample});page.click('#inspect')
 assert page.evaluate('localResult.mean')==6
 page.click('nav [data-page="charts"]');page.click('[data-board="D"]');page.click('[data-chart="monthly"]')
 page.select_option('#chartSource','imported');assert page.locator('#sourceBadge').inner_text()=='真实导入'
 page.click('nav [data-page="overview"]');page.click('#completeProject')
 assert page.evaluate("projectRecords[0].status")=='completed'
 assert page.locator('#completeProject').is_disabled()
 page.fill('#projectSearch','不存在');assert '没有符合条件' in page.locator('#projectArchiveList').inner_text()
 page.fill('#projectSearch','归档验收');assert page.locator('[data-open-project]').count()==1
 with page.expect_download() as d:page.click('#archiveExport')
 data=json.loads(Path(d.value.path()).read_text());assert data['projects'][0]['fields']['turbineCount']=='12'
 assert 'report_text' in data['projects'][0]
 page.reload(wait_until='networkidle')
 page.click('nav [data-page="overview"]');assert page.locator('[data-open-project]').count()==1
 page.click('[data-open-project]');assert page.locator('#report.active').count()==1
 assert page.locator('#turbineCount').is_disabled()
 assert page.evaluate('localResult') is None
 assert '本地归档' in page.locator('#reportArchiveTag').inner_text()
 with page.expect_download() as d:page.click('#reportDownload')
 html=Path(d.value.path()).read_text();assert '归档验收' in html and '本地归档文字快照' in html
 assert page.locator('#reportType option:not([disabled])').count()==1
 page.click('nav [data-page="overview"]');page.evaluate("window.scrollTo(0,0);document.querySelector('#toast').style.display='none'")
 page.screenshot(path=str(ROOT/'dist/验收-项目档案.png'),full_page=True)
 page.click('#cloneProject');page.fill('#projectName','副本项目');page.click('#projectForm button[type=submit]')
 assert page.evaluate('projectRecords.length')==2
 assert page.evaluate("projectRecords.filter(r=>r.status==='completed').length")==1
 assert page.locator('#turbineCount').is_enabled()
 page.set_viewport_size({'width':390,'height':844})
 for key in ['overview','data','analysis','charts','report']:
  page.click(f'nav [data-page="{key}"]');assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),key
 page.click('nav [data-page="charts"]')
 for board in 'ABCD':
  page.click(f'[data-board="{board}"]');assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),board
 offline=b.new_page();offline.on('pageerror',lambda e:errors.append(str(e)))
 offline.route('**/standalone.html',lambda route:route.fulfill(status=200,content_type='text/html',body=(ROOT/'dist/风序-GUI.html').read_text()))
 offline.goto('http://127.0.0.1:8000/standalone.html',wait_until='load');offline.click('nav [data-page="charts"]')
 assert offline.locator('[data-board]').count()==4
 assert '0.5.0' in offline.locator('.appfooter').inner_text()
 assert not errors,errors
 b.close();print('PASS: five modules, project metadata/counts, archive/search/reload/clone, no cross-project data leak, A–D boards, preview height/time, optional station, regression range and empty samples, charts/tables/rules, export, imported statistics, mobile and offline GUI.')
