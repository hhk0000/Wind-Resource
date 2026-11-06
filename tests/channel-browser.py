"""Keyword recognition integrated with the V0.7 automatic upload flow."""
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 page=b.new_page(viewport={'width':1550,'height':1100});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://127.0.0.1:8000',wait_until='networkidle');page.click('nav [data-page="data"]')
 headers=['time','WS80m_Avg_m/s','WS80m_Std_m/s','WS80m_Max_m/s','WS80m_Min_m/s','WS100m_Avg_m/s','WD80m_deg','Temp10m_°C','Pressure10m_hPa','RH10m_%','Voltage_Avg','WindSpeed80m_TI','Reliability_%']
 data=(','.join(headers)+'\n'+'2024-01-01 00:00,6,1,10,2,7,270,20,1000,50,12,0.1,99\n'+'2024-01-01 01:00,8,2,11,3,9,90,21,990,60,12,0.2,99\n').encode()
 page.set_input_files('[data-single-stage="raw"]',{'name':'任意厂家名称.csv','mimeType':'text/csv','buffer':data})
 page.wait_for_function('realDatasets.raw!==null')
 assert page.evaluate('realDatasets.raw.channels.length')==2
 assert page.evaluate('realDatasets.raw.rows[0].values[0].stddev')==1
 assert page.evaluate('realDatasets.raw.rows[0].parameters')==[293.15,100000,.5]
 assert page.evaluate('realDatasets.raw.standardHeaders[1].standard')=='WS-80m'
 assert page.evaluate('realDatasets.raw.standardHeaders[11].standard') is None
 page.click('[data-map-stage="raw"]');assert page.locator('#channelMappingDialog').is_visible()
 page.click('#channelMappingDialog [value="close"]')
 page.click('#keywordLibrary summary')
 with page.expect_download() as d:page.click('#exportKeywordLibrary')
 text=Path(d.value.path()).read_text();assert 'Inner Temperature' in text and 'WPD' in text
 assert not errors,errors
 b.close();print('PASS: automatic keyword-based upload, mean/std separation, multiheight ancillary values, standard names, exclusion preservation and dictionary JSON export.')
