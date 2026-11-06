'use strict';
const assert=require('node:assert/strict'),W=require('../gui/data-core.js');
(async()=>{
 const multi='设备说明\nDateTime,WS,WS,WD\n,80m,100m,80m\n,m/s,m/s,deg\n2024-01-01 00:00,6,7,270\n2024-01-01 01:00,7,8,280';
 const t=W.parseTable(multi);assert.equal(t.extraHeaderRows,2);assert.deepEqual(t.originalHeaders,['DateTime','WS','WS','WD']);assert.equal(t.rows.length,2);const d=await W.normalize(t,{file:'raw.csv'});assert.deepEqual(d.channels.map(c=>c.height),[80,100]);assert.equal(d.rows[0].values[1].v,7);
 for(const text of ['DateTime  WS80m  WD80m\n2024-01-01 00:00  6  270\n2024-01-01 01:00  7  280','DateTime WS80m WD80m\n2024-01-01 00:00 6 270\n2024-01-01 01:00 7 280']){const p=W.parseTable(text);assert.equal(p.delimiter,'whitespace');const x=await W.normalize(p,{file:'raw.csv'});assert.equal(x.rows.length,2);assert.equal(x.rows[0].values[0].v,6)}
 const duplicate='time,WS80m,WS80m\n2024-01-01 00:00,6,7\n2024-01-01 01:00,7,8';assert.throws(()=>W.parseTable(duplicate),/重复/);const kept=W.parseTable(duplicate,{headerRow:1,delimiter:',',allowDuplicateHeaders:true});assert.equal(kept.headers[2],'WS80m __COL3');assert.equal(kept.originalHeaders[2],'WS80m');
 const quoted=W.parseTable('time,WS80m,comment\n2024-01-01 00:00,6,"two\nlines"\n2024-01-01 01:00,7,"a,b"');assert.equal(quoted.rows.length,2);assert.equal(quoted.rows[0][2],'two\nlines');
 const selected=W.parseTable('note,note2\nmore,text\ntime;WS80m\n2024-01-01 00:00;6\n2024-01-01 01:00;7',{headerRow:3,delimiter:';'});assert.deepEqual(selected.headers,['time','WS80m']);assert.equal(selected.rows.length,2);
 console.log('PASS: multirow height/unit headers, raw-header provenance, wide/single-space TXT, duplicate recovery, quoted multiline records and manual header/separator.');
})().catch(e=>{console.error(e);process.exitCode=1});
