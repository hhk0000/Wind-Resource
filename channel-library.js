/* Versioned channel dictionary transcribed from the user's visible keyword table. */
(function(root){
'use strict';
const version='1.0.0';
const rules=[
 {id:'wind_speed',label:'风速',keywords:['speed','spd','WS','anemometer','m/s','风速','anem','sp'],exclude:['z方向','垂直','Z-Direction','Z-wind','vertical','VWindSpeed','TI']},
 {id:'wind_direction',label:'风向',keywords:['direction','Windvane','Dir','vane','WD','deg','°','º','风向'],exclude:['℃','°C','□C','Z-Direction','degree C']},
 {id:'temperature',label:'温度',keywords:['temperature','temp','Tmp','℃','°C','□C','_C','TP','外温','温度','degree C','tem','Ta'],exclude:['Inner Temperature','Int Temp','PTemp']},
 {id:'pressure',label:'气压',keywords:['Pres','Pa','mb','bp','气压','hPa','press','kpa','pressure','pr'],exclude:[]},
 {id:'humidity',label:'湿度',keywords:['humidity','rh','hr','%','hum','湿度','humi'],exclude:['可靠性','数据有效率','Reliability','Data Availability']},
 {id:'voltage',label:'电压',keywords:['v','volt','voltage'],exclude:['Avg','STDev','Deviation','Valid','Level','Data Availability','ver']},
 {id:'std',label:'标准差',keywords:['SD','STD','偏差','STDev','StdDev','standard deviation','标准差','标准偏差','水平风速标准差','Std','Deviation','sigma'],exclude:['Pressure','Temperature']},
 {id:'mean',label:'平均值',keywords:['mean','Avg'],exclude:['gust','Gust']},
 {id:'max',label:'最大值',keywords:['最大值','Maximum','Max','最大'],exclude:[]},
 {id:'min',label:'最小值',keywords:['最小值','Minimum','Min','最小'],exclude:[]}
];
const labels=Object.fromEntries(rules.map(r=>[r.id,r.label]));Object.assign(labels,{unknown:'未识别',u_component:'U分量',v_component:'V分量',gust:'阵风',ambiguous:'统计量冲突'});
function normalize(s){return String(s??'').normalize('NFKC').replace(/℃|□\s*C/g,'°C').replace(/º/g,'°').replace(/([a-z])([A-Z])/g,'$1 $2').replace(/([A-Z])([A-Z][a-z])/g,'$1 $2').toLowerCase().replace(/(^|[^a-z])([hk])\s+pa(?=$|[^a-z])/g,'$1$2pa').replace(/(^|[^a-z])m\s+v(?=$|[^a-z])/g,'$1mv')}
const compact=s=>normalize(s).replace(/[\s_\-]/g,'');
function hit(header,key){let h=normalize(header);const k=normalize(key);if(k==='min')h=h.replace(/\d+(?:\.\d+)?\s*min(?:utes?)?\b/g,' sampling_interval ');if(key==='_C')return /_c(?:$|[^a-z])/.test(h);if(/[^\x00-\x7f]/.test(k)||/[/%°]/.test(k)){
 if(k==='°')return /°(?!\s*c)/.test(h);if(k==='°c')return /°\s*c/.test(h);return h.includes(k);
 }
 // English words and abbreviations are tokens; adjacent heights are permitted,
 // so WS80 is matched, while sp does not match pressure or a random substring.
 const escaped=k.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
 if(/[\s_\-]/.test(k))return compact(h).includes(compact(k));
 return new RegExp('(?:^|[^a-z])'+escaped+'(?=$|[^a-z])','i').test(h);
}
function matched(h,list){return [...new Set(list.filter(k=>hit(h,k)))]}
function heightInfo(header,file=''){const h=normalize(header).replace(/(\d),(\d+)\s*(m|米)/g,'$1.$2$3');const explicit=[...h.matchAll(/(?:^|[^\d.])(\d{1,3}(?:\.\d+)?)\s*(?:m(?=$|[^a-z])|米)/g)].map(m=>+m[1]);const unique=[...new Set(explicit)];if(unique.length===1)return {height:unique[0],heightSource:'表头显式高度'};if(unique.length>1)return {height:null,heightSource:'表头存在多个高度，需确认'};
 const m=h.match(/(?:^|[^a-z])(?:ws|wd|spd|speed|direction|anemometer|anem|temperature|temp|pressure|pres|humidity|rh|voltage|u|v)[ _-]?(\d{1,3}(?:\.\d+)?)(?![\d.]|\s*(?:min|sec|hz))(?:$|[^\d])/);if(m&&+m[1]>=5)return {height:+m[1],heightSource:'紧凑通道名推断，需核对'};
 const f=String(file).match(/(?:^|[^\d.])(\d{1,3}(?:\.\d+)?)\s*(?:m(?=$|[^a-z])|米)/i);return f?{height:+f[1],heightSource:'文件名推断，需核对'}:{height:null,heightSource:'未提供高度，不以通道号代替'};
}
function unitInfo(h,element){const s=normalize(h),clean=s.replace(/\s/g,'');let sourceUnit=null,canonicalUnit=null,scale=1,offset=0;
 if(['wind_speed','u_component','v_component'].includes(element)){canonicalUnit='m/s';if(/km\/?h|kmh|千米/.test(clean)){sourceUnit='km/h';scale=1/3.6}else if(/mph/.test(s)){sourceUnit='mph';scale=.44704}else if(/knot|节/.test(s)){sourceUnit='knot';scale=.514444}else if(/m\/s|mps|米\/秒/.test(clean))sourceUnit='m/s';else canonicalUnit=null}
 if(element==='wind_direction'){canonicalUnit='deg';if(/rad|弧度/.test(s)){sourceUnit='rad';scale=180/Math.PI}else if(/deg|°|度/.test(s)&&!/°\s*c|degree\s*c/.test(s))sourceUnit='deg';else canonicalUnit=null}
 if(element==='temperature'){if(/°\s*c|degree\s*c|(?:^|[_\s])c(?:$|[_\s\]])/.test(s)){sourceUnit='°C';canonicalUnit='K';offset=273.15}else if(/(?:^|[\s\[(])k(?:$|[\s\])])|kelvin/.test(s)){sourceUnit='K';canonicalUnit='K'}}
 if(element==='pressure'){if(hit(s,'kpa')){sourceUnit='kPa';scale=1000}else if(hit(s,'hpa')||hit(s,'mb')){sourceUnit=hit(s,'mb')?'mb':'hPa';scale=100}else if(hit(s,'pa'))sourceUnit='Pa';if(sourceUnit)canonicalUnit='Pa'}
 if(element==='humidity'){if(s.includes('%')){sourceUnit='%';canonicalUnit='fraction';scale=.01}}
 if(element==='voltage'){if(/\bmv\b/.test(s)){sourceUnit='mV';scale=.001}else if(hit(s,'v')||hit(s,'volt'))sourceUnit='V';if(sourceUnit)canonicalUnit='V'}
 return {sourceUnit,canonicalUnit,scale,offset};
}
function sensor(header){const h=normalize(header);const m=h.match(/(?:channel|ch|sensor|通道|anemometer|anem)\s*[_#: -]?(\d+)\b/);return m?'sensor-'+m[1]:null}
function vectorElement(header){const h=normalize(header).replace(/\[[^\]]*\]|\([^)]*\)/g,'').trim();if(/^(u|eastward[ _-]?wind|u[ _-]?wind)(?:[ _-]?\d+(?:m)?)?$/i.test(h))return 'u_component';if(/^v[_-]?\d+(?:m)?$/i.test(h)||/^(northward[ _-]?wind|v[ _-]?wind)(?:[ _-]?\d+(?:m)?)?$/i.test(h))return 'v_component';return null}
function identifyOne(header,index=0,file='',override=null){const height=heightInfo(header,file),evidence={},rejections={};for(const rule of rules){evidence[rule.id]=matched(header,rule.keywords);rejections[rule.id]=matched(header,rule.exclude)}
 const vector=vectorElement(header),physical=rules.slice(0,6),valid=physical.filter(r=>evidence[r.id].length&&!rejections[r.id].length);let element='unknown',status='unrecognized',reason='',confidence='未识别';
 const explicitStats=['std','max','min'].filter(id=>evidence[id].length);let statistic=explicitStats.includes('std')?'std':explicitStats.length===1?explicitStats[0]:explicitStats.length>1?'ambiguous':matched(header,['gust','阵风']).length?'gust':'mean';
 const statisticSource=explicitStats.length||evidence.mean.length||statistic==='gust'?'显式统计量':'无统计量后缀，按均值候选';
 if(evidence.wind_speed.length&&rejections.wind_speed.length){element='wind_speed';status='excluded';confidence='已排除';reason='按风速排除词忽略：'+rejections.wind_speed.join('、')}
 else if(vector){element=vector;status='recognized';confidence='明确';reason='ERA5/矢量分量优先于短字母电压关键字'}
 else if(valid.length===1){element=valid[0].id;status='recognized';confidence='明确';reason='命中'+evidence[element].join('、');if(evidence[element].every(k=>['°','º','%','v','m/s','_C','℃','°C','□C','deg','Pa','mb'].some(x=>x.toLowerCase()===k.toLowerCase()))){confidence='待确认';reason+='；仅单位/短字母证据，需核对'} }
 else if(valid.length>1){status='ambiguous';confidence='待确认';reason='多个要素同时命中：'+valid.map(r=>r.label).join('、')}
 else {const blocked=physical.filter(r=>evidence[r.id].length&&rejections[r.id].length);if(blocked.length){element=blocked[0].id;status='excluded';confidence='已排除';reason='按排除词忽略：'+blocked.map(r=>rejections[r.id].join('、')).join('；')}else if(evidence.std.length){statistic='std';status='ambiguous';confidence='待确认';reason='识别到标准差，但不能仅凭SD/STD推断所属要素'}else if(evidence.max.length||evidence.min.length){status='ambiguous';confidence='待确认';reason='有统计量但所属参数未明确'}}
 // Explicit parameter words take priority over unit-only wind evidence (e.g. humidity % and wind speed units).
 if(valid.length>1&&status!=='excluded'){const strong=valid.filter(r=>evidence[r.id].some(k=>k.length>=3&&!['m/s','deg','hPa','kpa'].includes(k)));if(strong.length===1){element=strong[0].id;status='recognized';confidence='待确认';reason='优先采用明确要素词，其余单位证据保留核对'}}
 const exclusions=Object.entries(rejections).filter(([id,arr])=>arr.length&&(evidence[id]?.length||id===element)).map(([id,keywords])=>({element:id,keywords}));
 const result={index,header,element,statistic,statisticSource,...height,sensor:sensor(header),status,confidence,reason,evidence,exclusions,...unitInfo(header,element),manual:false};
 if(override){if(override.element){if(![...physical.map(r=>r.id),'u_component','v_component','unknown'].includes(override.element))throw Error('非法人工要素类型');result.element=override.element;Object.assign(result,unitInfo(header,result.element));result.status=result.element==='unknown'?'unrecognized':'recognized';result.confidence='人工确认';result.manual=true;result.reason='用户显式修正要素；原命中与排除记录保留'}if(override.statistic){if(!['mean','std','max','min','gust'].includes(override.statistic))throw Error('非法人工统计量');result.statistic=override.statistic;result.statisticSource='人工确认';result.manual=true}if(override.height!==undefined){const n=+override.height;if(!Number.isFinite(n)||n<=0||n>500)throw Error('人工高度应在0—500m范围内');result.height=n;result.heightSource='人工确认';result.manual=true}}
 if(result.statistic==='ambiguous'){result.status='ambiguous';result.confidence='待确认';result.reason+='；最大/最小等统计量冲突'}return result;
}
function identify(headers,file='',overrides={}){return headers.map((h,i)=>identifyOne(h,i,file,overrides[i]))}
function group(catalog){const groups=new Map();for(const c of catalog){const key=[c.element,c.height??'unknown',c.sensor??'unspecified'].join('|');if(!groups.has(key))groups.set(key,{element:c.element,height:c.height,sensor:c.sensor,columns:[]});groups.get(key).columns.push(c)}return [...groups.values()]}
function isAccepted(c){return c.status==='recognized'}
const api={version,rules,labels,normalize,hit,heightInfo,identifyOne,identify,group,isAccepted,unitInfo};root.ChannelLibrary=api;if(typeof module!=='undefined')module.exports=api;
})(typeof globalThis!=='undefined'?globalThis:this);
