# Rà lỗi caption M3Diff trên ảnh train

Codex assistant visual review of original train images and close crops; not independently human adjudicated.

48 cặp đã xem, 44 cặp giữ lại; 4 cặp loại: 1, 19, 43, 44. Đây là rà trực quan của trợ lý, chưa được người gán nhãn độc lập xác nhận.

## Cặp 0 — accept

ID: train_78a8dc3c50296d1aac96

Caption gốc: There are no noticeable differences between the two images.

Baseline: The computer screen has been closed. The person's right hand, which was previously on the mouse, is now placed on the table. The black headphones that were hanging on the left side of the table have disappeared.

Nhãn sửa: The camera viewpoint shifts to the right, showing the back of the person's head more directly. The monitor remains on and the objects on the desk remain present.

Bằng chứng: Both monitor screens are lit; headphones remain on the desk; the view shifts while the same desk objects are visible.

Loại lỗi: hallucinated_removal, viewpoint_confusion

Ảnh: images/review_00.jpg

## Cặp 1 — reject

ID: train_3e7039399babb789059c

Caption gốc: The yellow bottle on the left side of the desk against the wall disappears.

Baseline: The yellow bottle on the right side of the desk against the wall disappears. The white handle toy in front of the computer is moved to the left side of the table. The blue handle toy moves to the right side of the white handle toy. The white handle toy on the left side of the desk against the wall disappears. The green phone on the right side of the desk rotates 90 degrees clockwise. A book with a green cover appears on the left side of the top shelf.

Nhãn sửa: None

Bằng chứng: Upright originals show camera tilt/rightward crop; yellow bottle near far-left lower boundary may leave field of view. Cannot establish true removal or all object movements confidently.

Loại lỗi: viewpoint_confusion, uncertain_visibility

Ảnh: images/review_00.jpg

## Cặp 2 — accept

ID: train_e4b528f1146c2f4218c0

Caption gốc: On the yellow notebook on the right side, a purple notebook suddenly appears.The cup and the ice cubes in hand disappear. The book on the table is moved to the position originally occupied by the cup. The person picks up the two pens that were previously in front of the computer. The notebook featuring a little bear moves to the right onto the pile of books on the right, and in its original place a white shelf appears. A mobile phone shows up in front of the white fan.

Baseline: The person's hands move from picking up ice cubes to writing in a notebook. The ice cubes disappear. A phone appears on the desk.

Nhãn sửa: The person changes from picking up ice from a tray to writing in an open notebook while holding two pens. The ice tray and metal cup are removed. A phone appears in front of the fan. The small illustrated notebook moves onto the stack of books on the right, and a purple notebook is added to the stack.

Bằng chứng: The before tray and cup are absent in after; phone visible below fan; two pens in writing hand; stacked notebooks visible.

Loại lỗi: omission

Ảnh: images/review_01.jpg

## Cặp 3 — accept

ID: train_bfde9d418ba3d331e6e9

Caption gốc: Before the changes, all the toys inside the storage box were facing the front of the scene, towards the camera.

Baseline: The pink toy pig wearing an orange outfit in the back right has disappeared. The pink toy pig wearing a blue outfit on the right has turned to face the front of the scene. The pink toy pig wearing a red outfit in the front right has turned to face the left side of the scene. The pink toy pig wearing a green outfit in the front left has turned to face the back of the scene.

Nhãn sửa: The toys in the storage box turn from facing the camera to facing away. The teddy bear, gray elephant, and pink pig toys remain in the box.

Bằng chứng: Backs of all plush toys visible after, same toy inventory. No orange-clothed pig removed.

Loại lỗi: hallucinated_removal, wrong_orientation, wrong_object

Ảnh: images/review_01.jpg

## Cặp 4 — accept

ID: train_3df175a578fbeedeb43b

Caption gốc: The green wall hanging toy that was previously on the far left has moved to the far right hook. The blue wall hanging toy that was on the third hook from the left has moved to the far left hook. The pink wall hanging toy that was previously on the second hook from the left has moved to the hook on its right. A new red wall hanging toy has appeared on the second hook from the left. A new Ultraman toy box has appeared on the bed, against the wall.

Baseline: A new Ultraman toy box has appeared on the bed against the wall, positioned in front of the fourth hanger. The second hanger from the left, which was green, has changed to blue.

Nhãn sửa: The hanging learning boards are rearranged from green, pink, and blue on the first three hooks to blue, a new pink number board, pink, and green across all four hooks. A red toy box appears on the bed against the wall.

Bằng chứng: Visible colored boards and number icons identify moved boards and new pink board.

Loại lỗi: identity_confusion, omission

Ảnh: images/review_02.jpg

## Cặp 5 — accept

ID: train_facf52d0b063df43f36f

Caption gốc: A book with only a part visible in the upper left corner of the screen disappears. The red notebook under the phone stand turns blue. The blue small toilet paper behind the phone stand disappears. The phone stand moves forward towards the edge of the table. A pure white rectangular box next to the data cable moves to the lower left corner of the screen, and a bottle of watch disinfectant appears at its original position.

Baseline: The red notebook on the left side of the screen disappears, and a blue notebook appears in its place. The white phone holder moves to the position of the red notebook, and a pure white rectangular box next to the data cable moves to the original position of the white phone holder. A pure white rectangular box appears at the bottom of the screen. The blue - white - green - yellow - red keychain on the black leather bag in the center of the screen disappears. The blue - white - green - yellow - red keychain on the black leather bag disappears. The black water cup in the top right corner of the screen moves to the bottom right corner of the screen. A bottle of watch disinfectant appears at the bottom right corner of the screen.

Nhãn sửa: The notebook beneath the phone stand changes from red to blue, and the stand shifts forward. The blue tissue packet is no longer on top of the notebook and is visible in the drawer. The white square box moves from the drawer's right side to its front-left corner, and a small clear bottle appears in its former location. The dark tumbler and black bag remain present.

Bằng chứng: Tumbler and bag stay in same positions; blue tissue packet visible below wallet after; white box and new bottle visible.

Loại lỗi: hallucinated_removal, hallucinated_movement, repetition

Ảnh: images/review_02.jpg

## Cặp 6 — accept

ID: train_91bbee7637e311643138

Caption gốc: - The scene has not changed.

Baseline: The black mouse on the right side of the screen has disappeared. The blue pen and red pen in front of the notebook on the left side of the screen have swapped positions. A pure white rectangular box has appeared to the left of the stapler in the cabinet.

Nhãn sửa: The camera angle and framing change, but the desk and drawer objects remain in place. The black mouse is still visible at the right edge, the pens retain their arrangement, and the white square box remains to the left of the stapler.

Bằng chứng: Matched desk and drawer objects persist with camera parallax; mouse visible after at right edge.

Loại lỗi: hallucinated_removal, hallucinated_movement, viewpoint_confusion

Ảnh: images/review_03.jpg

## Cặp 7 — accept

ID: train_99391aa787b0fc3a4fa4

Caption gốc: Above the center of the plate, there are six green grapes arranged in a petal shape, with one purple grape in the center. Four newly appeared dark green cucumber slices cut into long strips connect the four groups of grapes arranged in a flower shape. Next to the cucumber strip in the lower right corner, there are two cucumber slices cut into leaf shapes. Next to the cucumber strip in the lower left corner, there are two cucumber slices cut into leaf shapes.

Baseline: Four dark purple grapes have been added to the center of the plate, forming a circle. Four cucumber slices cut into leaf shapes have been added to the outside of the circle formed by the four dark purple grapes.

Nhãn sửa: A fourth grape flower appears at the top of the plate, with green grapes surrounding one purple grape. Curved cucumber strips are added to connect the four flowers into a ring, and four leaf-shaped cucumber slices appear near the lower left and lower right of the ring.

Bằng chứng: Three grape flowers before, four after; only one additional purple-grape center.

Loại lỗi: wrong_count, wrong_addition

Ảnh: images/review_03.jpg

## Cặp 8 — accept

ID: train_5440f11ddcef077aa5bc

Caption gốc: The black storage bag in the lower right side of the scene has disappeared. The Ultraman toy box, which was originally placed vertically on the right side, is now gone. The white card with black scissors printed on it, which was in the center of the scene, has been replaced with a card featuring a table tennis racket and a table tennis ball. The badminton racket, which was previously placed vertically behind the Ultraman toy box, is now located above the yellow suitcase on the left side of the scene and is placed horizontally.

Baseline: The card with a white background, black scissors pattern, and red details on the right side of the scene has been replaced with a card featuring a table tennis racket and a table tennis ball. The Ultraman toy box that was leaning against the wall on the right side of the scene has disappeared.

Nhãn sửa: The covered badminton racket moves from standing upright on the right to lying horizontally across the light-colored bag on the left. The red toy box and the small black bag below it disappear. The scissors card is replaced by a card showing a table-tennis paddle and ball.

Bằng chứng: Racket cover, toy box, small bag, and printed cards all identifiable across views.

Loại lỗi: omission

Ảnh: images/review_04.jpg

## Cặp 9 — accept

ID: train_52e0857b34c40e05b47d

Caption gốc:  A pool appears in the background.

Baseline: The diver's posture changes from standing on the diving board with feet together, body upright, and gaze directed toward the front of the scene to standing on the edge of the pool with feet apart, knees slightly bent, and gaze directed downward.

Nhãn sửa: The camera view changes from the diver's side to a frontal view, revealing the swimming pool below and behind him. The diver remains standing on the elevated diving platform.

Bằng chứng: Platform visible in both; pool revealed by frontal viewpoint, not diver moving down to pool edge.

Loại lỗi: viewpoint_confusion, wrong_location, hallucinated_posture_change

Ảnh: images/review_04.jpg

## Cặp 10 — accept

ID: train_d8267b6973480f2addf7

Caption gốc: The green bird to the left of the fruit in the center appears to peck at the ground. The green bird in the upper right corner of the fruit has lowered its head, no longer stretching its neck to look toward the back left. The green bird to the left in the scene has disappeared.

Baseline: The green bird on the left side of the fruit, facing left with its head lowered, has disappeared. The green bird in the upper right corner, which was previously looking toward the front left, is now looking toward the back right. The green bird on the branch to the right of the fruit, which was previously looking toward the back right, is now looking toward the front left. A new green bird has appeared at the bottom center of the fruit, with both of its heads lowered and its tail raised.

Nhãn sửa: Two green birds now bend their heads down toward the fruit to feed, with their tails raised. A third green bird remains on the branch at the right side of the fruit.

Bằng chứng: Three visible birds in both images; two after have heads together over fruit, no two-headed bird.

Loại lỗi: wrong_count, hallucinated_addition, wrong_posture

Ảnh: images/review_05.jpg

## Cặp 11 — accept

ID: train_a24f16b32285bf5cf857

Caption gốc: The number of forks on the left side of the plate has increased to two, and the text "Dinner Fork" above the forks has disappeared. The number of knives on the right side of the plate has increased to two, and the text "Dinner Knife" above the knives has disappeared. Above the plate, there is an additional spoon, with the text "Dessert Spoon" appearing to the left of it.

Baseline: The text on the left side of the screen changes from "Dinner Fork" to "Dessert Spoon."  
A new spoon has appeared above the central plate.  
On the left side of the plate, a new knife has appeared.

Nhãn sửa: A spoon and the label 'Dessert Spoon' appear next to the plate. There are now two forks and two knives instead of one of each, while the 'Dinner Fork' and 'Dinner Knife' labels disappear.

Bằng chứng: Visible before one fork/knife; after two each and new spoon/label. Baseline calls added fork a knife.

Loại lỗi: wrong_object, wrong_count, wrong_text_location

Ảnh: images/review_05.jpg

## Cặp 12 — accept

ID: train_dd0b392855e9a3f3b5a3

Caption gốc: The perspective shifts to the left as a whole.

Baseline: The Ultraman figurine and the Piggy Hero figurine with its mouth open have swapped positions. A new figurine resembling a white pig has appeared in front of the Ultraman figurine.

Nhãn sửa: The camera viewpoint shifts and tilts, changing the apparent positions of the toys. The same figurines remain on the shelf, with no clear addition or swap.

Bằng chứng: Same figurine order and inventory across tilted views; white head figurine already visible before.

Loại lỗi: viewpoint_confusion, hallucinated_addition, hallucinated_swap

Ảnh: images/review_06.jpg

## Cặp 13 — accept

ID: train_f352838f6d8762a2cd7b

Caption gốc: The hands change from being lightly clasped across the chest with fingers slightly bent to being raised, with the right hand lifted slightly to the left side and the left hand placed on the table. The eyes change from being closed to being open. The head, which was slightly tilted upward, shifts to a neutral orientation.

Baseline: The hands, which were crossed in front of the chest with fingers slightly bent, are now extended to the sides. The eyes, previously closed, are now open.

Nhãn sửa: The woman opens her eyes and lowers her head slightly. Her hands separate from a clasped position at her chest: one hand is raised to the side while the other rests on the table.

Bằng chứng: Eyes closed before/open after; after one palm rests on tabletop and other lifted, not both arms extended sideways.

Loại lỗi: wrong_posture

Ảnh: images/review_06.jpg

## Cặp 14 — accept

ID: train_c635fc4f5de58402c71e

Caption gốc: The text at the top of the image changes from "Look2" to "LOOK3". The light yellow hat on the person's head disappears. The brown silk scarf tied around the woman's waist disappears. The woman's previously loose hair is now tied up. The posture changes from both hands holding a woven straw bag to the left hand naturally hanging down, and the right hand resting on the crossbody bag worn over the left shoulder. The light yellow flat leather shoes are replaced with white flat canvas shoes. A new black strap watch appears on the wrist of the naturally hanging left hand.

Baseline: The text at the top of the image changes from "Look2" to "Look3". The person's hat disappears. The person's posture changes from standing with legs apart and hands holding a woven bag in front of the body to standing with legs together, right hand hanging naturally, left hand on the waist, and the brown leather shoulder bag slung over the right shoulder. The white flat leather shoes are replaced by white canvas shoes.

Nhãn sửa: The text changes from 'Look2' to 'Look3'. The woman's straw hat is removed, her loose hair is tied back, and the woven handbag held in front is replaced by a brown shoulder bag. Her light-colored shoes change to white lace-up sneakers, and one hand hangs at her side instead of holding the woven bag.

Bằng chứng: Hat, hair, bags and shoe differences visible; avoid uncertain anatomical side and wristwatch provenance.

Loại lỗi: wrong_side, omission

Ảnh: images/review_07.jpg

## Cặp 15 — accept

ID: train_343cd111c16ac59f5de3

Caption gốc: Four people face the camera standing on their left leg, with their right leg bent and resting on the other leg, hands clasped together at the chest. Turn the body to face the left side of the frame. Stand on the right leg, lift the left leg high, swing the left hand back, and raise the right hand to make a sun-shading gesture.

Baseline: The four women's hands move from being clasped together in front of the chest to a pose where they raise their right legs and extend their left arms forward, with their heads turned to the right.

Nhãn sửa: The four women change from balancing on one leg with the lifted foot resting across the standing leg and palms together at their chests to lifting a bent knee forward while separating their arms. Several now hold a hand near their forehead to shade their eyes.

Bằng chứng: Both views still largely face camera; after knees point forward and three women shade eyes, no uniform left-arm-forward pose.

Loại lỗi: wrong_pose, wrong_orientation

Ảnh: images/review_07.jpg

## Cặp 16 — accept

ID: train_a6b64f2f8ef0805eed50

Caption gốc: Four figures stand close together, with the two on the left extending their right hands and leaning forward. The third person from the right to left poses with both hands showing a thumbs-up gesture. The fourth person is next to the third person, forming a line of four figures, with each person's arms extending horizontally and gradually rising from front to back.

Baseline: The number of people in the frame has decreased from five to four. The figures are arranged in a formation, with the person at the bottom squatting and supporting the three individuals above. The person on the far left raises their right hand high and bends forward, while the person on the far right also raises their right hand high and bends forward. The person in the middle, who was previously wearing a light blue jacket and black pants, is now wearing a green jacket and white pants.

Nhãn sửa: The four people change from standing close together in a side-by-side group to lining up one behind another. The front person crouches, and all four extend both arms horizontally. Their clothing remains the same.

Bằng chứng: Exactly four in each view, identifiable same pastel coats; line depth rather than supporting others.

Loại lỗi: wrong_count, identity_confusion, wrong_clothing_change

Ảnh: images/review_08.jpg

## Cặp 17 — accept

ID: train_8bd16c8f7d3936467aac

Caption gốc: The razor head, which was facing the right side, now turns its back to the camera, changing its orientation. The small blue tube of skincare product, previously in the middle of the screen, has been moved to the front right of the toothbrush cup. A large brown-yellow tube of skincare product has appeared in the original position of the small blue tube.

Baseline: The small blue skincare tube in the center of the screen has moved to the right front of the toothbrush cup. A large brownish-yellow skincare tube has appeared to the left of the toothbrush cup.

Nhãn sửa: The small dark-blue tube moves from in front of the pump bottle to the right of the toothbrush cup. A larger patterned tube appears in its former area. The electric razor rotates so that the front of its head faces the camera more directly.

Bằng chứng: Large new patterned tube, relocated small tube and head rotation visible; baseline omitted razor.

Loại lỗi: omission

Ảnh: images/review_08.jpg

## Cặp 18 — accept

ID: train_89bca5874046a83c8f55

Caption gốc: The outfit changes from a white T-shirt with a purple wool cardigan and dark gray high-waisted wide-leg pants to a white semi-transparent shirt with a black camisole underneath and a dark gray long skirt. The left hand, previously in the pants pocket, is now placed behind the back, while the right hand is holding a gray handbag. In the second image, the person is wearing black shoes.

Baseline: The person's expression changes from a smile to a smile revealing teeth. The outfit changes from a white T-shirt with a purple wool cardigan and gray high-waisted wide-leg pants to a white semi-transparent shirt with a gray inner layer, paired with a long dark purple skirt. The left hand moves from being in the pocket to holding a gray handbag. The right hand moves from being in the pocket to hanging naturally. The posture changes from standing upright with a slightly raised left hand to standing upright with both hands naturally hanging down.

Nhãn sửa: The framing widens to show the woman's full outfit. Her purple cardigan, white T-shirt, and wide trousers are replaced by a sheer white blouse over a dark inner top and a long dark skirt. She now holds a small gray handbag in one hand while the other arm is behind her back, and her black shoes become visible.

Bằng chứng: Wider after frame, skirt replaces trousers, blouse replaces cardigan, handbag held on image-left side.

Loại lỗi: wrong_side, inconsistent_pose, omission

Ảnh: images/review_09.jpg

## Cặp 19 — reject

ID: train_0323bd137e2de0a49119

Caption gốc: The person's expression changes from a somewhat exaggerated look with the mouth slightly open, eyes half-closed, displaying a sense of surprise or confusion, with the head slightly leaning forward, and the posture appearing somewhat tired or surprised, to an extremely angry expression with the mouth wide open, showing teeth, eyes wide open, eyebrows furrowed, conveying intense anger. The entire posture appears forceful, as if shouting or venting emotions.

Baseline: The person's expression changes from a slightly open mouth, with eyes slightly closed and eyebrows slightly furrowed, conveying a sense of surprise or confusion, to an intense scream with wide-open eyes, tightly clenched teeth, and furrowed brows, expressing extreme anger or fear.

Nhãn sửa: None

Bằng chứng: Baseline already captures the visible facial-expression change. Minor 'clenched teeth' wording is not sufficient to prioritize as a strong semantic correction.

Loại lỗi: wrong_mouth_state

Ảnh: images/review_09.jpg

## Cặp 20 — accept

ID: train_9abf9da22a3e43cf9cca

Caption gốc: The background has changed from a blue gradient to white. The text has shifted from the upper left corner to the center of the image. The font size has decreased, and the font has become thinner. The third line of text, "诚信、", has been moved to the second line.

Baseline: The background of the image has changed from a blue gradient to white. The text in the center of the image has shifted downward.

Nhãn sửa: The background changes from a pale blue gradient to plain white. The Chinese text block shifts downward toward the center and becomes smaller and thinner, with the line breaks rearranged.

Bằng chứng: Same text content reflowed in lighter smaller type, lower on white page.

Loại lỗi: omission

Ảnh: images/review_10.jpg

## Cặp 21 — accept

ID: train_4103242ce69e97760d83

Caption gốc: The ambient lighting has slightly brightened. The background changes, and the plate moves from the white cutting board to the yellow tabletop. Outside the dragon fruit slices, which have been cut into fan shapes and arranged in a circle on the outer side of the plate, there is an additional layer of lime slices cut into arcs. Inside, there is an additional layer of kiwi slices cut into ovals. Within the kiwi slices, there is a layer of orange slices cut into semi-circles, forming a complete circle. Inside the oranges, there are seven dragon fruit balls, one in the center and six around it.

Baseline: The brightness of the scene has increased. Inside the circle made of dragon fruit slices, there is an additional circle formed by kiwi slices cut into ovals. Inside the circle formed by the kiwi slices, there is an additional circle formed by semicircular orange slices. Inside the circle formed by the orange slices, there are seven dragon fruit slices cut into ovals arranged in a circle, and inside this circle, there are seven purple dragon fruit balls stacked together.

Nhãn sửa: The plate is shown more brightly against a yellow background. Green citrus wedges are added around the outer dragon-fruit slices, a ring of kiwi slices fills the middle, and a hollowed citrus half containing red fruit balls is placed in the center.

Bằng chứng: Center is a citrus shell/bowl, not additional rings of white fruit and orange semicircles.

Loại lỗi: wrong_object, wrong_count, hallucinated_addition

Ảnh: images/review_10.jpg

## Cặp 22 — accept

ID: train_318ec870a30691ac0938

Caption gốc: A new black wristwatch has appeared in the center of the scene. A new pack of green coffee bags has appeared in the lower center of the scene. The white card in the bottom right corner of the drawer, which previously featured a seal, has been replaced with a card displaying a dolphin. The blue disposable raincoat on the right side of the drawer has changed its orientation and is now placed upside down inside the drawer. The blue ball in the bottom left corner of the drawer has disappeared.

Baseline: The blue disposable raincoat on the right side of the drawer has changed its orientation and is now placed upside down inside the drawer. The white card in the bottom right corner of the drawer, which previously featured a seal, has been replaced with a card displaying a dolphin. The blue ball that was in the bottom left corner of the drawer has disappeared.

Nhãn sửa: A black wristwatch appears across a green sachet in the center of the drawer. The blue raincoat package turns upside down, the seal card changes to a dolphin card, and the small blue ball at the lower left disappears.

Bằng chứng: Watch and central green sachet visible after; blue ball absent, printed card and raincoat orientation change.

Loại lỗi: omission

Ảnh: images/review_11.jpg

## Cặp 23 — accept

ID: train_1d5ff2a551f0f467a8e8

Caption gốc: The ambient lighting has brightened. The position of the book "Percy and Pip Big Monster" at the top right has been swapped with the book "Animal World" at the middle right. The book "Percy and Pip Scooter" at the top left has been replaced by the book "Daily Necessities." The blue book "Colors and Shapes" at the middle left has been replaced by the book "Percy and Pop Wet Pants." The book "Answer Loudly 'Hey'" at the bottom left corner has been replaced by the book "Who Cried."

Baseline: The ambient lighting has brightened. The book with the cover "生活用品" on the left and the book with the cover "动物世界" on the right have swapped positions. The book with the cover "蓝色封面的书" in the upper left corner has disappeared, and a new book with the cover "粉色和白色相间的书" has appeared in its place. The book with the cover "蓝色封面的书" in the middle of the screen has disappeared, and a new book with the cover "棕色背景的书" has appeared in its place. The book with the cover "白色背景黄色字体'生活'的书" in the lower left corner has disappeared, and a new book with the cover "白色背景黄色字体'生活'的书" has appeared in its place.

Nhãn sửa: The scene becomes brighter. The green animal book and the illustrated rabbit book on the right exchange upper and middle positions. On the left, the top book is replaced by an orange book showing a green dish, the middle book by a yellow rabbit book, and the bottom book by a book showing a brown bear with blocks. The bottom-right elephant book stays in place.

Bằng chứng: Book-cover images and positions visually matched; do not invent untranslated titles.

Loại lỗi: hallucinated_swap, wrong_text, omission

Ảnh: images/review_11.jpg

## Cặp 24 — accept

ID: train_ef0d654539d4f0ecf827

Caption gốc: The two black-covered books, which were added to the scene, stacked on the wooden low stool with a black cushion in front right of the scene, have been removed. The black cushion near the large window on the right side of the sofa is slightly tilted outward.

Baseline: The black-covered book on the wooden low stool with a black cushion in front of the right sofa has disappeared. The black-covered book on the left side of the wooden low stool with a black cushion in front of the left sofa is no longer visible. The black-covered book on the right side of the wooden low stool with a black cushion in front of the left sofa is no longer visible. The black-covered book on the right side of the coffee table has disappeared. The black-covered book on the left side of the coffee table has disappeared. The black-covered book on the right side of the coffee table has disappeared. The black-covered book on the left side of the coffee table has disappeared.

Nhãn sửa: The two stacked books on the front-right round stool are removed, while the books on the central coffee table remain. One cushion on the right sofa changes its tilt.

Bằng chứng: Only stool books removed; coffee-table books persist; cushion angle changes.

Loại lỗi: hallucinated_removal, repetition, omission

Ảnh: images/review_12.jpg

## Cặp 25 — accept

ID: train_63456f17a52b26f5cc4a

Caption gốc:  The white 'Toxi' logo on the door of the orange taxi on the left side of the scene is absent. The man in a grey shirt and black pants who was on the road in front of the house in the middle of the scene is no longer present. In front of the building at the bottom center of the scene, the plant inside the small potted plant to the left of the green door and beneath the blue-and-white awning window is no longer present, leaving only the pot. The blue and white striped canopy above the brown window frame at the street corner has changed to light yellow.

Baseline: The woman wearing a gray top, black pants, and black shoes who was on the road in front of the house is no longer visible. The blue and white striped awning above the window to the left of the green door has changed to solid beige.

Nhãn sửa: The person standing in the road disappears. The white 'Toxi' lettering on the orange taxi door is removed, and the blue-and-white striped awning over the corner window changes to plain beige.

Bằng chứng: Close crop confirms person removal, awning change and text removal in full view. Potted plant removal not confidently established; excluded from corrected target.

Loại lỗi: omission

Ảnh: images/review_12.jpg

## Cặp 26 — accept

ID: train_1b142b6f036e648dbd72

Caption gốc: In the middle of the scene, the two stacked white teacups on the second shelf below the table have vanished.The red and white kettle on the central table has disappeared.There are two brown-yellow pendant lights above the central counter in the room, and the one at the back has disappeared.The dining stool on the left side of the central table has disappeared.In the first shelf of the rack under the central table in the scene, the originally white and blue tableware has all turned green.

Baseline: The red and white kettle on the central counter in the room has disappeared.The stack of white bowls on the second layer of the central counter has changed color from blue to green.

Nhãn sửa: The red-and-white kettle and the stool at the left of the island disappear. The white cups on the middle open shelf disappear, and the containers on the bottom shelf change from blue-gray to green. One of the two pendant lamps above the island is removed.

Bằng chứng: Close crop confirms rear of two overlapping pendant lamps absent; red-white counter kettle gone. Shelf/stool changes clear in full view.

Loại lỗi: omission, wrong_shelf_location

Ảnh: images/review_13.jpg

## Cặp 27 — accept

ID: train_174e2d3eef35c9605440

Caption gốc: The upper painting of the two hanging on the back left wall of the scene has disappeared.The dark blue blanket draped over the right side of the orange sofa in the center of the scene has disappeared.On the wall behind the orange sofa hangs a two-tiered shelf. On the left side of the first shelf, there are two slender turquoise decorative vases placed next to each other, with the one on the right changing color from turquoise to purple.

Baseline: The light in the scene has increased. The turquoise vase on the left side of the second shelf of the wooden rack behind the orange sofa has changed from cyan to purple.

Nhãn sửa: The upper of the two framed pictures on the left wall disappears. The dark teal blanket draped over the right end of the orange sofa is removed. On the lower wall shelf, the right vase of the pair of turquoise vases changes to purple.

Bằng chứng: Upper art absent; teal blanket gone; right of two lower-shelf vases visibly purple.

Loại lỗi: omission

Ảnh: images/review_13.jpg

## Cặp 28 — accept

ID: train_11cef13801fa664c4bd3

Caption gốc: The white teddy bear decoration on the central wooden table has turned its head from facing left to facing right. The glass of water to the right of the stacked paper cups on the wooden table has been removed. The circular white pendant light, originally positioned on the far right of the fixture above the wooden table, has been moved to the chair on the far right of the dining area with a black cushion. The white glass container on the left side of the upper shelf above the window behind the wooden table has increased in size.

Baseline: The white hourglass-shaped lamp on the far right side of the light bar above the wooden table has disappeared. The white teapot on the wooden table has been replaced by a large white ball-shaped decoration. The white cup stacked with other cups in the center of the dining table has disappeared.

Nhãn sửa: The rightmost glowing globe moves from the ceiling fixture onto the right dining chair. The small white bear-shaped ornament on the table changes orientation, and the white bottle at the right end of the table disappears. A white bowl on the lower illuminated wall shelf becomes larger.

Bằng chứng: Close crop confirms white bottle absent and shelf bowl enlarged. Omitted uncertain oven change from the target.

Loại lỗi: wrong_object, movement_as_removal, omission

Ảnh: images/review_14.jpg

## Cặp 29 — accept

ID: train_f0cd5daf498fb787d98d

Caption gốc: A person wearing a white shirt, light beige pants, and white shoes has appeared between the right side of the coffee table and the white sofa, facing the window on the left side of the room, with a beige jacket draped over their left shoulder. The black dumbbell that was previously on the carpet between the coffee table and the white sofa is no longer visible. A glowing blue sign displaying the word "Life" has appeared on the gray carpet in front of the round coffee table. The book with a light blue and yellow striped cover that was on the center of the coffee table is no longer visible.

Baseline: A person wearing a white shirt, light beige pants, and white shoes is now present in the center of the room, facing the gray sofa on the right side. A glowing blue sign displaying the word "Life" has appeared on the gray carpet in front of the round coffee table. The books stacked on the left side of the table have decreased in size.

Nhãn sửa: A person in a white top and beige trousers appears beside the coffee table with a beige jacket draped over one shoulder, facing toward the windows. A glowing blue 'Life' sign appears on the rug in front of the table. The dumbbell on the rug and the light blue-and-yellow book on the table are no longer visible.

Bằng chứng: Person faces image-left windows, not right sofa; left stack of books remains, no clear shrinkage.

Loại lỗi: wrong_orientation, hallucinated_size_change, omission

Ảnh: images/review_14.jpg

## Cặp 30 — accept

ID: train_47663623307f4dc0b2c1

Caption gốc: The surroundings have brightened. A black-covered book on the first shelf to the left of the gray table in the center of the room has disappeared.In front of the gray table in the center of the room are three white oval cushions, with the leftmost cushion now missing.The green potted plant to the left of the gray table in the center of the room has turned solid red.

Baseline: The surroundings have brightened. The green potted plant in the back left corner of the room has been replaced by a red flower arrangement in a tall vase.The black-covered book on the first shelf to the left of the gray table in the center of the room is no longer visible.The white oval cushion in front of the gray table at the front of the scene has disappeared.The white oval cushion on the right side of the gray table at the front of the scene has disappeared.The white oval cushion on the left side of the gray table at the front of the scene has moved to the right.

Nhãn sửa: The room becomes brighter. The leftmost of the three white oval floor cushions disappears, leaving two. The green plant and its pot to the left of the table turn red, and a dark book is removed from the nearby left shelving.

Bằng chứng: Only left floor cushion absent; same plant silhouette and pot change to red.

Loại lỗi: wrong_count, hallucinated_movement, wrong_color_change_as_replacement

Ảnh: images/review_15.jpg

## Cặp 31 — accept

ID: train_edd004308664e329dd7d

Caption gốc: The gray trolley in the rear-right corner of the room, which had a black coffee machine on it, has now disappeared. A person wearing a light-colored long-sleeve shirt, gray pants, and white shoes is standing in front of the conference table, facing the bookshelf at the back of the room. The black office chair that was previously located between the two black chairs in front of the conference table has returned to its original position on the right side of the table. The black office chair in the middle of the conference table has been moved to the front-right side of the table.

Baseline: A man wearing a light blue shirt, gray pants, and black shoes has appeared in the lower left corner of the scene, standing with his back to the camera, facing the bookshelf on the right side of the conference table, with his hands crossed behind his back. The black office chair at the end of the conference table on the right side is missing.

Nhãn sửa: A person in a light shirt and gray trousers appears in front of the conference table, facing the back shelving. The trolley with the coffee machine at the back right disappears, and the chairs along the near and right sides of the table are rearranged.

Bằng chứng: New person, missing rear-right trolley, near chair shifts; exact chair identities not asserted.

Loại lỗi: omission, chair_identity_confusion

Ảnh: images/review_15.jpg

## Cặp 32 — accept

ID: train_44b17c7da334548a9219

Caption gốc: A new gray upholstered armchair has appeared in the center of the room, positioned between the gray armchairs on either side, facing away from the camera and blocking the round table and the white sofa behind it. The black-and-white patterned ball in front of the left side of the white sofa at the back of the room is no longer visible. The additional cushion, identical in style to the gray low cushion on the left side of the white sofa, is no longer present. The green potted plant in the left rear of the room has been moved to the right rear of the room.

Baseline: The green potted plant in the corner of the room has moved from the left side of the gray sofa to the right side. The black and white spherical ball on the floor in front of the white sofa at the back of the room is no longer present. The gray armchair on the right side of the room has turned from facing the front to facing away from the camera.

Nhãn sửa: The green potted plant moves from the back-left to the back-right of the room. A new gray armchair appears in the center with its back to the camera, while the original side armchairs remain. The patterned ball and the extra gray cushion by the sofa are no longer visible.

Bằng chứng: Both original armchairs persist; additional chair in foreground blocks table; ball/cushion absent or occluded, no forced removal.

Loại lỗi: addition_as_rotation, omission

Ảnh: images/review_16.jpg

## Cặp 33 — accept

ID: train_228879cd92821c2709ae

Caption gốc: A new blue barrier with two A-frames has been added on the road between the first and second rows of gas pumps. The new trash can to the left of the rightmost pillar in the first row of the gas station is no longer present.

Baseline: A blue barrier with two A-frames has been added to the central scene.

Nhãn sửa: A blue A-frame barrier appears in the lane between the gas pumps. The pink trash bin immediately to the left of the front-right concrete pillar disappears.

Bằng chứng: Close crop confirms pink bin is removed next to front-right pillar and blue barrier added behind.

Loại lỗi: omission

Ảnh: images/review_16.jpg

## Cặp 34 — accept

ID: train_7ec9af7809c1763d642d

Caption gốc: The yellow and white striped coffee cup in the center of the wooden table has decreased in size. The gray wheeled stool on the right side of the wooden table has been replaced by a black round stool. A glowing blue 'Office' sign has newly appeared in the lower-left area of the scene, positioned between the sofa and the wooden table. The stack of books originally at the back left of the wooden table has been moved onto the round stool on the left side.

Baseline: The round black stool on the right side of the wooden table has been replaced by a round black stool with a metal frame and a white cushion. The text "Office" in large blue letters has appeared in the lower left corner of the scene, positioned between the sofa and the wooden table.

Nhãn sửa: The striped cup on the central table becomes smaller. The wheeled chair to the right of the table is replaced by a simple black stool. A blue 'Office' sign appears near the lower left, and the stack of books moves from the back-left part of the table onto the small stool to its left.

Bằng chứng: Cup shrinks; rolling chair base gone, stool remains; visible books moved left; new sign.

Loại lỗi: wrong_replacement, omission

Ảnh: images/review_17.jpg

## Cặp 35 — accept

ID: train_dc2cc79f2f1e87b6f397

Caption gốc: The light level has dropped. Three white strip lights are hanging above the conference table, arranged from left to right on the ceiling, with the two lights on the far left and far right having disappeared.

Baseline: The light level has dropped.

Nhãn sửa: Two of the three long ceiling light panels above the conference table are removed, leaving the middle panel. The room becomes darker.

Bằng chứng: Close ceiling crop shows three illuminated panels before, one middle panel after.

Loại lỗi: omission

Ảnh: images/review_17.jpg

## Cặp 36 — accept

ID: train_7d6b0d8cf1b968764a87

Caption gốc: The word "Cannunity" has newly appeared on the ground in the center of the alleyway.A woman wearing grey overalls, a red and black vest and white gloves appears in front of the building on the left side of the picture. Her left hand is across her waist, and she is holding a white bucket in her right hand. She has her back to the picture, and is leaning sideways to the right rear of the picture, turning her head to look at the building on the left side of the picture.

Baseline: The word "annunity" has appeared on the ground in front of the central part of the alley, with glowing white text. A person wearing a red vest, gray overalls, and a black hat appears in the left wall of the alleyway, facing away from the screen and looking toward the right side of the screen, holding a bucket in their right hand.

Nhãn sửa: White 'Cannunity' lettering appears on the ground. A person in a red-and-black top and gray trousers appears near the barrels on the left, facing away from the camera and holding a white bucket.

Bằng chứng: Text includes initial Ca; person stands on ground by barrels, not inside wall; no hat identity asserted.

Loại lỗi: wrong_text, wrong_location

Ảnh: images/review_18.jpg

## Cặp 37 — accept

ID: train_c62be59de9e0b2e349bd

Caption gốc: The size of the green potted plant in the back left corner of the scene has increased. The faucet next to the sink on the wooden table in the center has shifted its orientation from facing the back of the scene to facing the left side of the scene. The high-backed white chair behind the gray sofa has disappeared. The blue kettle on the right edge of the kitchen countertop on the left side of the scene has changed color to purple.

Baseline: The blue kettle on the right side of the kitchen countertop has changed to purple. The green potted plant in the back left corner of the room has increased in size. The faucet next to the sink at the back center of the wooden table has changed from white to silver.

Nhãn sửa: The plant at the back left becomes larger. The faucet on the island turns toward the left, the tall white chair behind the gray sofa disappears, and the small blue kettle on the left kitchen counter becomes purple.

Bằng chứng: Close crop confirms faucet orientation rotates, blue kettle turns purple, plant larger, rear white chair missing.

Loại lỗi: rotation_as_material_change, omission

Ảnh: images/review_18.jpg

## Cặp 38 — accept

ID: train_ea1bd8505ce95fc29fbc

Caption gốc: A blue sign with the word "Rest" has appeared on the wall above the head of the bed. A person wearing a pink and white jumpsuit is now to the left of the bed, leaning slightly forward and facing the front of the scene. The wooden chair with a white cushion on the left side of the bed is now facing the left wooden table, changing its orientation from previously facing the right double bed. The number of white teacups on the wooden desk in the left side of the room has decreased from three to two.

Baseline: A person wearing a pink and white jumpsuit has appeared to the left of the bed, leaning forward with their back to the camera and facing the wooden desk on the left side of the room. A large light blue "Rest" sign has appeared on the wall above the headboard. The black lamp hanging above the bedside table on the left side of the bed is present.

Nhãn sửa: A person in a pink-and-white outfit appears to the left of the bed, leaning forward and facing the camera. A blue 'Rest' sign appears above the headboard. The chair at the desk turns toward the desk, and the number of white cups on the desk decreases from three to two.

Bằng chứng: Close crop confirms chair rotation and three cups reduced to two; full view confirms front-facing new person.

Loại lỗi: wrong_facing_direction, omission

Ảnh: images/review_19.jpg

## Cặp 39 — accept

ID: train_89617bcefa2bd8e527c5

Caption gốc: There were originally three red cylindrical stools on the stage; the red stool on the left has been replaced with a white cushioned chair with wooden legs, and the red stool on the far right has disappeared. A woman wearing a checkered shirt and blue pants is now seated on the stool to the left of the microphone, facing the camera. The microphone stand at the front left of the stage has changed direction, with the microphone now pointing toward the right side of the stage.

Baseline: The black music stand at the front left of the stage has been moved to the center. The red guitar at the back left of the stage has been replaced by a white chair. A woman wearing a checkered shirt and blue pants is seated on a stool to the left of the microphone, facing the camera.

Nhãn sửa: A person in a patterned top and blue trousers appears seated at the front left of the stage. Of the three red stools, the left one is replaced by a light upholstered chair and the right one disappears, leaving the middle red stool. The front-left microphone changes direction, while the guitars remain on the stage.

Bằng chứng: All three red guitars remain; central music stand stays; stool inventory changes.

Loại lỗi: wrong_replacement, hallucinated_movement, omission

Ảnh: images/review_19.jpg

## Cặp 40 — accept

ID: train_00991f51a6a25e1d6a23

Caption gốc: A person wearing a gray long-sleeve shirt, blue jeans, and gray shoes has appeared in the center of the scene, facing the stove behind the kitchen, with their head turned to the right to look at the white cabinet. The light blue sign with the text 'Scuiiery' can now be seen on the white cabinet above the dining table behind the stove. The three beverage cartons, originally in white packaging, are now obscured from view in front of the dining table. The two wooden dining stools with orange cushions, located in the front-right side of the scene, have moved under the dining table.

Baseline: A person wearing a gray long-sleeve shirt, blue jeans, and black shoes has appeared in the center of the scene, facing the stove at the back of the kitchen, with their body oriented towards the right side of the image. The white kettle on the counter to the right of the stove is no longer present. A light blue sign with the word "Scuiiery" has appeared above the white marble backsplash behind the kitchen counter.

Nhãn sửa: A person wearing a gray-green shirt, blue jeans, and a backpack appears in front of the island, facing the stove and turning their head to the right. A pale blue 'Scullery' sign appears above the stove. The two stools on the right move closer under the island, while the small cartons on the counter become obscured.

Bằng chứng: Backpack clearly visible; sign reads Scullery; person can occlude counter objects, no forced kettle removal.

Loại lỗi: hallucinated_removal, wrong_text, omission

Ảnh: images/review_20.jpg

## Cặp 41 — accept

ID: train_05303e7cae29a0713585

Caption gốc: There are two brown-yellow pendant lights above the central countertop. The front one has disappeared, and the color of the back one has changed from brown-yellow to purple. The color of the teacup in the top right corner of the central countertop has changed from purple to white. The black teacup in the top right corner of the central countertop has appeared.

Baseline: The black pendant light that was above the central counter in the room has changed color from bronze to purple. The white teacup on the second layer of the central counter is no longer present.

Nhãn sửa: Of the two bronze pendant lamps over the island, the front one disappears and the remaining one turns purple. At the back-right corner of the island, the purple cup becomes white and a black cup appears. The white cup on the middle shelf remains.

Bằng chứng: Pendant overlap reduces to one purple lamp; middle shelf cup still present, unlike baseline claim.

Loại lỗi: hallucinated_removal, omission

Ảnh: images/review_20.jpg

## Cặp 42 — accept

ID: train_fc128024ba5b82f3b7df

Caption gốc: The environment has grown dimmer. There is a newly appeared neon blue sign with the word "barn" on the left side of the building, just to the left of the garage door.

Baseline: The light level has dropped. A newly added sign with the text "barn" appears on the left side of the building, positioned above the garage door and near the streetlight. The yellow metal post located to the right of the garage door entrance, near the base of the building and adjacent to the sidewalk, has decreased in size.

Nhãn sửa: The scene becomes darker, and a blue 'barn' sign appears on the wall to the left of the garage door. The yellow bollard to the right of the door changes to a dark striped bollard of similar height.

Bằng chứng: Same approximate bollard dimensions, but yellow replaced by black/red stripes; sign left not above door.

Loại lỗi: wrong_location, color_change_as_size_change

Ảnh: images/review_21.jpg

## Cặp 43 — reject

ID: train_51b523f58086ad1aae2e

Caption gốc: A dark sofa with a curved backrest has been placed to the left of the garage door. The two yellow pillars on the left side of the house have been reduced to one.

Baseline: A dark brown sofa with a curved backrest has been newly placed on the left side of the garage door, positioned in front of the building and facing the street. The yellow metal post located to the left of the garage door entrance and near the base of the light post on the left side of the building has disappeared.

Nhãn sửa: None

Bằng chứng: Baseline semantically matches visible sofa addition and loss of one left yellow bollard despite low train-CIDEr. Not a verified model error.

Loại lỗi: 

Ảnh: images/review_21.jpg

## Cặp 44 — reject

ID: train_16452f6f159bfbc738c9

Caption gốc: A round wooden ottoman with a reddish cushion has replaced the square blue ottoman with a tray and candle, positioned in front of the sofa on the wooden platform near the center-right of the scene. The sofa with cushions on the wooden platform increases in size.

Baseline: The blue sofa cushion located on the wooden platform near the center of the scene, positioned to the right side of the seating area and in front of the wall, has increased in size. The round cushion with a red patterned top and a dark base has replaced the square ottoman with a flat surface and dark frame that was placed in front of the light blue seating area on the wooden platform.

Nhãn sửa: None

Bằng chứng: Baseline conveys sofa enlargement and ottoman replacement adequately; sofa versus sofa-cushion wording alone is not a strong confirmed error.

Loại lỗi: 

Ảnh: images/review_22.jpg

## Cặp 45 — accept

ID: train_beee64e9dae6b80f994c

Caption gốc: The light in the scene has increased. A round wooden chair located in the middle of the deck has its back turned white and its base turned green.

Baseline: The environment has become brighter. A round wooden chair with a brown padded seat and metal legs is located in the middle of the deck, and its backrest has disappeared. The white lifebuoy hanging on the front railing of the dock has been replaced by a green and white cylindrical lamp post.

Nhãn sửa: The scene becomes brighter. One chair near the center-right of the deck changes from brown to a white backrest and a green pedestal base. Both life rings remain on the railing.

Bằng chứng: Same chair silhouette with changed colors; two life rings persist, no lamp replacement.

Loại lỗi: color_change_as_removal, hallucinated_replacement

Ảnh: images/review_22.jpg

## Cặp 46 — accept

ID: train_a6cab2e7c2601fc8eb2e

Caption gốc: The size of the black exercise ball behind the treadmill and exercise bike has increased. The jump rope that was previously on the mat next to the black exercise ball has been moved to the floor on the right side of the treadmill.

Baseline: The jump rope with black handles and white ropes, previously placed on the mat to the left of the black exercise ball, has been moved to the floor next to the treadmill. The black exercise ball that was in front of the treadmill and exercise bike pair, near the center of the mat, has been moved to the right side of the mat, closer to the exercise bike.

Nhãn sửa: The black exercise ball on the mat becomes much larger. The jump rope moves off the mat onto the wooden floor near the treadmill.

Bằng chứng: Same ball on mat substantially enlarges; rope relocated to floor between mat and treadmill.

Loại lỗi: size_change_as_movement

Ảnh: images/review_23.jpg

## Cặp 47 — accept

ID: train_e8cb554167ddfb6e1ed6

Caption gốc: A woman wearing a black and white striped top and blue pants appears on a stool in the front left of the garage, she is positioned with her body facing the front right of the picture, her left leg is raised and placed on the stool, and her hands are crossed on her legs as she looks down at her palms. The hand-held lamp with a handle on the wall to the right of the door has been replaced with a dome lamp.

Baseline: A man wearing a black and white striped shirt has appeared on a stool in the front left of the garage, he is sitting on the stool with his legs crossed, looking down at his palms, which are spread open. The dome lamp on the wall to the right of the door has been replaced by a table lamp.

Nhãn sửa: A person in a black-and-white striped top and blue trousers appears seated near the left side of the garage entrance, with one knee raised while looking down at their hands. The lamp on the right entrance pillar changes from a slender handled light to a larger covered lantern.

Bằng chứng: New seated person visible; lamp changes from narrow upright fixture to broad covered lantern, not reverse.

Loại lỗi: wrong_replacement_direction, wrong_posture

Ảnh: images/review_23.jpg
