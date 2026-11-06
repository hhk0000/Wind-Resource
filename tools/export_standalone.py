"""Produce an offline single-file GUI without a build dependency."""
from pathlib import Path
import re,json
root=Path(__file__).resolve().parents[1]
html=(root/'gui/index.html').read_text()
html=html.replace('<link rel="stylesheet" href="style.css">','<style>'+(root/'gui/style.css').read_text()+'</style>')
js=(root/'gui/app.js').read_text()+'\n'+(root/'gui/viz-v03.js').read_text()+'\n'+(root/'gui/workspace-v04.js').read_text()+'\n'+(root/'gui/channel-library.js').read_text()+'\n'+(root/'gui/data-core.js').read_text()+'\n'+(root/'gui/xlsx-input.js').read_text()+'\n'+(root/'gui/data-import-v05.js').read_text()+'\n'+(root/'gui/channel-recognition-ui.js').read_text()+'\n'+(root/'gui/standard-channels.js').read_text()+'\n'+(root/'gui/upload-flow-v07.js').read_text()
# Offline output needs no network call; preserve the current build version.
version=json.loads((root/'gui/version.json').read_text())['version']
js=re.sub(r'// Read the deployed version[\s\S]*?\.catch\(\(\)=>\{\}\);',"document.querySelector('.appfooter').firstChild.textContent='风序 WIND RESOURCE · "+version+" · 离线版 ';",js)
html=html.replace('<script src="viz-v03.js"></script>','').replace('<script src="workspace-v04.js"></script>','')
for name in ['channel-library.js','data-core.js','xlsx-input.js','data-import-v05.js','channel-recognition-ui.js','standard-channels.js','upload-flow-v07.js']:
 html=html.replace('<script src="'+name+'"></script>','')
html=html.replace('<script src="app.js"></script>','<script>'+js.replace('</script','<\\/script')+'</script>')
out=root/'dist/风序-GUI.html';out.parent.mkdir(exist_ok=True);out.write_text(html)
print(out)
