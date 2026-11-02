# NVIDIA LocateAnything-3B: thử định vị trên OmniDiff

Thử định tính trên 4 truy vấn; chưa phải benchmark hoặc phép đo cải thiện M3Diff.

## real_before_box
Locate a single instance that matches the following description: the green storage box.

Số box: 1; thời gian: 2.37s.

<ref>the green storage box</ref><box><712><0><998><169></box><|im_end|>

![Result](real_before_box_boxes.png)

## real_after_box
Locate a single instance that matches the following description: the green storage box.

Số box: 1; thời gian: 2.92s.

<ref>the green storage box</ref><box><584><0><784><67></box><|im_end|>

![Result](real_after_box_boxes.png)

## real_before_objects
Locate all the instances that matches the following description: storage box</c>cabinet.

Số box: 8; thời gian: 1.57s.

<ref>storage box</ref><box><0><0><169><40></box><box><0><108><41><144></box><box><0><198><54><240></box><box><27><53><167><145></box><box><52><143><157><243></box><box><711><75><981><168></box><box><721><1><996><91></box><ref>cabinet</ref><box><146><132><1000><376></box><|im_end|>

![Result](real_before_objects_boxes.png)

## render_people
Locate all the instances that matches the following description: person.

Số box: 1; thời gian: 1.12s.

<ref>person</ref><box><315><406><402><637></box><|im_end|>

![Result](render_people_boxes.png)
