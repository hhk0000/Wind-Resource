/* Real time-series input and window calculations. No synthetic data or UI dependencies. */
(function(root){
'use strict';
const C=root.ChannelLibrary||(typeof require==='function'?require('./channel-library.js'):null);
if(!C)throw Error('通道关键字库未加载');
const num=x=>{const s=String(x??'').trim();return s===''?NaN:Number(s)};
function dateParts(ms,offset=8){const d=new Date(ms+offset*3600000);return [d.getUTCFullYear(),d.getUTCMonth()+1,d.getUTCDate(),d.getUTCHours(),d.getUTCMinutes(),d.getUTCSeconds()]}
function makeDate(y,m,d,h=0,min=0,sec=0,offset=8){if(m<1||m>12||d<1||h<0||h>23||min<0||min>59||sec<0||sec>59)return NaN;const t=Date.UTC(y,m-1,d,h,min,sec);const q=new Date(t);return q.getUTCFullYear()===y&&q.getUTCMonth()===m-1&&q.getUTCDate()===d?t-offset*3600000:NaN}
function parseDate(value,{offset=8,excel=false,format='ymd'}={}){let s=String(value??'').trim();if(!s)return NaN;if(excel&&/^\d{4,5}(\.\d+)?$/.test(s)){const n=+s;if(n>=60&&n<100000)return Math.round((n-25569)*86400000)-offset*3600000}
 if(/^\d{10}$/.test(s))return +s*1000;if(/^\d{13}$/.test(s))return +s;
 s=s.replace(/[年月]/g,'-').replace('日','').replace(/\//g,'-');let tz=offset;const z=s.match(/(Z|[+-]\d{2}:?\d{2})$/i);if(z&&/[T ]\d{2}:\d{2}/.test(s)){if(z[0].toUpperCase()==='Z')tz=0;else{const v=z[0].replace(':',''),hh=+v.slice(1,3),mm=+v.slice(3,5);if(hh>14||mm>59||(hh===14&&mm))return NaN;tz=(hh+mm/60)*(v[0]==='-'?-1:1)}s=s.slice(0,-z[0].length)}
 let p=s.match(/^(\d{4})-(\d{1,2})-(\d{1,2})(?:[T ](\d{1,2}):(\d{2})(?::(\d{2})(?:\.(\d{1,3}))?)?)?$/);
 if(p)return makeDate(+p[1],+p[2],+p[3],+(p[4]||0),+(p[5]||0),+(p[6]||0),tz)+Number((p[7]||'').padEnd(3,'0'));
 if(format!=='ymd'){p=s.match(/^(\d{1,2})-(\d{1,2})-(\d{4})(?:[T ](\d{1,2}):(\d{2})(?::(\d{2}))?)?$/);if(p)return makeDate(+p[3],format==='dmy'?+p[2]:+p[1],format==='dmy'?+p[1]:+p[2],+(p[4]||0),+(p[5]||0),+(p[6]||0),tz)}
 return NaN;
}
function shiftYear(ms,delta,offset=8){const p=dateParts(ms,offset),y=p[0]+delta,days=new Date(Date.UTC(y,p[1],0)).getUTCDate();return makeDate(y,p[1],Math.min(p[2],days),p[3],p[4],p[5],offset)+new Date(ms).getUTCMilliseconds()}
function fmt(ms,offset=8){const p=dateParts(ms,offset);return `${p[0]}-${String(p[1]).padStart(2,'0')}-${String(p[2]).padStart(2,'0')} ${p.slice(3).map(x=>String(x).padStart(2,'0')).join(':')}`}
function stageFromName(name){if(/meso|era5|merra|中尺度|再分析/i.test(name))return 'mesoscale';if(/final|hub|轮毂|最终|订正|外推/i.test(name))return 'final';if(/qc|clean|质控|标记|删除/i.test(name))return 'qc';if(/raw|origin|原始/i.test(name))return 'raw';return ''}
function heightOf(s){return C.heightInfo(s).height}
function detect(headers,file='',overrides={}){
 const catalog=C.identify(headers,file,overrides),accepted=catalog.filter(C.isAccepted);
 let ti=-1,date=-1,clock=-1,flag=-1;
 headers.forEach((h,i)=>{if(/^(time|timestamp|datetime|date.?time|时间戳|时间|日期时间)$/i.test(h)||/date.*time|^valid[_ ]time$|^timestamp[_ (]|^time(?:[ _(]|$)/i.test(h))ti=i;else if(/^(date|日期)$/i.test(h))date=i;else if(/^(hour|clock|时刻|时分秒)$/i.test(h))clock=i;if(/^(qc|flag|qc.flag|quality.flag|质量标记|删除标记)$/i.test(h))flag=i});
 if(date>=0&&ti>=0&&/^(time|时间)$/i.test(headers[ti])){clock=ti;ti=date}else if(ti<0&&date>=0)ti=date;
 const dirs=accepted.filter(c=>c.element==='wind_direction'&&c.statistic==='mean');
 const means=accepted.filter(c=>c.element==='wind_speed'&&c.statistic==='mean');
 const channels=means.map(c=>({key:'c'+c.index,name:c.header,speed:c.index,height:c.height,sensor:c.sensor,scale:c.scale,unit:'m/s',sourceUnit:c.sourceUnit||'待确认（界面默认m/s）',recognition:c}));
 const warnings=[];
 for(const u of accepted.filter(c=>c.element==='u_component'&&c.statistic==='mean')){
  const vs=accepted.filter(c=>c.element==='v_component'&&c.statistic==='mean'&&c.height===u.height);
  if(vs.length===1){const v=vs[0];channels.push({key:'uv'+u.index,name:`U/V合成 ${u.height??'未识别'}m`,u:u.index,v:v.index,height:u.height,scale:u.scale,vScale:v.scale,unit:'m/s',sourceUnit:u.sourceUnit||'待确认（默认m/s）',recognition:u})}else warnings.push(u.header+'的V分量缺失或不唯一');
 }
 for(const c of channels){
  const same=dirs.filter(d=>d.height===c.height);let dir=same.length===1?same[0]:same.find(d=>d.sensor&&d.sensor===c.sensor);
  if(!dir&&!same.length&&dirs.length===1)dir=dirs[0];
  if(dir){c.direction=dir.index;c.dirScale=dir.scale;c.directionHeight=dir.height}else if(same.length>1)warnings.push(c.name+'匹配到多个风向通道，请人工指定');
  for(const [stat,field]of [['std','stddevColumn'],['max','maximumColumn'],['min','minimumColumn']]){
   let matches=accepted.filter(d=>d.element==='wind_speed'&&d.statistic===stat&&d.height===c.height);
   if(c.sensor){const own=matches.filter(d=>d.sensor===c.sensor);if(own.length)matches=own}
   if(matches.length===1){c[field]=matches[0].index;c[field.replace('Column','Scale')]=matches[0].canonicalUnit?matches[0].scale:c.scale;}else if(matches.length>1)warnings.push(c.name+'的'+C.labels[stat]+'通道不唯一，未自动绑定');
  }
 }
 const parameterChannels=accepted.filter(c=>['wind_power_density','temperature','pressure','humidity','voltage'].includes(c.element)).map(c=>({...c}));
 return {time:ti,clock,flag,channels,catalog,parameterChannels,warnings,dictionaryVersion:C.version};
}
function splitCSV(input,delimiter){let rows=[],row=[],cell='',quote=false;
 for(let i=0;i<input.length;i++){const c=input[i];if(c==='"'){if(quote&&input[i+1]==='"'){cell+='"';i++}else quote=!quote}else if(c===delimiter&&!quote){row.push(cell);cell=''}else if((c==='\n'||c==='\r')&&!quote){if(c==='\r'&&input[i+1]==='\n')i++;row.push(cell);if(row.some(v=>v.trim()))rows.push(row);row=[];cell=''}else cell+=c}
 if(quote)throw Error('文件存在未闭合的引号。');row.push(cell);if(row.some(v=>v.trim()))rows.push(row);return rows;
}
function whitespaceParts(line){const wide=line.trim().split(/\t+| {2,}/);return wide.length>1?wide:line.trim().split(/\s+/)}
function metadataCell(value){const x=String(value).trim();return !x||/^(?:\d{1,3}(?:[.,]\d+)?\s*(?:m|米)|m\/?s|km\/?h|deg|degree|°|º|°c|℃|hpa|kpa|pa|%|rh|v|mv|w\/m[²2]|avg|average|mean|sd|std|stddev|stdev|min|max|minimum|maximum|height|heights|units?|高度|单位|均值|平均值|最大值|最小值|标准差)$/i.test(x)}
function parseTable(text,options={}){text=text.replace(/^\uFEFF/,'');const lines=text.split(/\r?\n/);const delimiters=options.delimiter&&options.delimiter!=='auto'?[options.delimiter==='tab'?'\t':options.delimiter]:['\t',',',';','whitespace'];let best=-1,score=-1,delimiter=',';
 const start=options.headerRow?options.headerRow-1:0,stop=options.headerRow?start+1:Math.min(lines.length,200);if(start<0||start>=lines.length)throw Error('所选表头行超出文件范围。');
 for(let i=start;i<stop;i++){const line=lines[i];for(const sep of delimiters){let hs;try{hs=sep==='whitespace'?whitespaceParts(line):splitCSV(line,sep)[0]||[]}catch{continue}if(hs.length<2)continue;const d=detect(hs);const n=(d.time>=0?10:0)+(d.channels.length?10:0)+Math.min(hs.length,10)+(sep==='whitespace'?-.1:0);if(n>score){best=i;score=n;delimiter=sep}}}
 if(best<0)throw Error('无法识别表头或分隔符，请打开解析设置，指定表头行及分隔符。');
 let rows=delimiter==='whitespace'?lines.slice(best).filter(l=>l.trim()).map(whitespaceParts):splitCSV(lines.slice(best).join('\n'),delimiter);
 if(rows.length<2)throw Error('文件需要表头和数据行。');if(rows.length>1000001)throw Error('单文件最多100万行。');
 const originalHeaders=rows.shift().map(x=>String(x).trim()),headerParts=[originalHeaders];let headers=[...originalHeaders];
 // Only merge conservative, wholly metadata-only rows, never numeric observations.
 for(let i=0;i<3&&rows.length;i++){const next=rows[0];if(next.length!==headers.length||!next.every(metadataCell)||!next.some(x=>String(x).trim()))break;headerParts.push(rows.shift().map(x=>String(x).trim()))}
 headers=headers.map((h,i)=>[h,...headerParts.slice(1).map(r=>r[i])].filter(Boolean).join(' ').trim());
 if(options.allowDuplicateHeaders){const used=new Set();headers=headers.map((h,i)=>{let name=h||'未命名列'+(i+1);if(used.has(name))name+=' __COL'+(i+1);used.add(name);return name})}
 if(new Set(headers).size!==headers.length||headers.some(h=>!h))throw Error('合并高度/单位行后表头仍为空或重复，请打开解析设置勾选保留重名列，再人工映射。');
 if(delimiter==='whitespace'){const m=detect(headers);rows=rows.map(r=>{if(r.length===headers.length+1&&m.time===0&&m.clock<0&&/^\d{4}[-/]\d{1,2}[-/]\d{1,2}$/.test(r[0])&&/^\d{1,2}:\d{2}/.test(r[1]))return [r[0]+' '+r[1],...r.slice(2)];return r})}
 return {headers,originalHeaders,headerParts,rows,preambleLines:best,extraHeaderRows:headerParts.length-1,delimiter};
}
async function normalize(table,{file,stage='',offset=8,inputOffset=offset,format='ymd',defaultHeight=null,validFlags=['0','valid','good'],mapping=null,excel=false}={}){const map=mapping||detect(table.headers,file);if(map.time<0)throw Error('时间列未识别，请手动指定。');if(!map.channels.length)throw Error('风速通道未识别，请手动映射风速列。');if(map.channels.some(c=>c.unit==='unsupported'))throw Error('风速单位未支持，请先转换为m/s。');const parameterChannels=map.parameterChannels||[];const channels=map.channels.map(c=>({...c,height:c.height??(defaultHeight!==null&&defaultHeight!==''?Number(defaultHeight):null)}));let badTime=0,malformed=0,duplicates=0;const seen=new Set(),rows=[],grids=new Set();
 const lat=table.headers.findIndex(h=>/^(lat|latitude|纬度)$/i.test(h)),lon=table.headers.findIndex(h=>/^(lon|longitude|经度)$/i.test(h));
 for(let i=0;i<table.rows.length;i++){const row=table.rows[i];if(row.length!==table.headers.length){malformed++;continue}if(lat>=0&&lon>=0)grids.add(row[lat]+','+row[lon]);const timeValue=excel&&map.clock>=0&&Number.isFinite(num(row[map.time]))&&Number.isFinite(num(row[map.clock]))?num(row[map.time])+num(row[map.clock]):String(row[map.time])+(map.clock>=0?' '+row[map.clock]:'');const ts=parseDate(timeValue,{offset:inputOffset,format,excel});if(!Number.isFinite(ts)){badTime++;continue}if(seen.has(ts)){duplicates++;continue}seen.add(ts);const flag=map.flag<0||validFlags.includes(String(row[map.flag]).trim().toLowerCase());const values=channels.map(c=>{let speed=c.u!==undefined?Math.hypot(num(row[c.u])*(c.scale||1),num(row[c.v])*(c.vScale??c.scale??1)):num(row[c.speed])*c.scale;let dir=c.u!==undefined?(Math.atan2(-num(row[c.u]),-num(row[c.v]))*180/Math.PI+360)%360:c.direction!==undefined?num(row[c.direction])*(c.dirScale||1):NaN;if(!Number.isFinite(dir)||dir<0||dir>360)dir=null;if(!flag||!Number.isFinite(speed)||speed<0)speed=null;const value={v:speed,dir:dir===360?0:dir};for(const [column,key]of [['stddevColumn','stddev'],['maximumColumn','maximum'],['minimumColumn','minimum']])if(c[column]!==undefined){const n=num(row[c[column]]);value[key]=flag&&Number.isFinite(n)&&n>=0?n*(c[column.replace('Column','Scale')]??c.scale):null}return value});const record={ts,values};if(parameterChannels.length)record.parameters=parameterChannels.map(c=>{const n=num(row[c.index]);return flag&&Number.isFinite(n)&&!(c.statistic==='std'&&n<0)?n*c.scale+(c.statistic==='std'?0:c.offset):null});rows.push(record);if(i&&i%25000===0)await new Promise(r=>setTimeout(r,0))}
 if(grids.size>1)throw Error('检测到多个经纬度格点，请先选择单个中尺度格点导出，不能混合为同一序列。');if(!rows.length)throw Error('没有有效时间戳，请检查日期格式和时区。');rows.sort((a,b)=>a.ts-b.ts);const counts=new Map();for(let i=1;i<rows.length;i++){const d=rows[i].ts-rows[i-1].ts;if(d>0&&d<=86400000)counts.set(d,(counts.get(d)||0)+1)}const step=[...counts].sort((a,b)=>b[1]-a[1]||a[0]-b[0])[0]?.[0];if(!step)throw Error('无法可靠推断采样步长；至少需要两个相邻记录。');const start=rows[0].ts,end=rows.at(-1).ts+step,expected=Math.round((end-start)/step),offgrid=rows.filter(r=>(r.ts-start)%step!==0).length;
 if(offgrid)throw Error(`发现${offgrid}条不在推断时间网格上的记录，请先统一采样间隔。`);
 return {file,stage:stage||stageFromName(file),offset,channels,rows,step,start,end,expected,diagnostics:{badTime,malformed,duplicates,missing:Math.max(0,expected-rows.length),invalid:channels.map((_,j)=>rows.filter(r=>r.values[j].v===null).length)},mapping:map,catalog:map.catalog||[],parameterChannels,dictionaryVersion:map.dictionaryVersion||null};
}
function representativeYear(final){if(!final)throw Error('尚未导入最终轮毂高度数据，无法确定测风年锚点。');const target=shiftYear(final.start,1,final.offset);if(final.end!==target)throw Error(`最终数据需恰好覆盖一个日历年：[${fmt(final.start,final.offset)}, ${fmt(target,final.offset)})；当前结束为${fmt(final.end,final.offset)}。`);return {start:final.start,end:target,offset:final.offset,expected:final.expected,missing:final.diagnostics.missing,invalid:final.diagnostics.invalid}}
function channelIndex(ds,key){if(key==='auto'||key===undefined)return 0;const idx=ds.channels.findIndex(c=>String(c.height)===String(key));return idx}
function aggregate(ds,{start=ds.start,end=ds.end,channel=0,period='year',anchor=null}={}){if(channel<0)return [];const bins=new Map(),edges=anchor;for(const row of ds.rows){if(row.ts<start||row.ts>=end)continue;const v=row.values[channel];if(!v)continue;let k;if(edges){let lo=0,hi=edges.length-1;while(lo<hi){const m=Math.floor((lo+hi+1)/2);if(edges[m]<=row.ts)lo=m;else hi=m-1}k=lo;if(k>=edges.length-1)continue}else if(period==='day')k=Math.floor((row.ts+ds.offset*3600000)/86400000)*86400000-ds.offset*3600000;else if(period==='hour')k=Math.floor(row.ts/3600000)*3600000;else k=dateParts(row.ts,ds.offset)[0];if(!bins.has(k))bins.set(k,{key:k,sum:0,n:0,observed:0,rose:Array(16).fill(0),dirCount:0});const b=bins.get(k);b.observed++;if(v.v!==null){b.sum+=v.v;b.n++;if(v.dir!==null&&v.v>.5){b.rose[Math.floor((v.dir+11.25)%360/22.5)]++;b.dirCount++}}}return [...bins.values()].sort((a,b)=>a.key-b.key).map(b=>({...b,mean:b.n?b.sum/b.n:null}))}
function windowStats(meso,final,n,channel=0){const year=representativeYear(final),start=shiftYear(year.end,-n,year.offset),end=year.end,edges=Array.from({length:n+1},(_,i)=>shiftYear(end,-n+i,year.offset));if(!meso)return {n,start,end,status:'missing',annual:[],message:'尚未导入中尺度文件'};if(channel<0)return {n,start,end,status:'missing_channel',annual:[],message:'中尺度无所选高度通道'};const annual=aggregate(meso,{start,end,channel,anchor:edges}),by=new Map(annual.map(b=>[b.key,b]));const expected=(end-start)/meso.step,observed=annual.reduce((s,b)=>s+b.observed,0),valid=annual.reduce((s,b)=>s+b.n,0),coverage=expected?valid/expected:0,full=meso.start<=start&&meso.end>=end&&observed===expected&&valid===expected;return {n,start,end,status:full?'complete':'partial',coverage,observed,valid,expected,mean:valid?annual.reduce((s,b)=>s+b.sum,0)/valid:null,annual:edges.slice(0,-1).map((s,i)=>({start:s,end:edges[i+1],...(by.get(i)||{n:0,mean:null,rose:Array(16).fill(0),dirCount:0})})),message:full?'窗口完整覆盖':'资料不足或含无效/缺测记录，不能标为完整长期序列'}}
const api={num,parseDate,shiftYear,fmt,stageFromName,heightOf,detect,parseTable,normalize,representativeYear,channelIndex,aggregate,windowStats};root.WindData=api;if(typeof module!=='undefined')module.exports=api;
})(typeof globalThis!=='undefined'?globalThis:this);
