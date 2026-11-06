'use strict';
const assert=require('node:assert/strict'),C=require('../gui/channel-library.js'),S=require('../gui/standard-channels.js'),W=require('../gui/data-core.js');
for(const [n,k]of [['原始数据.csv','raw'],['质控后数据.xlsx','qc'],['删除标记后数据.txt','qc'],['结果数据.csv','final'],['中尺度数据.csv','mesoscale']])assert.equal(S.stage(n),k);
assert.equal(S.stage('不明确.csv'),'');assert.equal(S.stage('原始数据_中尺度.csv'),'');
const hs=['time','WS_100m_Avg','WS_100m_Std','WD_100m','WPD_100m(W/m2)','Temp_10m_°C','RH_80m_%','WS_100m_Avg_sensor2','说明'];
const cat=C.identify(hs),schema=S.schema(cat,{time:0,ignored:[8]});assert.deepEqual(schema.slice(0,7).map(c=>c.standard),['TIME','WS-100m','WS-100m-STD','WD-100m','WPD-100m','TEMP-10m','RH-80m']);assert.ok(schema[7].standard!=='WS-100m');assert.equal(schema[8].standard,null);assert.equal(schema[8].original,'说明');assert.equal(new Set(schema.filter(c=>c.standard).map(c=>c.standard)).size,8);
assert.equal(C.identifyOne('WPD-100m').element,'wind_power_density');assert.equal(C.identifyOne('WindPowerDensity100m(W/m²)').element,'wind_power_density');
assert.equal(W.detect(['time','WS100m','WPD100m(W/m2)']).parameterChannels[0].element,'wind_power_density');
console.log('PASS: four category filenames, ambiguity rejection, WS/WD/WPD canonical names, statistical suffixes, duplicate disambiguation, original/ignored preservation and WPD channel recognition.');
