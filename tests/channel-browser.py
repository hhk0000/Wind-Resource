"""Keyword library UI integration, override audit and statistic-safe import."""
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 page=b.new_page(viewport={'width':1550,'height':1100});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://127.0.0.1:8000',wait_until='networkidle');page.click('nav [data-page="data"]')
 headers=['time','WS80m_Avg_m/s','WS80m_Std_m/s','WS80m_Max_m/s','WS80m_Min_m/s','WS100m_Avg_m/s','WD80m_deg','Temp10m_°C','Pressure10m_hPa','RH10m_%','Voltage_Avg','WindSpeed80m_TI','Reliability_%']
 data=(','.join(headers)+'\n'+'2024-01-01 00:00,6,1,10,2,7,270,20,1000,50,12,0.1,99\n'+'2024-01-01 01:00,8,2,11,3,9,90,21,990,60,12,0.2,99\n').encode()
 page.set_input_files('#realFiles',{'name':'raw_channels.csv','mimeType':'text/csv','buffer':data})
 page.wait_for_function('importEntries.length===1&&!importBusy')
 assert page.locator('.recognitionTable tbody tr').count()==len(headers)
 assert '已排除' in page.locator('[data-recognition-column="11"]').inner_text()
 assert '已排除' in page.locator('[data-recognition-column="12"]').inner_text()
 page.click('#commitRealFiles');page.wait_for_function('!importBusy')
 assert page.evaluate('realDatasets.raw.channels.length')==2
 assert page.evaluate('realDatasets.raw.rows[0].values[0].v')==6
 assert page.evaluate('realDatasets.raw.rows[0].values[0].stddev')==1
 assert page.evaluate('realDatasets.raw.rows[0].parameters')==[293.15,100000,0.5]
 page.click('nav [data-page="data"]')
 page.select_option('[data-field="speed"]','3')
 page.click('#commitRealFiles');page.wait_for_function('!importBusy')
 assert '标准差/极值' in page.locator('#realImportStatus').inner_text()
 assert page.evaluate('realDatasets.raw.rows[0].values[0].v')==6
 generic=b'time,Signal\n2024-01-01 00:00,5\n2024-01-01 01:00,7\n'
 page.set_input_files('#realFiles',{'name':'raw_manual.csv','mimeType':'text/csv','buffer':generic})
 page.wait_for_function('importEntries.length===1&&!importBusy')
 page.select_option('[data-recognition-column="1"] [data-channel-override="element"]','wind_speed')
 page.fill('[data-recognition-column="1"] [data-channel-override="height"]','125')
 page.locator('[data-recognition-column="1"] [data-channel-override="height"]').blur()
 assert '人工确认' in page.locator('[data-recognition-column="1"]').inner_text()
 page.click('#commitRealFiles');page.wait_for_function('!importBusy')
 assert page.evaluate('realDatasets.raw.channels[0].height')==125
 assert page.evaluate('realDatasets.raw.catalog[1].manual') is True
 assert page.evaluate('realDatasets.raw.rows[0].values[0].v')==5
 page.click('nav [data-page="data"]');page.locator('#keywordLibrary summary').click()
 with page.expect_download() as d:page.click('#exportKeywordLibrary')
 text=Path(d.value.path()).read_text();assert 'Inner Temperature' in text and 'STDev' in text
 page.evaluate("window.scrollTo(0,0);document.querySelector('#toast').style.display='none'")
 page.screenshot(path=str(ROOT/'docs/GUI-V06-关键字通道识别.png'),full_page=True)
 page.set_viewport_size({'width':390,'height':844})
 assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 assert not errors,errors
 b.close();print('PASS: dictionary report, exclusion/mean/std separation, multiheight auxiliary extraction, unsafe max-column guard, per-column overrides, unit conversions, JSON library export and mobile layout.')
