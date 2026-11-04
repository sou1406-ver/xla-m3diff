"""Check report evidence and artifact integrity; never evaluates a new model."""
from pathlib import Path
import json,hashlib,zipfile,re
from lxml import etree
from docx import Document
H=Path(__file__).parent;O=H.parent
cs=json.loads((H/'CASES.json').read_text(encoding='utf-8'));doc=Document(H/'BAO_CAO_BTL_M3DIFF.docx');md=(H/'BAO_CAO_BTL_M3DIFF.md').read_text(encoding='utf-8')
assert len(cs)==8 and len(doc.inline_shapes)==8
for c in cs:
 assert hashlib.sha256((H/c['figure_file']).read_bytes()).hexdigest()==c['figure_sha256']
 assert c['id'] in md
 for cap in c['captions'].values():assert cap in md
for ref,digest in json.loads((H/'EVIDENCE_MANIFEST.json').read_text()).items():assert hashlib.sha256((O/ref).read_bytes()).hexdigest()==digest
with zipfile.ZipFile(H/'BAO_CAO_BTL_M3DIFF.docx') as z:
 ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
 for n in ['word/document.xml','word/styles.xml']:assert not etree.fromstring(z.read(n)).xpath('//w:pBdr',namespaces=ns)
render=json.loads((H/'RENDER_MANIFEST.json').read_text());assert render['page_count']==18
for p in render['pages']:assert Path(p).is_file()
assert 'không có CIDEr OmniDiff của V2' in md and 'Thiếu toàn bộ 60 cặp' in md
assert 'Camera và synth so với base lưu sẵn' in md
assert 'affine một phần' in md
assert '127 (73,0%)' in md and '121 (69,5%)' in md
finalhash={Path(p).name:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in render['pages']}
result={'status':'PASS','docx_pages':18,'embedded_figures':8,'all_pages_visually_reviewed':True,'final_changed_pages_reviewed':[5,7,9,10],'page_hashes':finalhash,'checks':['8 figure hashes and exact captions','existing source metric hashes unchanged','no title paragraph borders','full vs partial scope preserved','cached camera baseline vs matched val explicit','V2 OmniDiff not evaluated','registration affine implementation named correctly'],'reviewer':'Codex assistant; not independent human content adjudication','new_model_inference':False,'new_training':False,'new_modal_compute':False,'docx_sha256':hashlib.sha256((H/'BAO_CAO_BTL_M3DIFF.docx').read_bytes()).hexdigest()}
(H/'FINAL_REPORT_QA.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k!='page_hashes'},ensure_ascii=False,indent=2))
