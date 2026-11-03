# Kiểm tra thời gian lúc20:30,không thay cấu hình model

User yêu cầu kiểm tra20:30–21:00ngày03/11vàchophépnớideadline trướckhichấm nếu dựbáokhôngkịp,nhưng tổngchi phí continuation vẫn<=11USD. Đã tạo heartbeatmộtlần20:30Asia/Bangkok trong chat hiện tại,id`ki-m-tra-mbr-l-c-20-30`. Máy/app cần mởđể thực hiện tácvụlocal;Modaljob đang chạy độc lập.

Snapshot18:54có52cặp mới;log18:58có67cặp,interpairRealmean12,16giây,recent20mean15,52giây. Đây là Real551trởđi,không nhấtthiết cólatencygiống550cặpđầu;chưa cóRender đểđo. Không lấy8%wordlengthlàmquyluật8%latency. Chưa nới deadline,chưa chấm điểm.

Đến20:30đọc actualprogress,recordtimings,sessioncount vàbillingreport theoapp. Dựbáo bằng cảthroughputmỗi miền/đoạngầnnhất vàđuôi caption. Nếu kịp thìgiữnguyên. Nếu không,khóa revision/budget trước khiápdụng vàtrước bấtkỳ scorefullnào. 12600giây chỉ làgợiý,không phải mặcđịnh: cần cộngCPU/RAM,CPUscore/controller,startup/overlap vàchi phíđãtiêu;11USDlàtrầntổngmọiphiêncontinuation.

Timerworker,childenvdeadline vàcontrollerhiệntạiđềufixedkhi khởichạy. SửaSTATEtrênVolumeđơnthuần không kéo dài tiến trình live. Nếu phảihandoff,giữmọipairđãcommit,dừngGPU/controllercũ cókiểmsoát,xácminhGPUcũđãdừng rồi chạyphiênmới vớiimmutableprefix,sameseed/config/selector vàglobalbudgetstartbanđầu. Khôngreset11USD/khôngtạo11USDmới. Ghiactualsessionmapping,giữnguyên550rawcũ. Nếu không chứng minhđược nằmtrongtrần thìdừng đúnggiớihạn.

Nếu đãcomplete,tải vàcommitmetric/perpair/selection/CI/sessionanalysis/rawfull,billing vàbằngchứngGPUoff. Nếupartial/error,ghisốcặp vàkhônggọilàbenchmarkfull. BảngEARLY_THROUGHPUTchỉdùngtiming,khôngdùngCIDEr.
