"""Lock four unchanged image cases crossed with all ten training-question styles."""
from pathlib import Path
import json,hashlib
HERE=Path(__file__).parent;OUT=HERE.parent/'prompt_probe';OUT.mkdir(exist_ok=True)
rows=json.loads((HERE/'train.json').read_text());templates=sorted({r['conversations'][0]['value'] for r in rows});assert len(templates)==10
questions={q['id']:q for q in json.loads((HERE/'eval_questions.json').read_text())};manifest={q['id']:q for q in json.loads((HERE/'eval_manifest.json').read_text())}
sources=['new__clothesline__zoom_in_1p10','new__computer_desk__roll_8_safe','new__bunk_bedroom__zoom_out_reverse_1p10','new__bicycle_alley__identity'];qs=[];meta=[]
for i,rid in enumerate(sources):
 for j,prompt in enumerate(templates):
  q=questions[rid];newid=f'case_{i:02d}_prompt_{j:02d}';qs.append({'id':newid,'image':q['image'],'conversations':[{'from':'human','value':prompt}]})
  meta.append({**manifest[rid],'id':newid,'source_case_id':rid,'prompt_index':j,'prompt':prompt})
for n,obj in [('eval_questions.json',qs),('eval_manifest.json',meta)]: (OUT/n).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf8')
protocol={'run':'invariance_prompt_probe_v1','sources_chosen_before_any_probe_outputs':sources,'n_cases':40,'n_models':3,'models':['baseline','old_mixed','balanced'],'templates':templates,'question_sha256':hashlib.sha256((OUT/'eval_questions.json').read_bytes()).hexdigest(),'criterion':'No scene/object/light changes in any of these40pairs. Score physicalFP, illumination, incorrect global explanations and identity differences; fixed source cases repeated across10 question styles. Compare same images and prompts for all models. No new scenes or natural recall test here.','selection':'Balanced preferred for full official evaluation only if factual72 gate passes and joint-error count across40 probe cases is not above old mixed; both prior fixed-prompt and variable-prompt results must be reported. Selection before any full benchmark scores.','limits':'Four development source cases, fixed conditions, one seed and assistant labels. Not independent benchmark proof. No prompt/LR tuning after this probe.'}
(OUT/'protocol.json').write_text(json.dumps(protocol,ensure_ascii=False,indent=2),encoding='utf8');print({'n_questions':40,'n_generations':120})
