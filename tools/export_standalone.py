"""Produce an offline single-file GUI without a build dependency."""
from pathlib import Path
import re
root=Path(__file__).resolve().parents[1]
html=(root/'gui/index.html').read_text()
html=html.replace('<link rel="stylesheet" href="style.css">','<style>'+(root/'gui/style.css').read_text()+'</style>')
js=(root/'gui/app.js').read_text()
# Offline output needs no network call; preserve a visible build version.
js=re.sub(r'// Read the deployed version[\s\S]*?\.catch\(\(\)=>\{\}\);',"document.querySelector('.appfooter').firstChild.textContent='风序 WIND RESOURCE · 0.1.0-prototype · 离线版 ';",js)
html=html.replace('<script src="app.js"></script>','<script>'+js.replace('</script','<\\/script')+'</script>')
out=root/'dist/风序-GUI.html';out.parent.mkdir(exist_ok=True);out.write_text(html)
print(out)
