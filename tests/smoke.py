"""Browser checks for V0.3 review compositions and existing import workflow."""
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 page=b.new_page(viewport={'width':1550,'height':1080});errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://127.0.0.1:8000',wait_until='networkidle')
 assert page.locator('nav button').count()==5
 page.fill('#projectName','组合图验收');page.click('#projectForm button[type=submit]')
 page.click('nav [data-page="charts"]')
 ids=page.locator('[data-chart]').evaluate_all('(es)=>es.map(e=>e.dataset.chart)')
 assert ids[:9]==['longterm','overviewLines','density','correlation','shear','turbulence','monthly','daily','frequency'],ids
 for key in ids:
  page.click(f'[data-chart="{key}"]')
  assert page.locator('#v03Composition svg,#mainChart svg').count()>0,key
 assert len(ids)==12
 # Ensure rendered chart groups precede tables, and all rules follow tables.
 for key in ids[:9]:
  page.click(f'[data-chart="{key}"]')
  assert page.evaluate("""()=>{
   const r=document.querySelector('#v03Composition');
   const graph=r.querySelector('svg'), table=r.querySelector('table'), rules=r.querySelector('.presentationRules');
   return !!graph && !!rules && (!table || !!(graph.compareDocumentPosition(table)&Node.DOCUMENT_POSITION_FOLLOWING)) && (!table || !!(table.compareDocumentPosition(rules)&Node.DOCUMENT_POSITION_FOLLOWING));
  }"""),key
 page.click('[data-chart="longterm"]');assert page.locator('#v03Composition svg').count()==2
 assert page.locator('#v03Composition table tr').count()==2
 page.click('[data-chart="overviewLines"]');assert page.locator('[data-series]').count()==4
 page.locator('[data-series="1"]').uncheck()
 assert page.evaluate('v03State.visible[1]') is False
 for i in [0,2,3]:page.locator(f'[data-series="{i}"]').uncheck()
 assert '所有曲线均已关闭' in page.locator('#v03Composition').inner_text()
 for i in range(4):page.locator(f'[data-series="{i}"]').check()
 page.click('[data-chart="density"]')
 assert page.locator('#v03Composition rect[fill="#e55757"]').count()==1
 assert page.locator('#v03Composition rect[fill="#29a77e"]').count()==12
 assert '平均值' in page.locator('#v03Composition table tr').last.inner_text()
 page.click('[data-chart="correlation"]')
 page.select_option('#v03SectorCount','12');page.select_option('#v03Sector','3')
 assert page.evaluate('v03State.sectorCount')==12
 assert 'n = ' in page.locator('.v03fit').inner_text()
 page.select_option('#v03SectorCount','1');assert page.locator('#v03Sector option').count()==1
 before=page.locator('.inlineFormula').inner_text()
 page.select_option('#v03Baseline','30');after=page.locator('.inlineFormula').inner_text()
 assert before!=after and '近30年' in after
 page.click('[data-chart="shear"]');assert page.locator('#v03Composition table tbody tr').count()==5
 page.click('[data-chart="turbulence"]');assert page.locator('#v03Composition table').count()==3
 assert '样本数' in page.locator('#v03Composition table').first.inner_text()
 page.click('[data-chart="monthly"]');assert page.locator('#v03Composition svg').count()==3
 assert page.locator('#v03Composition table th').count()==7
 page.click('[data-chart="daily"]');assert page.locator('#v03Composition table tbody tr').count()==24
 page.click('[data-chart="frequency"]');assert page.locator('#v03Composition svg').count()==3
 with page.expect_download() as d:page.click('#svgDownload')
 svg=Path(d.value.path()).read_text();assert '合成示例' in svg and svg.count('<svg')==4
 with page.expect_download() as d:page.click('#csvDownload')
 assert '125m风能频率' in Path(d.value.path()).read_text()
 page.click('[data-chart="correlation"]');page.evaluate("window.scrollTo(0,0);document.querySelector('#toast').style.display='none'")
 page.screenshot(path=str(ROOT/'docs/GUI-V03-相关性组合.png'),full_page=True)
 page.click('[data-chart="density"]');page.evaluate('window.scrollTo(0,0)')
 page.screenshot(path=str(ROOT/'docs/GUI-V03-空气密度.png'),full_page=True)
 page.click('nav [data-page="data"]')
 sample=b'timestamp,wind_speed,wind_direction,qc_flag\n2024-01-01 00:00,6,350,0\n2024-01-01 00:10,8,10,0\n2024-01-01 00:20,10,90,1\n2024-01-01 00:40,4,180,0\n'
 page.set_input_files('#file',{'name':'sample.csv','mimeType':'text/csv','buffer':sample});page.click('#inspect')
 r=page.evaluate('localResult');assert (r['expected'],r['valid'],r['mean'])==(5,3,6)
 page.click('nav [data-page="charts"]');page.click('[data-chart="monthly"]')
 assert page.locator('#sourceBadge').inner_text()=='真实导入'
 page.click('[data-chart="density"]');assert page.locator('#svgDownload').is_disabled()
 page.click('#showExample');assert page.locator('#v03Composition').count()==1
 page.click('#jumpReport');assert page.locator('#report.active').count()==1
 with page.expect_download() as d:page.click('#reportDownload')
 assert '组合图验收' in Path(d.value.path()).read_text()
 page.set_viewport_size({'width':390,'height':844})
 for key in ['overview','data','analysis','charts','report']:
  page.click(f'nav [data-page="{key}"]')
  assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),key
 page.click('nav [data-page="charts"]')
 for key in ids[:9]:
  page.click(f'[data-chart="{key}"]');assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),key
 offline=b.new_page();offline.on('pageerror',lambda e:errors.append(str(e)))
 offline.route('**/standalone.html',lambda route:route.fulfill(status=200,content_type='text/html',body=(ROOT/'dist/风序-GUI.html').read_text()))
 offline.goto('http://127.0.0.1:8000/standalone.html',wait_until='load')
 offline.click('nav [data-page="charts"]');offline.click('[data-chart="overviewLines"]')
 assert offline.locator('[data-series]').count()==4
 assert '0.3.1' in offline.locator('.appfooter').inner_text()
 assert not errors,errors
 b.close()
 print('PASS: chart order, four toggles/gaps, radar/year table, density colors/formula, 1/12/16 regression, baseline deviation, multiheight dual axes/tables, CSV/SVG/report downloads, real-source guard, mobile and offline GUI.')
