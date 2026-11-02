# Minimal caption color verifier V4

24 development pairs; 1 captions edited.
Locator supplies object regions; corresponding color pixels verify the replacement clause. No full-caption rewrite.
Same development sample as earlier iterations. This is proof-of-concept, not held-out improvement evidence.

|Split|Arm|BLEU-4 x100|METEOR x100|ROUGE-L x100|CIDEr x100|
|---|---|---:|---:|---:|---:|
|Real|baseline|10.77|15.38|26.82|11.43|
|Real|grounded|10.40|14.95|26.92|19.06|
|Real|v2|10.77|15.38|26.82|11.43|
|Real|v4|10.77|15.38|26.82|11.43|
|Render|baseline|15.98|19.89|33.85|16.42|
|Render|grounded|10.96|16.76|31.92|7.47|
|Render|v2|15.98|19.89|33.85|16.42|
|Render|v4|15.56|19.77|33.57|20.87|