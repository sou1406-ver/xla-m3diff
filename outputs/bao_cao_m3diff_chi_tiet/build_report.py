from pathlib import Path
import json,csv,re,hashlib,zipfile
from docx import Document
from docx.shared import Pt,Mm,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT,WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT

HERE=Path(__file__).parent;OUT=HERE.parent;WORK=OUT.parent
def read(path):return (OUT/path).read_text(encoding='utf-8-sig')
def load(path):return json.loads(read(path))
def mdtable(headers,rows):
 clean=lambda x:str(x).replace('|','/').replace('\n',' ')
 return '\n'.join(['| '+' | '.join(map(clean,headers))+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(map(clean,row))+' |' for row in rows])
def tablefrom(path,index=0):
 tables=re.findall(r'(?m)(?:^\|[^\n]*\|[ \t]*\n)+',read(path)+'\n')
 return tables[index].strip()
config=load('baseline_results/run_config.json')
versions=mdtable(['Thành phần','Phiên bản hoặc định danh'],[
 ['Repository','Yuan-Liu-01/M3Diff'],['Commit',config['repo_commit']],
 ['Checkpoint','IVC-liuyuan/M3Diff'],['Revision weights',config['hf_revisions']['model']],
 ['Revision dataset',config['hf_revisions']['dataset']],['Seed',42],
 ['Giải mã','BF16 / greedy / beam 1 / 1024 token / không FlashAttention']])
baseline=list(csv.DictReader(read('baseline_results/summary_x100.csv').splitlines()))
base_table=mdtable(['Miền','Số cặp','BLEU 4','METEOR','ROUGE L','CIDEr'],[[r['split'],r['n_pairs'],*[f'{float(r[k]):.3f}' for k in ['Bleu_4','METEOR','ROUGE_L','CIDEr']]] for r in baseline])
coco=load('locateanything_coco/summary.json')
cocot=mdtable(['Prompt','Hit ảnh dương IoU 0,5','Box sai trên ảnh âm','Từ chối đúng ảnh âm'],[[key,f"{coco[key]['positive_hits_iou50']}/12",f"{coco[key]['negative_false_positives']}/12",f"{coco[key]['negative_correct_rejections']}/12"] for key in ['single','all']])
scores=load('mixed_full_benchmark/results/summary_x100.json')
rawclean=[r for r in scores if r['processing'] in ['raw','dedup']]
primary=mdtable(['Miền','Model và xử lý','BLEU 4','METEOR','ROUGE L','CIDEr'],[[r['split'],('Gốc' if r['arm']=='baseline' else 'Mixed')+' '+r['processing'],*[f'{r[k]:.3f}' for k in ['Bleu_4','METEOR','ROUGE_L','CIDEr']]] for r in rawclean])
bleu=mdtable(['Miền','Model','Xử lý','BLEU 1','BLEU 2','BLEU 3','BLEU 4'],[[r['split'],'Gốc' if r['arm']=='baseline' else 'Mixed',r['processing'].replace('dedup_joined_v2','dedup v2'),*[f'{r[k]:.3f}' for k in ['Bleu_1','Bleu_2','Bleu_3','Bleu_4']]] for r in scores])
other=mdtable(['Miền','Model','Xử lý','METEOR','ROUGE L','CIDEr'],[[r['split'],'Gốc' if r['arm']=='baseline' else 'Mixed',r['processing'].replace('dedup_joined_v2','dedup v2'),*[f'{r[k]:.3f}' for k in ['METEOR','ROUGE_L','CIDEr']]] for r in scores])
validated=load('mixed_full_benchmark/results/FULL_RUN_VALIDATED.json')
batches=mdtable(['Chunk','Số cặp','GPU thực tế','Thời gian giây','Hoàn tất'],[[r['batch'],r['n_completed'],r['actual_gpu'].split(',')[0],f"{r['elapsed_seconds']:.1f}",'Có'] for r in validated['batches']])
behavior=load('mixed_full_benchmark/results/caption_behavior_audit.json')['by_split_arm']
behave=mdtable(['Miền','Model','Từ trung bình','Trung vị từ','P95 từ','Caption từ 500 từ'],[[r['split'],'Gốc' if r['arm']=='baseline' else 'Mixed',f"{r['mean_whitespace_words']:.2f}",r['median_whitespace_words'],r['p95_whitespace_words'],r['captions_at_least_500_whitespace_words']] for r in behavior])
caps=load('caption_cap_probe/CAP_AUDIT.json')
capst=mdtable(['Nhánh','Số ca','Natural chạm cap','Ca dài chạm cap','Đối chứng cùng GPU'],[[r['probe'],r['status']['n_completed'],len(r['natural_cap_hit_ids']),f"{sum(x['cap_hit'] for x in r['long_cases'])}/4",'18/19 natural khớp 1024' if r['probe']=='base128' else 'Không có trong lượt này'] for r in caps['probes']])
manifest=load('m3diff_portable/EXPORT_MANIFEST.json')
integrity='\n\n'.join([f"**{name}**\n\n`{value}`" for name,value in [('Commit repository',config['repo_commit']),('Revision checkpoint',config['hf_revisions']['model']),('Revision dataset',config['hf_revisions']['dataset']),('SHA256 runner baseline',config['runner_sha256']),('SHA256 adapter đã chọn',manifest['adapter_files_sha256']['adapter_model.bin']),('SHA256 môi trường 5 chunk',validated['environment_freeze_sha256'])]])
integrity+='\n\n'+mdtable(['Kiểm tra','Kết quả'],[['ID full test','1570 duy nhất và đủ hai miền'],['Nạp LoRA','392 tensor / giá trị FP32 khớp'],['Khởi tạo và thứ tự ablation','Khớp ở cả hai epoch'],['Kiểm tra duplicate train và eval','Không có hash RGB trùng trong phạm vi đã kiểm tra'],['Portable smoke','2 trên 2 caption khớp runner tham chiếu cùng GPU'],['CRC gói xuất','Tất cả thành viên đạt trong lần đóng gói đã lưu'],['GPU sau công việc','Các app gần đây của công việc stopped và 0 task']])
artifacts=mdtable(['Sản phẩm','Vị trí trong workspace','Vai trò'],[
 ['Notebook baseline','m3diff-baseline-full.ipynb','Quy trình tái lập đầy đủ'],
 ['Kết quả baseline','outputs/baseline_results/','Điểm và cấu hình gốc'],
 ['Gói chạy độc lập','outputs/m3diff_portable.zip','Adapter và notebook inference'],
 ['Gói kết quả full','outputs/m3diff_full_benchmark_results.zip','Caption và các phép đo đầy đủ'],
 ['Manifest','outputs/m3diff_portable/EXPORT_MANIFEST.json','Hash và kiểm tra nạp'],
 ['Notebook portable','outputs/m3diff_portable/m3diff-inference-portable.ipynb','Mặc định base, có lựa chọn LoRA'],
 ['Hồ sơ annotation','Các thư mục invariance và prompt','Rubric, masked, decoded, decision'],
 ['Trạng thái GPU cuối','outputs/modal_budget/FINAL_GPU_CHECK.json','Xác nhận không còn app công việc hoạt động']])
source_groups=[
 ('H01','Tái lập baseline',['baseline_results/REPORT.md','baseline_results/run_config.json','baseline_results/SUCCESS.json']),
 ('H02','LocateAnything định tính',['locateanything_demo/REPORT.md','locateanything_robustness/REPORT.md','locateanything_demo/run_config.json']),
 ('H03','LocateAnything với mẫu COCO',['locateanything_coco/summary.json','locateanything_coco/run_config.json','locateanything_coco/per_query.csv']),
 ('H04','Grounded caption pilot',['grounded_caption_pilot/REPORT.md','grounded_caption_pilot/run_config.json','grounded_caption_pilot/metrics.json']),
 ('H05','Verifier phát triển',['caption_verifier_color_v4/REPORT.md','caption_verifier_color_v4/run_config.json','m3diff_caption_verifier/caption_verifier.py']),
 ('H06','Verifier validation mới',['m3diff_caption_verifier/KET_QUA.md','m3diff_caption_verifier/validation/REPORT.md','m3diff_caption_verifier/validation/run_config.json']),
 ('H07','Continued SFT random và hard',['real_sft_results/REPORT.md','real_sft_results/metrics.json']),
 ('H08','SFT nhãn sửa và đối chứng',['curated_sft/KET_QUA.md','curated_sft/README.md','curated_sft/decision.json']),
 ('H09','Lọc lặp full baseline',['curated_sft/dedup_full_results/REPORT.md','curated_sft/dedup_full_results/audit.json']),
 ('H10','Diagnostic và prompt camera',['viewpoint_diagnostic/KET_QUA.md','viewpoint_diagnostic/PROMPT_KET_QUA.md','viewpoint_diagnostic/protocol_locked.json']),
 ('H11','Stress căn chỉnh mở rộng',['viewpoint_extension/KET_QUA.md','viewpoint_extension/decision.json','viewpoint_extension/safe_check/SUCCESS.json']),
 ('H12','Invariance SFT đầu tiên',['invariance_sft/KET_QUA.md','invariance_sft/protocol.json','invariance_sft/data_audit.json']),
 ('H13','Kiểm tra precision',['precision_audit/KET_QUA.md','precision_audit/comparison_protocol.json','precision_audit/decision.json']),
 ('H14','Ablation loss không đổi',['invariance_ablation/KET_QUA.md','invariance_ablation/results/protocol.json','invariance_ablation/results/matched_training_audit.json']),
 ('H15','Confirmation 80 cặp',['invariance_confirmation/KET_QUA.md','invariance_confirmation/decision.json','invariance_confirmation/metrics.json']),
 ('H16','Full benchmark candidate',['mixed_full_benchmark/results/summary_x100.json','mixed_full_benchmark/results/FULL_RUN_VALIDATED.json','mixed_full_benchmark/selection_locked.json','mixed_full_benchmark/protocol.json']),
 ('H17','Template distribution và balanced',['invariance_ablation/prompt_distribution_audit.json','prompt_balanced_sft/KET_QUA.md','prompt_balanced_sft/decision.json']),
 ('H18','Probe template',['prompt_probe/KET_QUA.md','prompt_probe/decision.json','prompt_probe/metrics.json']),
 ('H19','Kiểm tra cleanup v2',['caption_cleanup_v2/corpus_audit_with_full.json','caption_cleanup_v2/protocol.json']),
 ('H20','Caption cap và đối chứng cùng GPU',['caption_cap_probe/KET_QUA.md','caption_cap_probe/CAP_AUDIT.json','caption_cap_probe/base_protocol.json','caption_cap_probe/base128_results/same_GPU_control_extension.json']),
 ('H21','Chuyển máy và nạp adapter',['m3diff_portable/README.md','m3diff_portable/EXPORT_MANIFEST.json','m3diff_portable/INPUT_CHECKS.json','FINAL_ARTIFACTS.json'])]
sources=[];evidence=[]
for key,label,paths in source_groups:
 sources.append(f'### {key} {label}')
 for path in paths:
  p=OUT/path;assert p.is_file(),p
  sources.append(f'- [{path}]({p.as_posix()})')
  evidence.append({'evidence_id':key,'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
external=[('T01','Repository chính thức M3Diff','https://github.com/Yuan-Liu-01/M3Diff'),('T02','OmniDiff A Comprehensive Benchmark for Fine grained Image Difference Captioning','https://arxiv.org/abs/2503.11093'),('T03','Model card NVIDIA LocateAnything 3B','https://huggingface.co/nvidia/LocateAnything-3B'),('T04','Robust Change Captioning ICCV 2019','https://openaccess.thecvf.com/content_ICCV_2019/html/Park_Robust_Change_Captioning_ICCV_2019_paper.html'),('T05','Distractors Immune Representation Learning ECCV 2024','https://www.ecva.net/papers/eccv_2024/papers_ECCV/html/5989_ECCV_2024_paper.php')]
for key,label,url in external:sources.append(f'### {key} {label}\n\n[{label}]({url})')
sources.append('Các tài liệu ngoài giải thích kiến trúc và cơ sở nghiên cứu; không được dùng thay số đo thực nghiệm trong workspace. Tên model trong tài liệu mới có thể khác cách viết của snapshot cũ; định danh commit và revision trong cấu hình thực nghiệm là căn cứ tái lập.')
replacements={'VERSIONS':versions,'BASELINE':base_table,'COCO':cocot,'GROUNDED':tablefrom('grounded_caption_pilot/REPORT.md'),'VERIFIER_DEV':tablefrom('caption_verifier_color_v4/REPORT.md'),'VERIFIER_VALIDATION':tablefrom('m3diff_caption_verifier/validation/REPORT.md'),'REAL_SFT':tablefrom('real_sft_results/REPORT.md'),'CURATED':tablefrom('curated_sft/KET_QUA.md'),'DEDUP':tablefrom('curated_sft/KET_QUA.md',1),'PROMPT_GEOMETRY':tablefrom('viewpoint_diagnostic/PROMPT_KET_QUA.md'),'REGISTRATION_STRESS':tablefrom('viewpoint_extension/KET_QUA.md',1),'INVARIANCE_FIRST':tablefrom('invariance_sft/KET_QUA.md'),'PRECISION':tablefrom('precision_audit/KET_QUA.md'),'ABLATION':tablefrom('invariance_ablation/KET_QUA.md'),'CONFIRMATION':tablefrom('invariance_confirmation/KET_QUA.md'),'BALANCED':tablefrom('prompt_balanced_sft/KET_QUA.md'),'TEMPLATE_PROBE':tablefrom('prompt_probe/KET_QUA.md'),'BATCHES':batches,'FULL_PRIMARY':primary,'BEHAVIOR':behave,'CAPS':capst,'ARTIFACTS':artifacts,'FULL_BLEU':bleu,'FULL_OTHER':other,'INTEGRITY':integrity,'SOURCES':'\n\n'.join(sources)}
replacements.update({'PROMPT_GEOMETRY_ERRORS':tablefrom('viewpoint_diagnostic/PROMPT_KET_QUA.md',1),'PROMPT_FACTS':tablefrom('viewpoint_diagnostic/PROMPT_KET_QUA.md',2),'REGISTRATION_COVERAGE':tablefrom('viewpoint_extension/KET_QUA.md',0),'REGISTRATION_COMPOSED':tablefrom('viewpoint_extension/KET_QUA.md',2),'INVARIANCE_FACTS':tablefrom('invariance_sft/KET_QUA.md',1),'PRECISION_FACTS':tablefrom('precision_audit/KET_QUA.md',1)})
text=(HERE/'noi_dung.md').read_text(encoding='utf8')
for key,value in replacements.items():
 assert '{{'+key+'}}' in text,key
 text=text.replace('{{'+key+'}}',value)
assert not re.search(r'\{\{.*?\}\}',text)
output=HERE/'BAO_CAO_M3DIFF_CHI_TIET.md';output.write_text(text,encoding='utf8')
(HERE/'EVIDENCE_MANIFEST.json').write_text(json.dumps({'date_local':'2026-10-28','timezone':'Asia/Bangkok','sources':evidence,'external_references':[{'id':k,'title':n,'url':u} for k,n,u in external]},ensure_ascii=False,indent=2),encoding='utf8')

doc=Document();sec=doc.sections[0];sec.page_width=Mm(210);sec.page_height=Mm(297)
sec.top_margin=Mm(19);sec.bottom_margin=Mm(19);sec.left_margin=Mm(20);sec.right_margin=Mm(20)
normal=doc.styles['Normal'];normal.font.name='Times New Roman';normal.font.size=Pt(11.5)
normal.paragraph_format.line_spacing=1.12;normal.paragraph_format.space_after=Pt(6)
for name,size in [('Title',23),('Heading 1',15),('Heading 2',12.5),('Heading 3',11.5)]:
 style=doc.styles[name];style.font.name='Times New Roman';style.font.size=Pt(size);style.font.color.rgb=RGBColor(0,0,0)
 style.paragraph_format.keep_with_next=True;style.paragraph_format.space_before=Pt(13);style.paragraph_format.space_after=Pt(6)
for style in ['Normal','Title','Heading 1','Heading 2','Heading 3']:
 rpr=doc.styles[style].element.get_or_add_rPr();fonts=rpr.find(qn('w:rFonts'))
 if fonts is None:fonts=OxmlElement('w:rFonts');rpr.append(fonts)
 for key in ['asciiTheme','hAnsiTheme','eastAsiaTheme','cstheme','csTheme']:
  fonts.attrib.pop(qn('w:'+key),None)
 for key in ['ascii','hAnsi','eastAsia','cs']:fonts.set(qn('w:'+key),'Times New Roman')
for root in [doc.element,doc.styles.element]:
 for border in list(root.xpath('.//w:pBdr')):border.getparent().remove(border)
def add_link(p,label,url):
 h=OxmlElement('w:hyperlink');h.set(qn('r:id'),p.part.relate_to(url,RT.HYPERLINK,is_external=True))
 r=OxmlElement('w:r');props=OxmlElement('w:rPr');color=OxmlElement('w:color');color.set(qn('w:val'),'1F4E79');props.append(color);r.append(props)
 t=OxmlElement('w:t');t.text=label;r.append(t);h.append(r);p._p.append(h)
def inline(p,s):
 pattern=r'(\[[^\]]+\]\([^)]+\)|\*\*[^*]+\*\*|`[^`]+`)'
 for part in re.split(pattern,s):
  if not part:continue
  link=re.fullmatch(r'\[([^\]]+)\]\(([^)]+)\)',part)
  if link:add_link(p,link[1],link[2]);continue
  run=p.add_run(part[2:-2] if part.startswith('**') else part[1:-1] if part.startswith('`') else part)
  if part.startswith('**'):run.bold=True
  if part.startswith('`'):
   run.font.name='Consolas';run.font.size=Pt(9)
def add_table(lines):
 matrix=[[v.strip() for v in line.strip().strip('|').split('|')] for line in lines]
 matrix=[r for r in matrix if not all(re.fullmatch(r':?-+:?',c) for c in r)]
 n=len(matrix[0]);assert all(len(row)==n for row in matrix)
 tbl=doc.add_table(rows=0,cols=n);tbl.alignment=WD_TABLE_ALIGNMENT.CENTER;tbl.autofit=False
 if n==2:fractions=[.28,.72]
 elif n==3:fractions=[.2,.35,.45]
 elif n==4:fractions=[.07,.32,.26,.35] if matrix[0][0]=='Mã' else [.23,.26,.26,.25]
 elif n==5:fractions=[.18,.14,.2,.2,.28]
 elif n==6:fractions=[.14,.27,.145,.145,.145,.155]
 else:fractions=[.12,.14,.18]+[.56/(n-3)]*(n-3)
 for col,f in zip(tbl.columns,fractions):col.width=Mm(170*f)
 borders=OxmlElement('w:tblBorders')
 for edge in ['top','left','bottom','right','insideH','insideV']:
  e=OxmlElement('w:'+edge);e.set(qn('w:val'),'single');e.set(qn('w:sz'),'4');e.set(qn('w:color'),'D9D9D9');borders.append(e)
 tbl._tbl.tblPr.append(borders)
 for i,row in enumerate(matrix):
  cells=tbl.add_row().cells
  trpr=tbl.rows[-1]._tr.get_or_add_trPr();trpr.append(OxmlElement('w:cantSplit'))
  if i==0:trpr.append(OxmlElement('w:tblHeader'))
  for j,(cell,value) in enumerate(zip(cells,row)):
   cell.width=Mm(170*fractions[j]);cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
   tcpr=cell._tc.get_or_add_tcPr();shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'234A66' if i==0 else ('F2F5F7' if i%2==0 else 'FFFFFF'));tcpr.append(shade)
   margins=OxmlElement('w:tcMar')
   for side,val in [('top','70'),('bottom','70'),('left','85'),('right','85')]:
    e=OxmlElement('w:'+side);e.set(qn('w:w'),val);e.set(qn('w:type'),'dxa');margins.append(e)
   tcpr.append(margins)
   p=cell.paragraphs[0];p.paragraph_format.space_after=Pt(0);p.paragraph_format.line_spacing=1.05
   p.paragraph_format.keep_with_next=i==0
   p.alignment=WD_ALIGN_PARAGRAPH.CENTER if re.fullmatch(r'[0-9.,/ +%→−-]+',value) or value in ['Real','Render','Có','single','all'] else WD_ALIGN_PARAGRAPH.LEFT
   inline(p,value)
   for run in p.runs:run.font.size=Pt(9 if n>=6 else 9.5);run.bold=i==0;run.font.color.rgb=RGBColor(255,255,255) if i==0 else RGBColor(0,0,0)
 p=doc.add_paragraph();p.paragraph_format.space_after=Pt(2);p.paragraph_format.space_before=Pt(0);p.paragraph_format.line_spacing=0.3;p.add_run().font.size=Pt(2)
lines=text.splitlines();i=0
while i<len(lines):
 line=lines[i].strip()
 if not line:i+=1;continue
 if line.startswith('|'):
  block=[]
  while i<len(lines) and lines[i].strip().startswith('|'):block.append(lines[i]);i+=1
  add_table(block);continue
 if line.startswith('# '):p=doc.add_paragraph(style='Title');inline(p,line[2:])
 elif line.startswith('## '):p=doc.add_paragraph(style='Heading 1');inline(p,line[3:])
 elif line.startswith('### '):p=doc.add_paragraph(style='Heading 2');inline(p,line[4:])
 elif line.startswith('- '):p=doc.add_paragraph(style='List Bullet');inline(p,line[2:])
 else:
  p=doc.add_paragraph();inline(p,line)
  p.paragraph_format.widow_control=True
 i+=1
footer=sec.footer.paragraphs[0];footer.alignment=WD_ALIGN_PARAGRAPH.CENTER
footer.add_run('Trang ').font.size=Pt(9)
field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');footer._p.append(field)
doc.core_properties.title='Báo cáo tái lập M3Diff và các hướng cải thiện đã thực nghiệm';doc.core_properties.author='Codex';doc.core_properties.subject='Tái lập và đánh giá các phương án cải thiện M3Diff trên OmniDiff'
docx=HERE/'BAO_CAO_M3DIFF_CHI_TIET.docx';doc.save(docx)
with zipfile.ZipFile(docx) as z:assert z.testzip() is None
summary={'markdown':str(output),'docx':str(docx),'whitespace_words':len(text.split()),'characters':len(text),'tables':len(doc.tables),'paragraphs':len(doc.paragraphs),'evidence_files':len(evidence),'body_sections':28,'appendices':4}
(HERE/'BUILD_SUMMARY.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(summary,ensure_ascii=False,indent=2))
