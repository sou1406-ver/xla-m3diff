import json,collections
from pathlib import Path
root=Path(__file__).resolve().parents[1]/'outputs/curated_sft'
qs=json.loads((root/'eval_questions.json').read_text(encoding='utf8'))
for split in ['Real','Render']:
    parent={}
    def find(x):
        parent.setdefault(x,x)
        if parent[x]!=x:parent[x]=find(parent[x])
        return parent[x]
    rows=[q for q in qs if q['split']==split]
    for q in rows:
        a,b=map(find,q['image']);parent[a]=b
    clusters=collections.Counter(find(q['image'][0]) for q in rows)
    print(split,'pairs',len(rows),'unique images',len(parent),'shared-image clusters',len(clusters),'cluster sizes',sorted(clusters.values(),reverse=True))
