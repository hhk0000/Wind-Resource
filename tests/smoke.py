"""V0.2 functional browser validation; requires system Chromium and Playwright."""
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 page=browser.new_page(viewport={'width':1550,'height':1080},device_scale_factor=1)
 errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://127.0.0.1:8000',wait_until='networkidle')
 assert page.locator('nav button').count()==5
 assert page.locator('#overview.active').count()==1
 page.fill('#projectName','山地风电评估 · 界面验收')
 page.fill('#region','示例区域');page.fill('#capacity','75');page.fill('#projectNotes','安装资料待补')
 page.click('#projectForm button[type=submit]')
 assert '界面验收' in page.locator('#projectNameDisplay').inner_text()
 page.screenshot(path=str(ROOT/'docs/GUI-V02-项目信息.png'),full_page=True)
 page.click('nav [data-page="analysis"]');page.click('[data-years="30"]')
 assert '[1995-01-01, 2025-01-01)' in page.locator('#windowPreview').inner_text()
 page.fill('#end','2020-02-29');page.fill('#start','2019-03-01')
 assert '[1990-02-28, 2020-02-29)' in page.locator('#windowPreview').inner_text()
 page.fill('#start','2024-01-01');page.fill('#end','2025-01-01')
 page.select_option('#densityMethod','mesoscale')
 with page.expect_download() as d:page.click('#configDownload')
 data=Path(d.value.path()).read_text();assert 'mesoscale' in data and 'trailing_calendar_years' in data
 page.click('#configForm button[type=submit]')
 assert page.locator('#charts.active').count()==1
 ids=page.locator('[data-chart]').evaluate_all('(es)=>es.map(e=>e.dataset.chart)')
 assert len(ids)==13,ids
 for key in ids:
  page.click(f'[data-chart="{key}"]')
  assert page.locator('#mainChart svg').count()==1,key
  assert page.locator('#sourceBadge').inner_text()=='合成示例',key
  assert page.locator('#chartTable tr').count()>1,key
 page.click('[data-chart="correlation"]');page.select_option('#corrSector','4')
 assert '25 个合成点' in page.locator('#chartStats').inner_text()
 page.evaluate("window.scrollTo(0,0);document.querySelector('#toast').style.display='none'");page.wait_for_timeout(120)
 page.screenshot(path=str(ROOT/'docs/GUI-V02-相关性散点.png'),full_page=True)
 page.click('[data-chart="density"]')
 page.click('#toggleTable');page.evaluate("window.scrollTo(0,0)");page.wait_for_timeout(120)
 page.screenshot(path=str(ROOT/'docs/GUI-V02-图表中心.png'),full_page=True)
 page.click('#toggleTable')
 with page.expect_download() as d:page.click('#svgDownload')
 assert '合成示例' in Path(d.value.path()).read_text()
 with page.expect_download() as d:page.click('#csvDownload')
 assert '合成示例' in Path(d.value.path()).read_text()
 page.fill('#chartSearch','威布尔');assert page.locator('[data-chart]').count()==1
 page.fill('#chartSearch','Weibull');assert page.locator('[data-chart]').count()==1
 page.fill('#chartSearch','')
 page.click('nav [data-page="data"]')
 sample=b'timestamp,wind_speed,wind_direction,qc_flag\n2024-01-01 00:00,6,350,0\n2024-01-01 00:10,8,10,0\n2024-01-01 00:20,10,90,1\n2024-01-01 00:40,4,180,0\n'
 page.set_input_files('#file',{'name':'sample.csv','mimeType':'text/csv','buffer':sample});page.click('#inspect')
 r=page.evaluate('localResult');assert (r['expected'],r['observed'],r['valid'],r['mean'])==(5,4,3,6)
 page.click('nav [data-page="charts"]')
 page.click('[data-chart="monthly"]');assert page.locator('#sourceBadge').inner_text()=='真实导入'
 assert page.locator('#chartTable').inner_text().count('无样本')==11
 for key in ['daily','annual','frequency','rose']:
  page.click(f'[data-chart="{key}"]');assert page.locator('#mainChart svg').count()==1,key
 page.select_option('#vizStage','mesoscale')
 assert '所选阶段尚无可用结果' in page.locator('#mainChart').inner_text()
 page.select_option('#vizStage','raw')
 for key in ['density','shear','weibull','correlation','power','energyRose','turbulence','longterm']:
  page.click(f'[data-chart="{key}"]');assert page.locator('#mainChart svg').count()==0,key
  assert page.locator('#svgDownload').is_disabled(),key
 page.click('#showExample');assert page.locator('#mainChart svg').count()==1
 page.click('#jumpReport');assert page.locator('#report.active').count()==1
 page.click('[data-chapter="4"]');page.click('[data-report-graph="shear"]')
 assert '切变' in page.locator('#chartTitle').inner_text()
 page.click('nav [data-page="report"]');page.click('[data-chapter="0"]')
 assert '界面验收' in page.locator('#chapterBody').inner_text()
 with page.expect_download() as d:page.click('#reportDownload')
 html=Path(d.value.path()).read_text();assert '2.10' in html and '图表位置待绑定' in html and '<mark>' in html
 assert 'data-report-graph=' not in html
 page.evaluate("window.scrollTo(0,0);document.querySelector('#toast').style.display='none'");page.wait_for_timeout(120)
 page.screenshot(path=str(ROOT/'docs/GUI-V02-报告预览.png'),full_page=True)
 page.click('nav [data-page="data"]')
 page.set_input_files('#file',{'name':'unsupported.xlsx','mimeType':'application/octet-stream','buffer':b'fake'})
 assert '未导入成功' in page.locator('#fileStatus').inner_text()
 edge=b'timestamp,wind_speed\n2024-01-01 00:00,6\n2024-01-01 00:00,7\n2024-01-01 00:05,9\n2024-01-01 00:10,\nbad,2\n2024-01-01 00:20,4\n'
 page.set_input_files('#file',{'name':'edge.csv','mimeType':'text/csv','buffer':edge});page.click('#inspect')
 r=page.evaluate('localResult');assert (r['duplicates'],r['badTime'],r['offgrid'],r['valid'])==(1,1,1,2)
 page.set_viewport_size({'width':390,'height':844})
 for key in ['overview','data','analysis','charts','report']:
  page.click(f'nav [data-page="{key}"]')
  assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),key
 page.click('nav [data-page="charts"]')
 page.screenshot(path=str(ROOT/'docs/GUI-V02-移动端.png'),full_page=True)
 offline=browser.new_page()
 offline_errors=[];offline.on('pageerror',lambda e:offline_errors.append(str(e)))
 offline.route('**/standalone.html',lambda route:route.fulfill(status=200,content_type='text/html',body=(ROOT/'dist/风序-GUI.html').read_text()))
 offline.goto('http://127.0.0.1:8000/standalone.html',wait_until='load')
 offline.click('nav [data-page="charts"]');offline.click('[data-chart="weibull"]')
 assert offline.locator('#mainChart svg').count()==1
 assert '0.2.0-prototype' in offline.locator('.appfooter').inner_text()
 assert not offline_errors,offline_errors
 assert not errors,errors
 browser.close()
 print('PASS: five pages, project/report sync, 13 charts, source/stage guards, CSV statistics, config, leap day, sector filter, SVG/CSV/HTML downloads, report navigation, mobile layout; no script errors.')
