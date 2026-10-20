# Đặc tả Use Case — Công cụ "Chat với tài liệu" (MVP)

> **Chuẩn:** UML 2.0 (sơ đồ) · Mẫu đặc tả use case dạng văn bản · Truy vết IEEE 29148
> **Sơ đồ:** [UseCase_ChatVoiTaiLieu.drawio](UseCase_ChatVoiTaiLieu.drawio) v0.2
> **Đầu vào:** [PRD.md](PRD.md) v0.4 · [BRD.md](BRD.md) v0.4
> ⚠️ **Tài liệu bài tập.** Mọi số liệu đánh dấu **[GĐ]** là giả định bài tập, kế thừa từ BRD §12 và PRD §8.

---

## 1. Thông tin tài liệu

| Thuộc tính | Giá trị |
|---|---|
| Số hiệu | UCS-CWD-001 |
| Phiên bản | 0.2 |
| Ngày cập nhật | 2026-10-21 |
| Trạng thái | **Draft** |
| Tác giả | Business Analyst (bản nháp do Claude soạn hỗ trợ) |
| Người review | Product Owner, Trưởng nhóm BD, QA Lead, Trưởng phòng CNTT |
| Người phê duyệt | Product Owner |

### Lịch sử phiên bản

| Phiên bản | Ngày | Tác giả | Thay đổi |
|---|---|---|---|
| 0.1 | 2026-10-21 | BA | Bản đầu tiên. Đặc tả 20 use case theo sơ đồ v0.2. Sơ đồ v0.2 đã sửa so với v0.1: UC-03 đổi từ «include» sang «extend»; include UC-09 chuyển từ UC-07 sang UC-08; UC-04 gộp vào UC-01; thêm điều kiện extend và extension points |
| 0.2 | 2026-10-21 | BA | Đóng OI-01..05 bằng giả định [GĐ]. Cập nhật UC-01 (E5), UC-02 (vai trò Quản lý bộ tài liệu), UC-09 (E1 chính thức), UC-19 (gán vai trò), UC-20 và UC-21 (BRU-007, xuất CSV), §3, §7, §8 |

---

## 2. Quy ước

- **"Hệ thống"** là công cụ Chat với tài liệu, tức mọi thứ nằm trong khung hệ thống của sơ đồ.
- **Luồng** được viết theo mẫu *"Số bước. Ai làm gì."*. Luồng thay thế (`A`) và luồng ngoại lệ (`E`) luôn ghi rõ bước mà chúng rẽ nhánh, theo mẫu *"A1 (từ bước 3)"*.
- **Mức use case:** *Mục tiêu người dùng* là việc tác nhân muốn hoàn thành. *Chức năng con* là phần được include hoặc extend, không có tác nhân chính khởi tạo trực tiếp.
- **Không mô tả giao diện.** Tài liệu này nói hệ thống làm gì, không nói màn hình trông ra sao hay người dùng bấm nút nào. Chi tiết giao diện nằm ở PRD §4 (UI-001 đến UI-010).
- Các mã `E-xx` trong ngoặc tham chiếu bảng trường hợp biên ở PRD §4.2.

---

## 3. Tác nhân

| Tác nhân | Loại | Mô tả | Kế thừa | Nguồn |
|---|---|---|---|---|
| *Người dùng* {abstract} | Chính | Bất kỳ ai đăng nhập vào hệ thống | — | — |
| Thành viên BD (P-01) | Chính | Chuyên viên Phát triển kinh doanh; tải tài liệu lên và hỏi đáp | Người dùng | STK-002 |
| Trưởng nhóm BD (P-02) | Chính | Chủ sở hữu nghiệp vụ; có vai trò **Quản lý bộ tài liệu** (do CNTT gán), là người duy nhất được tải lô (UC-02) [GĐ: OI-03] | Thành viên BD | STK-002 |
| Quản trị viên CNTT (P-03) | Chính | Quản lý nhóm truy cập và vai trò, gỡ tài liệu, tra và xuất nhật ký; chỉ thấy **thông tin mô tả** tài liệu, không xem hay truy vấn được nội dung (BRU-007) | Người dùng | STK-004 |
| Dịch vụ AI «system» | Phụ | Tạo nội dung câu trả lời từ câu hỏi và các đoạn tài liệu liên quan; phải đáp ứng BRU-005 | — | IF-01 |
| Microsoft 365 «system» | Phụ | Xác thực tài khoản công ty | — | IF-02 |

---

## 4. Danh mục use case

| ID | Tên | Tác nhân chính | Mức | Ưu tiên | Quan hệ | Nguồn |
|---|---|---|---|---|---|---|
| UC-01 | Tải tài liệu PDF lên | Thành viên BD | Mục tiêu người dùng | P0 | Được mở rộng bởi UC-03, UC-05; được kế thừa bởi UC-02 | US-001, BR-001 |
| UC-02 | Tải lô tài liệu dự án | Trưởng nhóm BD | Mục tiêu người dùng | P0 | Kế thừa UC-01 | US-002, BR-002 |
| UC-03 | Xác nhận phân loại tài liệu | (qua UC-01) | Chức năng con | P0 | «extend» UC-01 | AC-US001-4, BRU-001 |
| UC-04 | *Withdrawn: gộp vào UC-01 bước 4 (v0.2)* | — | — | — | — | — |
| UC-05 | Thông báo file bị từ chối | (qua UC-01) | Chức năng con | P1 | «extend» UC-01 | US-004, BR-004 |
| UC-06 | Xem danh sách và trạng thái tài liệu | Thành viên BD | Mục tiêu người dùng | P1 | — | US-003, US-005, BR-003 |
| UC-07 | Đặt câu hỏi về tài liệu | Thành viên BD | Mục tiêu người dùng | P0 | «include» UC-08; được mở rộng bởi UC-10, UC-11, UC-12 | US-006, BR-005, BR-012 |
| UC-08 | Tạo câu trả lời có căn cứ | (qua UC-07); Dịch vụ AI | Chức năng con | P0 | «include» UC-09 | US-007, US-008, BR-006, BR-007 |
| UC-09 | Trích dẫn nguồn | (qua UC-08) | Chức năng con | P0 | — | US-009, BR-008 |
| UC-10 | Báo không tìm thấy thông tin | (qua UC-07) | Chức năng con | P0 | «extend» UC-07 | US-010, BR-009 |
| UC-11 | Đặt câu hỏi tiếp nối | (qua UC-07) | Chức năng con | P1 | «extend» UC-07 | US-011, BR-010 |
| UC-12 | Dừng câu trả lời | (qua UC-07) | Chức năng con | P1 | «extend» UC-07 | US-017 |
| UC-13 | Xem đoạn văn nguồn | Thành viên BD | Mục tiêu người dùng | P0 | Được mở rộng bởi UC-14 | US-009 (AC-US009-2), BR-008 |
| UC-14 | Mở PDF gốc tại trang trích dẫn | (qua UC-13) | Chức năng con | P2 | «extend» UC-13 | US-019 |
| UC-15 | Sao chép câu trả lời kèm nguồn | Thành viên BD | Mục tiêu người dùng | P1 | — | US-018 |
| UC-16 | Bắt đầu hội thoại mới | Thành viên BD | Mục tiêu người dùng | P2 | — | US-016 |
| UC-17 | Đánh giá câu trả lời | Thành viên BD | Mục tiêu người dùng | P1 | — | US-015, BR-014 |
| UC-18 | Đăng nhập | Người dùng; Microsoft 365 | Mục tiêu người dùng | P0 | — | US-012, BR-013, BR-015 |
| UC-19 | Quản lý nhóm truy cập | Quản trị viên CNTT | Mục tiêu người dùng | P0 | — | US-013, US-014, NFR-011 |
| UC-20 | Gỡ tài liệu | Quản trị viên CNTT | Mục tiêu người dùng | P0 | — | US-020, BR-017 |
| UC-21 | Tra cứu nhật ký truy cập | Quản trị viên CNTT | Mục tiêu người dùng | P0 | — | NFR-010, BR-016 |

---

## 5. Tiền điều kiện chung, quy tắc và yêu cầu dùng chung

**Tiền điều kiện chung** (áp dụng cho mọi use case trừ UC-18):
- **GP-1:** Người dùng đã đăng nhập (UC-18) và phiên còn hiệu lực (NFR-009: hết hạn sau 8 giờ không hoạt động).
- **GP-2:** Với use case của Thành viên BD: người dùng thuộc nhóm truy cập của bộ tài liệu (BR-013, BR-015). Với use case của Quản trị viên: người dùng có vai trò quản trị.
- **GP-3:** Thiết bị truy cập từ mạng nội bộ hoặc VPN công ty (CON-007).

**Yêu cầu dùng chung:**
- **NFR-010:** mọi thao tác tải lên, xác nhận phân loại, xem, truy vấn, gỡ tài liệu, đổi quyền đều được ghi nhật ký truy cập, không chứa nội dung (BRU-004).
- **G-13:** không ghi nội dung câu hỏi, câu trả lời, tài liệu vào analytics hay log ứng dụng.
- **COM-01:** mọi giao tiếp được mã hóa (TLS 1.2 trở lên).

---

## 6. Đặc tả chi tiết

### UC-01 Tải tài liệu PDF lên

| Mục | Nội dung |
|---|---|
| Mô tả | Thành viên BD đưa một file PDF vào bộ tài liệu dự án, để có thể đặt câu hỏi về nội dung file đó. |
| Tác nhân chính / phụ | Thành viên BD / — |
| Trigger | Thành viên BD yêu cầu tải lên một file PDF. |
| Tiền điều kiện | GP-1..3. Bộ tài liệu có ít hơn 50 file. |
| Hậu điều kiện (thành công) | Tài liệu có trong bộ tài liệu với trạng thái "Sẵn sàng" và truy vấn được qua UC-07. Có bản ghi nhật ký tải lên. |
| Hậu điều kiện (thất bại) | Bộ tài liệu không thay đổi; không có bản ghi tài liệu dở dang. Người dùng biết lý do thất bại. |
| Extension points | **tải lần đầu trong phiên** (bước 2); **file không hợp lệ** (bước 4) |

**Luồng chính**
1. Thành viên BD yêu cầu tải lên một tài liệu.
2. Hệ thống kiểm tra đây có phải lần tải lên đầu tiên trong phiên đăng nhập không. Nếu đúng, thực hiện UC-03 tại extension point *tải lần đầu trong phiên*.
3. Thành viên BD chọn một file.
4. Hệ thống kiểm tra file: là PDF, ≤ 200 trang, ≤ 20 MB, và bộ tài liệu chưa đủ 50 file.
5. Hệ thống tiếp nhận file và báo trạng thái "Đang xử lý".
6. Hệ thống trích xuất nội dung văn bản và chuẩn bị tài liệu để truy vấn, đồng thời cập nhật tiến trình xử lý.
7. Hệ thống chuyển trạng thái tài liệu sang "Sẵn sàng" và ghi nhật ký tải lên.
8. Use case kết thúc thành công.

**Luồng thay thế**
- **A1 (từ bước 4):** Đã có file trùng tên trong bộ tài liệu. Hệ thống lưu file mới với tên `ten (2).pdf` và thông báo cho người dùng (E-09). Tiếp tục bước 5.
- **A2 (từ bước 6):** Người dùng đặt câu hỏi trong khi tài liệu chưa "Sẵn sàng". UC-07 trả lời từ các tài liệu đã sẵn sàng, kèm ghi chú nêu tên tài liệu chưa được dùng (AC-US001-3). Bước 6 vẫn tiếp tục.

**Luồng ngoại lệ**
- **E1 (từ bước 2):** Người dùng không xác nhận phân loại ở UC-03. Hệ thống không cho tải lên; use case kết thúc thất bại.
- **E2 (từ bước 4):** File không đạt điều kiện. Thực hiện UC-05 tại extension point *file không hợp lệ*; use case kết thúc thất bại (E-03, E-07, E-08).
- **E3 (từ bước 5):** Mất kết nối khi đang gửi file. Hệ thống tự thử lại tối đa 3 lần. Nếu vẫn lỗi, hệ thống báo người dùng thử lại và không tạo bản ghi tài liệu (E-10).
- **E4 (từ bước 6):** File hỏng, có mật khẩu, hoặc là bản scan không có lớp văn bản. Hệ thống chuyển trạng thái sang "Lỗi" kèm lý do và không dùng file để trả lời (E-04, E-05, E-06).
- **E5 (từ bước 3):** Người dùng không có vai trò Quản lý bộ tài liệu nhưng chọn nhiều file cùng lúc. Hệ thống không tiếp nhận lô và hướng dẫn tải từng file (AC-US002-4) [GĐ: OI-03].

| Mục | Nội dung |
|---|---|
| Quy tắc nghiệp vụ | BRU-001 (chỉ tài liệu Công khai/Nội bộ); BR-002 (≤ 50 file/bộ, ≤ 200 trang, ≤ 20 MB/file); BRU-002 (thời gian lưu tài liệu); CON-004 (chỉ PDF dạng văn bản) |
| Yêu cầu phi chức năng | NFR-003 (≤ 2 phút cho 50 trang; ≤ 8 phút cho 200 trang); COM-03 (chịu gián đoạn mạng ngắn); NFR-010 |
| Dữ liệu | **Vào:** file PDF. **Ghi nhận:** mã tài liệu, tên file, số trang, dung lượng, người tải lên, thời điểm tải lên, trạng thái, lý do lỗi (nếu có), bộ tài liệu |
| Giả định | ASM-001 (≥ 90% PDF có văn bản trích xuất được) |
| Truy vết | US-001, AC-US001-1..4, BR-001, AC-001, E-03..E-10 |

---

### UC-02 Tải lô tài liệu dự án

| Mục | Nội dung |
|---|---|
| Mô tả | Trưởng nhóm BD tải nhiều file PDF lên cùng lúc, để chuẩn bị toàn bộ bộ tài liệu dự án trong một lần. Đây là trường hợp đặc biệt của UC-01 (quan hệ kế thừa). |
| Tác nhân chính / phụ | Trưởng nhóm BD / — |
| Trigger | Trưởng nhóm BD chọn nhiều file để tải lên cùng lúc. |
| Tiền điều kiện | Như UC-01. Người dùng có vai trò **Quản lý bộ tài liệu** của bộ tài liệu này (gán qua UC-19) [GĐ: OI-03]. |
| Hậu điều kiện (thành công) | Mọi file hợp lệ ở trạng thái "Sẵn sàng". Tổng số file trong bộ ≤ 50. |
| Hậu điều kiện (thất bại) | Các file không hợp lệ không có trong bộ tài liệu. Các file hợp lệ vẫn được tiếp nhận. |

**Luồng chính**
1. Trưởng nhóm BD yêu cầu tải lên nhiều tài liệu.
2. Hệ thống thực hiện bước 2 của UC-01 (xác nhận phân loại nếu là lần đầu trong phiên).
3. Trưởng nhóm BD chọn N file.
4. Hệ thống kiểm tra từng file theo bước 4 của UC-01, và kiểm tra tổng số file sau khi tải không vượt 50.
5. Hệ thống tiếp nhận các file hợp lệ; mỗi file có trạng thái riêng.
6. Hệ thống xử lý từng file theo bước 6–7 của UC-01.
7. Hệ thống báo tổng kết: số file "Sẵn sàng" và số file "Lỗi".
8. Use case kết thúc thành công.

**Luồng ngoại lệ**
- **E1 (từ bước 4):** Một số file không hợp lệ. Hệ thống thực hiện UC-05 cho từng file đó; các file còn lại tiếp tục bước 5 (AC-US002-2).
- **E2 (từ bước 4):** Tổng số file vượt 50. Hệ thống tiếp nhận đến khi đủ 50 file và từ chối phần dư (E-08).
- **E3, E4:** như E3, E4 của UC-01, áp dụng riêng cho từng file.

| Mục | Nội dung |
|---|---|
| Quy tắc nghiệp vụ | Như UC-01 |
| Yêu cầu phi chức năng | NFR-003, NFR-007 (≤ 10.000 trang/bộ) |
| Dữ liệu | Như UC-01, cho từng file; thêm số file hợp lệ/lỗi trong lô |
| Truy vết | US-002, AC-US002-1..4, BR-002, AC-002 |

---

### UC-03 Xác nhận phân loại tài liệu

| Mục | Nội dung |
|---|---|
| Mô tả | Người tải lên cam kết tài liệu không thuộc loại "Mật" hay "Tuyệt mật" trước lần tải lên đầu tiên trong phiên. |
| Tác nhân chính / phụ | Thành viên BD (qua UC-01) / — |
| Quan hệ | «extend» UC-01 tại *tải lần đầu trong phiên* — điều kiện: [lần tải lên đầu tiên trong phiên] |
| Trigger | UC-01 bước 2 xác định đây là lần tải lên đầu tiên trong phiên. |
| Tiền điều kiện | Chưa có lượt xác nhận nào trong phiên hiện tại. |
| Hậu điều kiện (thành công) | Lượt xác nhận được ghi nhật ký; hệ thống không yêu cầu xác nhận lại trong phiên này. |
| Hậu điều kiện (thất bại) | Không có tài liệu nào được tải lên; không ghi lượt xác nhận. |

**Luồng chính**
1. Hệ thống yêu cầu người dùng xác nhận: "Tài liệu thuộc loại Công khai hoặc Nội bộ, không phải Mật/Tuyệt mật".
2. Người dùng xác nhận.
3. Hệ thống ghi lượt xác nhận (người dùng, thời điểm, phiên) vào nhật ký truy cập.
4. Quay lại UC-01 bước 3.

**Luồng ngoại lệ**
- **E1 (từ bước 2):** Người dùng không xác nhận. Hệ thống không cho tải lên; UC-01 kết thúc theo E1.

| Mục | Nội dung |
|---|---|
| Quy tắc nghiệp vụ | BRU-001 |
| Dữ liệu | Người dùng, thời điểm, mã phiên |
| Truy vết | AC-US001-4, UI-010, BRU-001 |

---

### UC-04 *(Withdrawn)*

Đã gộp vào **UC-01 bước 4** từ sơ đồ v0.2, vì đây là chức năng kiểm tra nội bộ, không phải mục tiêu của tác nhân. ID được giữ lại và không dùng cho use case khác.

---

### UC-05 Thông báo file bị từ chối

| Mục | Nội dung |
|---|---|
| Mô tả | Báo cho người tải lên biết một file không được tiếp nhận và vì sao, để họ không nhầm là tài liệu đã có trong bộ. |
| Tác nhân chính / phụ | Thành viên BD hoặc Trưởng nhóm BD (qua UC-01, UC-02) / — |
| Quan hệ | «extend» UC-01 tại *file không hợp lệ* — điều kiện: [file không hợp lệ] |
| Trigger | UC-01 bước 4 phát hiện file không đạt điều kiện. |
| Tiền điều kiện | — |
| Hậu điều kiện (thành công) | Người dùng biết tên file và lý do bị từ chối; file không có trong bộ tài liệu. |
| Hậu điều kiện (thất bại) | Không áp dụng. |

**Luồng chính**
1. Hệ thống xác định lý do từ chối: không phải PDF; quá 200 trang; quá 20 MB; hoặc bộ tài liệu đã đủ 50 file.
2. Hệ thống thông báo cho người tải lên tên file và lý do.
3. Hệ thống không thêm file vào bộ tài liệu và ghi sự kiện từ chối (EVT-002).

| Mục | Nội dung |
|---|---|
| Quy tắc nghiệp vụ | BR-002, CON-004 |
| Dữ liệu | Tên file, lý do (not_pdf / too_large / too_many_pages / limit_reached) |
| Truy vết | US-004, AC-US004-1, BR-004, AC-004, E-03, E-07, E-08 |

---

### UC-06 Xem danh sách và trạng thái tài liệu

| Mục | Nội dung |
|---|---|
| Mô tả | Thành viên BD xem bộ tài liệu đang có và trạng thái của từng tài liệu, để biết câu trả lời được tổng hợp từ những tài liệu nào và khi nào có thể hỏi. |
| Tác nhân chính / phụ | Thành viên BD / — |
| Trigger | Thành viên BD mở bộ tài liệu. |
| Tiền điều kiện | GP-1..3. |
| Hậu điều kiện (thành công) | Người dùng thấy danh sách hiện tại; danh sách được cập nhật khi có thay đổi. |
| Hậu điều kiện (thất bại) | Người dùng không thấy tên hay thông tin nào của tài liệu. |

**Luồng chính**
1. Thành viên BD yêu cầu xem bộ tài liệu.
2. Hệ thống kiểm tra quyền xem (BR-013).
3. Hệ thống trả về danh sách tài liệu, mới nhất trước. Mỗi tài liệu gồm tên, số trang, trạng thái, phần trăm tiến trình (nếu đang xử lý) và lý do lỗi (nếu có).
4. Hệ thống cập nhật trạng thái và tiến trình ít nhất mỗi 5 giây. Thay đổi do người khác tạo ra (tải lên, gỡ) được cập nhật trong ≤ 10 giây.
5. Use case kết thúc khi người dùng rời bộ tài liệu.

**Luồng thay thế**
- **A1 (từ bước 3):** Bộ tài liệu chưa có tài liệu nào. Hệ thống thông báo và hướng dẫn tải lên (UC-01); không cho đặt câu hỏi (E-01).

**Luồng ngoại lệ**
- **E1 (từ bước 2):** Không có quyền xem. Hệ thống từ chối và không tiết lộ tên tài liệu (E-19).

| Mục | Nội dung |
|---|---|
| Yêu cầu phi chức năng | COM-02 (đẩy cập nhật không cần tải lại trang); E-20 (≤ 10 giây) |
| Dữ liệu | Tên file, số trang, trạng thái, % tiến trình, thời điểm tải lên, lý do lỗi |
| Truy vết | US-003, US-005, AC-US003-1, AC-US005-1, BR-003, AC-003 |

---

### UC-07 Đặt câu hỏi về tài liệu

| Mục | Nội dung |
|---|---|
| Mô tả | Thành viên BD đặt một câu hỏi bằng ngôn ngữ tự nhiên và nhận câu trả lời chỉ dựa trên các tài liệu dự án đã tải lên, kèm nguồn. |
| Tác nhân chính / phụ | Thành viên BD / Dịch vụ AI (qua UC-08) |
| Trigger | Thành viên BD gửi một câu hỏi. |
| Tiền điều kiện | GP-1..3. Bộ tài liệu có ít nhất 1 tài liệu "Sẵn sàng". |
| Hậu điều kiện (thành công) | Người dùng nhận được câu trả lời có nội dung kèm trích dẫn, hoặc thông báo "không tìm thấy". Lượt hỏi đáp được lưu trong hội thoại hiện tại (tối đa 30 ngày, BRU-003). Sự kiện EVT-006, EVT-007 được ghi. |
| Hậu điều kiện (thất bại) | Câu hỏi được giữ lại để gửi lại. Không có câu trả lời dở dang nào được lưu như câu trả lời hoàn chỉnh. EVT-008 được ghi. |
| Extension points | **có hội thoại trước** (bước 1); **không có thông tin** (bước 4); **yêu cầu dừng** (bước 5) |

**Luồng chính**
1. Thành viên BD nhập câu hỏi bằng tiếng Việt hoặc tiếng Anh và gửi đi. Nếu hội thoại hiện tại đã có lượt trước, thực hiện UC-11 tại extension point *có hội thoại trước*.
2. Hệ thống kiểm tra câu hỏi không rỗng và không quá 2.000 ký tự.
3. Hệ thống kiểm tra quyền truy vấn (BR-015) và giới hạn 30 câu hỏi/người/giờ.
4. Hệ thống thực hiện UC-08 để tạo câu trả lời từ các tài liệu "Sẵn sàng". Nếu UC-08 xác định tài liệu không chứa thông tin, thực hiện UC-10 tại extension point *không có thông tin*.
5. Hệ thống chuyển câu trả lời tới người dùng theo từng phần ngay khi nội dung được tạo. Nếu người dùng yêu cầu dừng, thực hiện UC-12 tại extension point *yêu cầu dừng*.
6. Hệ thống hoàn tất câu trả lời kèm trích dẫn nguồn (đã tạo ở UC-09).
7. Hệ thống lưu lượt hỏi đáp vào hội thoại hiện tại và ghi sự kiện.
8. Use case kết thúc thành công.

**Luồng thay thế**
- **A1 (từ bước 4):** Có tài liệu đang xử lý. Câu trả lời kèm ghi chú nêu tên tài liệu chưa được dùng (AC-US001-3).
- **A2 (từ bước 4):** Câu hỏi có nhiều đáp án hợp lệ (SC-05). Hệ thống liệt kê các đáp án kèm đối tượng và nguồn của từng đáp án, hoặc hỏi lại để làm rõ (E-17).
- **A3 (từ bước 4):** Các tài liệu nêu thông tin mâu thuẫn nhau. Câu trả lời nêu tất cả các giá trị kèm nguồn của từng giá trị, không tự chọn một (AC-US008-2).

**Luồng ngoại lệ**
- **E1 (từ bước 1):** Không có tài liệu nào "Sẵn sàng". Hệ thống không cho gửi câu hỏi (E-01, E-02).
- **E2 (từ bước 2):** Câu hỏi rỗng hoặc quá 2.000 ký tự. Hệ thống không gửi và báo lý do (E-14, E-15).
- **E3 (từ bước 3):** Không có quyền truy vấn. Hệ thống từ chối, không trả nội dung tài liệu (E-19).
- **E4 (từ bước 3):** Vượt 30 câu/giờ hoặc chi phí AI tháng đã đạt 100% ngân sách. Hệ thống tạm chặn và báo thời điểm được hỏi lại (E-13).
- **E5 (từ bước 4):** Dịch vụ AI lỗi hoặc không phản hồi sau 60 giây. Hệ thống báo bận và giữ câu hỏi để gửi lại (E-12).
- **E6 (từ bước 5):** Mất kết nối khi đang nhận câu trả lời. Hệ thống giữ phần đã nhận, đánh dấu "chưa hoàn tất" và cho phép tạo lại (E-11).
- **E7 (từ bước 1 đến bước 3):** Phiên đăng nhập hết hạn. Hệ thống giữ câu hỏi và yêu cầu đăng nhập lại (UC-18, E-18).

| Mục | Nội dung |
|---|---|
| Quy tắc nghiệp vụ | BR-006 (chỉ dùng tài liệu đã tải lên); BRU-006 (câu trả lời chỉ mang tính tham khảo, phải đối chiếu nguồn trước khi gửi đối tác); G-16 (30 câu/người/giờ; trần chi phí 5 triệu VND/tháng) [GĐ] |
| Yêu cầu phi chức năng | NFR-001 (p90 ≤ 5 giây tới nội dung đầu tiên); NFR-002 (p90 ≤ 20 giây hoàn tất); NFR-004 (Việt/Anh); NFR-005 (10 người đồng thời); NFR-006 (20 câu/phút) |
| Dữ liệu | **Vào:** nội dung câu hỏi (≤ 2.000 ký tự). **Ghi nhận:** mã hội thoại, thứ tự lượt, ngôn ngữ (vi/en), thời điểm, câu trả lời, loại câu trả lời (answered / not_found / clarification), trạng thái (hoàn tất / đã dừng / chưa hoàn tất), danh sách trích dẫn |
| Giả định | ASM-002 (có dịch vụ AI đáp ứng BRU-005) |
| Truy vết | US-006, AC-US006-1..3, BR-005, BR-012, AC-005, AC-012 |

---

### UC-08 Tạo câu trả lời có căn cứ

| Mục | Nội dung |
|---|---|
| Mô tả | Hệ thống tìm các đoạn văn liên quan trong tài liệu, rồi dùng Dịch vụ AI để tạo câu trả lời **chỉ** từ các đoạn văn đó. |
| Tác nhân chính / phụ | (qua UC-07) / Dịch vụ AI |
| Quan hệ | Được include bởi UC-07; «include» UC-09 |
| Trigger | UC-07 bước 4. |
| Tiền điều kiện | Câu hỏi hợp lệ; người dùng có quyền truy vấn bộ tài liệu. |
| Hậu điều kiện (thành công) | Có câu trả lời có nội dung kèm trích dẫn; hoặc kết quả "không có thông tin" được trả về UC-07. |
| Hậu điều kiện (thất bại) | Trả lỗi về UC-07 (E5 của UC-07); không có dữ liệu nào được Dịch vụ AI lưu lại (BRU-005). |

**Luồng chính**
1. Hệ thống tìm các đoạn văn liên quan đến câu hỏi trong các tài liệu "Sẵn sàng" của bộ tài liệu người dùng có quyền. Nếu là câu hỏi tiếp nối, ngữ cảnh do UC-11 cung cấp được dùng khi tìm.
2. Hệ thống gửi câu hỏi, các đoạn văn liên quan và ngữ cảnh hội thoại tới Dịch vụ AI, kèm yêu cầu chỉ trả lời từ các đoạn văn đó.
3. Dịch vụ AI trả về nội dung câu trả lời.
4. Hệ thống thực hiện UC-09 để gắn trích dẫn nguồn.
5. Hệ thống trả câu trả lời về UC-07.

**Luồng thay thế**
- **A1 (từ bước 1):** Thông tin liên quan nằm ở nhiều tài liệu. Hệ thống gửi đoạn văn từ tất cả các tài liệu đó, để câu trả lời tổng hợp đủ thông tin (BR-007).
- **A2 (từ bước 1 hoặc bước 3):** Không tìm thấy đoạn văn liên quan, hoặc Dịch vụ AI xác định các đoạn văn không chứa câu trả lời. UC-08 trả kết quả "không có thông tin" về UC-07 và bỏ qua bước 4. UC-07 thực hiện UC-10.

**Luồng ngoại lệ**
- **E1 (từ bước 2):** Dịch vụ AI lỗi hoặc không phản hồi sau 60 giây. Trả lỗi về UC-07.

| Mục | Nội dung |
|---|---|
| Quy tắc nghiệp vụ | BR-006; BR-015 (chỉ bộ tài liệu có quyền); BRU-005 (dịch vụ AI không huấn luyện trên dữ liệu, không lưu sau xử lý, vùng dữ liệu được duyệt) |
| Yêu cầu phi chức năng | NFR-001, NFR-002; COM-01; G-13 |
| Dữ liệu | **Gửi Dịch vụ AI:** câu hỏi, các đoạn văn (mã tài liệu, số trang, nội dung), ngữ cảnh hội thoại. **Nhận:** nội dung câu trả lời |
| Truy vết | US-007, US-008, AC-US007-1..2, AC-US008-1..2, BR-006, BR-007, AC-006, AC-007, IF-01 |

---

### UC-09 Trích dẫn nguồn

| Mục | Nội dung |
|---|---|
| Mô tả | Gắn tên tài liệu và số trang cho thông tin trong câu trả lời, để người dùng kiểm chứng được. |
| Tác nhân chính / phụ | (qua UC-08) / — |
| Quan hệ | Được include bởi UC-08 (luồng chính) |
| Trigger | UC-08 bước 4. |
| Tiền điều kiện | Có câu trả lời có nội dung. |
| Hậu điều kiện (thành công) | Câu trả lời có ít nhất 1 trích dẫn (tên file, số trang) và danh sách nguồn. |
| Hậu điều kiện (thất bại) | Xem E1. |

**Luồng chính**
1. Với mỗi thông tin trong câu trả lời, hệ thống xác định tài liệu và số trang nguồn từ các đoạn văn đã dùng.
2. Hệ thống gắn chỉ số trích dẫn vào thông tin tương ứng và lập danh sách nguồn (tên file, số trang) ở cuối câu trả lời.
3. Quay lại UC-08 bước 5.

**Luồng ngoại lệ**
- **E1 (từ bước 1):** Không xác định được nguồn cho một thông tin. Hệ thống loại thông tin đó khỏi câu trả lời (AC-US009-4) [GĐ: OI-02].
- **E2 (từ bước 1):** Mọi thông tin đều bị loại theo E1. UC-08 trả kết quả "không có thông tin" về UC-07, và UC-07 thực hiện UC-10.

| Mục | Nội dung |
|---|---|
| Quy tắc nghiệp vụ | BR-008 (Must: mọi câu trả lời có nội dung phải nêu tên tài liệu và số trang); BRU-006 |
| Dữ liệu | Mỗi trích dẫn: chỉ số, mã tài liệu, tên file, số trang, đoạn văn nguồn (≤ 300 ký tự, dùng cho UC-13) |
| Truy vết | US-009, AC-US009-1, AC-US009-3, AC-US009-4, BR-008, AC-008, G-09 |

---

### UC-10 Báo không tìm thấy thông tin

| Mục | Nội dung |
|---|---|
| Mô tả | Khi tài liệu không chứa thông tin được hỏi, hệ thống nói rõ là không tìm thấy, thay vì đưa ra câu trả lời suy đoán. |
| Tác nhân chính / phụ | (qua UC-07) / — |
| Quan hệ | «extend» UC-07 tại *không có thông tin* — điều kiện: [không có thông tin] |
| Trigger | UC-08 trả kết quả "không có thông tin". |
| Tiền điều kiện | — |
| Hậu điều kiện (thành công) | Người dùng nhận thông báo kèm gợi ý; lượt hỏi đáp được lưu với loại `not_found`. Use case UC-07 kết thúc. |
| Hậu điều kiện (thất bại) | Không áp dụng. |

**Luồng chính**
1. Hệ thống thông báo: "Không tìm thấy thông tin này trong các tài liệu đã tải lên."
2. Hệ thống gợi ý diễn đạt lại câu hỏi, hoặc kiểm tra tài liệu liên quan đã được tải lên chưa.
3. Hệ thống lưu lượt hỏi đáp với loại `not_found` (UC-07 bước 7); UC-07 kết thúc.

| Mục | Nội dung |
|---|---|
| Quy tắc nghiệp vụ | BR-009 |
| Yêu cầu phi chức năng | G-08 (≥ 90% câu hỏi loại SC-03 nhận thông báo này) [GĐ] |
| Truy vết | US-010, AC-US010-1..2, BR-009, AC-009, E-16 |

---

### UC-11 Đặt câu hỏi tiếp nối

| Mục | Nội dung |
|---|---|
| Mô tả | Thành viên BD hỏi tiếp mà không phải nhắc lại ngữ cảnh; hệ thống hiểu đối tượng đang được nói tới. |
| Tác nhân chính / phụ | Thành viên BD (qua UC-07) / — |
| Quan hệ | «extend» UC-07 tại *có hội thoại trước* — điều kiện: [có hội thoại trước đó] |
| Trigger | Câu hỏi được gửi trong một hội thoại đã có ít nhất 1 lượt. |
| Tiền điều kiện | Hội thoại hiện tại có ít nhất 1 lượt hỏi đáp. |
| Hậu điều kiện (thành công) | Câu hỏi được hiểu đúng đối tượng tham chiếu. |
| Hậu điều kiện (thất bại) | Không áp dụng. Nếu không xác định được đối tượng, áp dụng A2 của UC-07 (hỏi lại để làm rõ). |

**Luồng chính**
1. Hệ thống lấy ngữ cảnh các lượt trước trong hội thoại hiện tại.
2. Hệ thống dùng ngữ cảnh đó để xác định đối tượng được tham chiếu trong câu hỏi.
3. Hệ thống chuyển ngữ cảnh cho UC-08; quay lại UC-07 bước 2.

| Mục | Nội dung |
|---|---|
| Quy tắc nghiệp vụ | BR-010; chỉ dùng ngữ cảnh của hội thoại hiện tại (US-016) |
| Yêu cầu phi chức năng | ≥ 4/5 câu hỏi loại SC-04 được hiểu đúng (AC-010) [GĐ] |
| Dữ liệu | Mã hội thoại, các lượt trước |
| Truy vết | US-011, AC-US011-1..2, BR-010, AC-010 |

---

### UC-12 Dừng câu trả lời

| Mục | Nội dung |
|---|---|
| Mô tả | Thành viên BD dừng một câu trả lời đang được tạo, khi nhận ra mình hỏi sai hoặc đã đủ thông tin. |
| Tác nhân chính / phụ | Thành viên BD (qua UC-07) / — |
| Quan hệ | «extend» UC-07 tại *yêu cầu dừng* — điều kiện: [người dùng yêu cầu dừng] |
| Trigger | Thành viên BD yêu cầu dừng trong lúc câu trả lời đang được tạo. |
| Tiền điều kiện | Có câu trả lời đang được tạo (UC-07 bước 5). |
| Hậu điều kiện (thành công) | Câu trả lời ngừng trong ≤ 1 giây; phần đã nhận được giữ lại và đánh dấu "đã dừng"; người dùng có thể hỏi câu mới. |
| Hậu điều kiện (thất bại) | Không áp dụng. |

**Luồng chính**
1. Thành viên BD yêu cầu dừng câu trả lời.
2. Hệ thống ngừng nhận nội dung từ Dịch vụ AI trong ≤ 1 giây.
3. Hệ thống giữ phần đã nhận và đánh dấu "đã dừng".
4. Hệ thống ghi EVT-015, lưu lượt hỏi đáp với trạng thái "đã dừng"; UC-07 kết thúc.

| Mục | Nội dung |
|---|---|
| Truy vết | US-017, AC-US017-1 |

---

### UC-13 Xem đoạn văn nguồn

| Mục | Nội dung |
|---|---|
| Mô tả | Thành viên BD xem đoạn văn gốc mà một trích dẫn trỏ tới, để kiểm chứng câu trả lời trước khi dùng. |
| Tác nhân chính / phụ | Thành viên BD / — |
| Trigger | Thành viên BD chọn một trích dẫn trong câu trả lời. |
| Tiền điều kiện | GP-1..3. Có câu trả lời kèm trích dẫn. |
| Hậu điều kiện (thành công) | Người dùng thấy đoạn văn nguồn kèm tên file và số trang. EVT-010 được ghi. |
| Hậu điều kiện (thất bại) | Người dùng được báo lý do; không có nội dung nào bị lộ. |
| Extension points | **mở tài liệu gốc** (bước 3) |

**Luồng chính**
1. Thành viên BD chọn một trích dẫn.
2. Hệ thống kiểm tra quyền xem bộ tài liệu (BR-013).
3. Hệ thống trả về đoạn văn nguồn (tối đa 300 ký tự), tên file và số trang. Nếu người dùng chọn mở tài liệu gốc, thực hiện UC-14 tại extension point *mở tài liệu gốc*.
4. Hệ thống ghi EVT-010; use case kết thúc.

**Luồng ngoại lệ**
- **E1 (từ bước 2):** Không có quyền xem. Hệ thống từ chối (E-19).
- **E2 (từ bước 3):** Tài liệu đã bị gỡ (UC-20). Hệ thống báo "Tài liệu đã được gỡ" và không trả nội dung (E-22).

| Mục | Nội dung |
|---|---|
| Quy tắc nghiệp vụ | BR-013, BRU-006 |
| Dữ liệu | Mã trích dẫn → mã tài liệu, tên file, số trang, đoạn văn (≤ 300 ký tự) |
| Truy vết | US-009 (AC-US009-2), BR-008, UI-004 |

---

### UC-14 Mở PDF gốc tại trang trích dẫn

| Mục | Nội dung |
|---|---|
| Mô tả | Thành viên BD mở file PDF gốc tại đúng trang được trích dẫn, để đọc ngữ cảnh xung quanh. |
| Tác nhân chính / phụ | Thành viên BD (qua UC-13) / — |
| Quan hệ | «extend» UC-13 tại *mở tài liệu gốc* — điều kiện: [người dùng chọn mở tài liệu gốc] |
| Trigger | Thành viên BD chọn mở tài liệu gốc từ đoạn văn nguồn. |
| Tiền điều kiện | Đang xem đoạn văn nguồn (UC-13 bước 3). |
| Hậu điều kiện (thành công) | File gốc được cung cấp và mở tại đúng trang N. EVT-010 được ghi với `target = original`. |
| Hậu điều kiện (thất bại) | Không cung cấp file. |

**Luồng chính**
1. Thành viên BD chọn mở tài liệu gốc.
2. Hệ thống kiểm tra lại quyền xem (BR-013).
3. Hệ thống cung cấp file gốc, mở tại trang được trích dẫn.

**Luồng ngoại lệ**
- **E1 (từ bước 2):** Không có quyền, hoặc tài liệu đã bị gỡ. Hệ thống từ chối (E-19, E-22).

| Mục | Nội dung |
|---|---|
| Truy vết | US-019, AC-US019-1 |

---

### UC-15 Sao chép câu trả lời kèm nguồn

| Mục | Nội dung |
|---|---|
| Mô tả | Thành viên BD lấy câu trả lời kèm danh sách nguồn để dùng trong email hoặc tài liệu gửi đối tác. |
| Tác nhân chính / phụ | Thành viên BD / — |
| Trigger | Thành viên BD yêu cầu sao chép một câu trả lời. |
| Tiền điều kiện | GP-1..3. Câu trả lời đã hoàn tất. |
| Hậu điều kiện (thành công) | Bộ nhớ tạm của người dùng chứa nội dung câu trả lời và danh sách nguồn (tên file, số trang) ở dạng văn bản thuần. EVT-012 được ghi. |
| Hậu điều kiện (thất bại) | Bộ nhớ tạm không thay đổi; người dùng được báo. |

**Luồng chính**
1. Thành viên BD yêu cầu sao chép một câu trả lời.
2. Hệ thống đưa nội dung câu trả lời và danh sách nguồn vào bộ nhớ tạm của người dùng.
3. Hệ thống xác nhận đã sao chép và ghi EVT-012.

| Mục | Nội dung |
|---|---|
| Quy tắc nghiệp vụ | BRU-006: thông tin gửi đối tác phải được đối chiếu với nguồn trước khi gửi |
| Truy vết | US-018, AC-US018-1 |

---

### UC-16 Bắt đầu hội thoại mới

| Mục | Nội dung |
|---|---|
| Mô tả | Thành viên BD mở một hội thoại mới, để câu hỏi về chủ đề khác không bị lẫn ngữ cảnh cũ. |
| Tác nhân chính / phụ | Thành viên BD / — |
| Trigger | Thành viên BD yêu cầu bắt đầu hội thoại mới. |
| Tiền điều kiện | GP-1..3. |
| Hậu điều kiện (thành công) | Có hội thoại mới không có ngữ cảnh; hội thoại cũ vẫn được lưu theo BRU-003; bộ tài liệu không thay đổi. EVT-005 được ghi. |
| Hậu điều kiện (thất bại) | Không áp dụng. |

**Luồng chính**
1. Thành viên BD yêu cầu bắt đầu hội thoại mới.
2. Hệ thống đóng hội thoại hiện tại.
3. Hệ thống tạo hội thoại mới, không mang ngữ cảnh của hội thoại cũ.
4. Hệ thống ghi EVT-005.

| Mục | Nội dung |
|---|---|
| Quy tắc nghiệp vụ | BRU-003 (lịch sử hội thoại lưu tối đa 30 ngày) |
| Truy vết | US-016, AC-US016-1 |

---

### UC-17 Đánh giá câu trả lời

| Mục | Nội dung |
|---|---|
| Mô tả | Thành viên BD đánh giá một câu trả lời là hữu ích hay không, để nhóm sản phẩm theo dõi chất lượng. |
| Tác nhân chính / phụ | Thành viên BD / — |
| Trigger | Thành viên BD chọn đánh giá cho một câu trả lời. |
| Tiền điều kiện | GP-1..3. Câu trả lời đã hoàn tất. |
| Hậu điều kiện (thành công) | Mỗi người có đúng một đánh giá cho mỗi câu trả lời. EVT-009 được ghi. |
| Hậu điều kiện (thất bại) | Đánh giá cũ (nếu có) được giữ nguyên. |

**Luồng chính**
1. Thành viên BD chọn đánh giá tiêu cực.
2. Hệ thống yêu cầu chọn lý do: Sai / Thiếu / Nguồn sai / Khác.
3. Thành viên BD chọn lý do.
4. Hệ thống ghi đánh giá và EVT-009.

**Luồng thay thế**
- **A1 (từ bước 1):** Thành viên BD chọn đánh giá tích cực. Bỏ qua bước 2–3; tiếp tục bước 4.
- **A2 (từ bước 1):** Người dùng đã đánh giá câu trả lời này trước đó. Hệ thống thay đánh giá cũ bằng đánh giá mới (AC-US015-2).

| Mục | Nội dung |
|---|---|
| Yêu cầu phi chức năng | KR3.2 (≥ 70% đánh giá tích cực) [GĐ] |
| Dữ liệu | Mã câu trả lời, người dùng (ẩn danh trong analytics), đánh giá (tích cực/tiêu cực), lý do, loại câu trả lời |
| Truy vết | US-015, AC-US015-1..2, BR-014, MET-002 |

---

### UC-18 Đăng nhập

| Mục | Nội dung |
|---|---|
| Mô tả | Người dùng xác thực bằng tài khoản công ty để được dùng công cụ với đúng vai trò và đúng bộ tài liệu. |
| Tác nhân chính / phụ | Người dùng (Thành viên BD, Trưởng nhóm BD, Quản trị viên CNTT) / Microsoft 365 |
| Trigger | Người dùng truy cập công cụ khi chưa có phiên hợp lệ, hoặc khi phiên đã hết hạn. |
| Tiền điều kiện | GP-3. Người dùng có tài khoản Microsoft 365 công ty. |
| Hậu điều kiện (thành công) | Có phiên hợp lệ (hết hạn sau 8 giờ không hoạt động). Vai trò và danh sách bộ tài liệu được phép đã được xác định. EVT-014 được ghi. |
| Hậu điều kiện (thất bại) | Không tạo phiên; không có dữ liệu tài liệu nào được trả về. |

**Luồng chính**
1. Người dùng truy cập công cụ.
2. Hệ thống chuyển yêu cầu xác thực tới Microsoft 365.
3. Người dùng xác thực bằng tài khoản công ty.
4. Microsoft 365 trả về định danh người dùng và các nhóm của người đó.
5. Hệ thống tạo phiên, xác định vai trò (Thành viên BD hoặc Quản trị viên) và các bộ tài liệu được phép.
6. Hệ thống ghi EVT-014 và nhật ký truy cập.

**Luồng ngoại lệ**
- **E1 (từ bước 1):** Truy cập từ ngoài mạng nội bộ hoặc VPN. Không truy cập được (E-21).
- **E2 (từ bước 3):** Xác thực thất bại. Hệ thống không tạo phiên.
- **E3 (từ bước 5):** Người dùng không thuộc nhóm truy cập nào và không có vai trò quản trị. Hệ thống báo không có quyền và không hiển thị bộ tài liệu nào (E-19).
- **E4 (sau bước 6, khi đang dùng):** Phiên hết hạn. Hệ thống giữ thao tác đang dở (ví dụ câu hỏi đang nhập) và quay lại bước 2 (E-18).

| Mục | Nội dung |
|---|---|
| Quy tắc nghiệp vụ | BR-013, BR-015; CON-007 |
| Yêu cầu phi chức năng | NFR-009 (8 giờ); COM-01, COM-04 |
| Dữ liệu | Định danh người dùng, nhóm, vai trò, mã phiên, thời điểm đăng nhập, thời điểm hết hạn |
| Truy vết | US-012, AC-US012-1..2, IF-02 |

---

### UC-19 Quản lý nhóm truy cập

| Mục | Nội dung |
|---|---|
| Mô tả | Quản trị viên CNTT thêm hoặc gỡ người dùng khỏi nhóm truy cập của một bộ tài liệu, và gán hoặc bỏ vai trò Quản lý bộ tài liệu, để chỉ đúng người xem, hỏi và tải lô được tài liệu. |
| Tác nhân chính / phụ | Quản trị viên CNTT / Microsoft 365 (tra cứu tài khoản) |
| Trigger | Quản trị viên nhận yêu cầu thêm hoặc gỡ thành viên (thường từ Trưởng nhóm BD, hoặc khi nhân sự nghỉ việc). |
| Tiền điều kiện | GP-1, GP-3. Người dùng có vai trò quản trị. |
| Hậu điều kiện (thành công) | Nhóm truy cập được cập nhật. Quyền bị gỡ hết hiệu lực trong ≤ 15 phút. Thay đổi được ghi nhật ký. |
| Hậu điều kiện (thất bại) | Nhóm truy cập không thay đổi. |

**Luồng chính**
1. Quản trị viên chọn bộ tài liệu.
2. Hệ thống trả về danh sách thành viên của nhóm truy cập.
3. Quản trị viên thêm hoặc gỡ một tài khoản, hoặc gán hoặc bỏ vai trò Quản lý bộ tài liệu cho một thành viên.
4. Hệ thống áp dụng thay đổi. Quyền bị gỡ hết hiệu lực trong ≤ 15 phút, kể cả với phiên đang mở.
5. Hệ thống ghi thay đổi vào nhật ký truy cập.

**Luồng ngoại lệ**
- **E1 (từ bước 3):** Tài khoản không tồn tại trong Microsoft 365. Hệ thống từ chối thêm và báo lý do.

| Mục | Nội dung |
|---|---|
| Quy tắc nghiệp vụ | BRU-007 / PCON-03: quản trị viên chỉ thấy thông tin mô tả, không xem hay truy vấn được nội dung tài liệu; muốn xem phải được thêm vào nhóm như một Thành viên BD. MVP chỉ gán vai trò Quản lý bộ tài liệu cho Trưởng nhóm BD [GĐ: OI-03] |
| Yêu cầu phi chức năng | NFR-011 (≤ 15 phút); NFR-010 |
| Dữ liệu | Bộ tài liệu, tài khoản, thao tác (thêm / gỡ / gán vai trò / bỏ vai trò), người thực hiện, thời điểm |
| Truy vết | US-013, US-014, AC-US014-2, BR-013, BR-015 |

---

### UC-20 Gỡ tài liệu

| Mục | Nội dung |
|---|---|
| Mô tả | Quản trị viên CNTT gỡ hoàn toàn một tài liệu khỏi công cụ theo yêu cầu, ví dụ khi tài liệu "Mật" bị tải lên nhầm hoặc đối tác yêu cầu. |
| Tác nhân chính / phụ | Quản trị viên CNTT / — |
| Trigger | Quản trị viên nhận yêu cầu gỡ từ Trưởng nhóm BD hoặc Pháp chế. Yêu cầu được gửi qua kênh nội bộ ngoài hệ thống. |
| Tiền điều kiện | GP-1, GP-3. Tài liệu tồn tại trong bộ tài liệu. |
| Hậu điều kiện (thành công) | File gốc và toàn bộ dữ liệu đã xử lý bị xóa. Tài liệu biến mất khỏi danh sách của mọi người dùng trong ≤ 10 giây. Câu hỏi về nội dung tài liệu đó nhận được "không tìm thấy". Thao tác được ghi nhật ký. |
| Hậu điều kiện (thất bại) | Tài liệu giữ nguyên; quản trị viên được báo lỗi để thử lại trong hạn 1 ngày làm việc. |

**Luồng chính**
1. Quản trị viên tìm tài liệu theo tên trong bộ tài liệu. Hệ thống chỉ trả thông tin mô tả (tên file, số trang, dung lượng, người tải lên, thời điểm, trạng thái), không trả nội dung (BRU-007).
2. Quản trị viên yêu cầu gỡ, ghi lý do và người yêu cầu.
3. Hệ thống yêu cầu xác nhận, vì thao tác không hoàn tác được.
4. Quản trị viên xác nhận.
5. Hệ thống xóa file gốc và toàn bộ dữ liệu đã xử lý của tài liệu.
6. Hệ thống cập nhật danh sách của mọi người dùng đang mở bộ tài liệu.
7. Hệ thống ghi nhật ký truy cập và EVT-016.

**Luồng thay thế**
- **A1 (từ bước 4):** Quản trị viên hủy. Không có gì thay đổi; use case kết thúc.

**Luồng ngoại lệ**
- **E1 (từ bước 5):** Tài liệu đang được trích dẫn trong các câu trả lời đã có. Các câu trả lời giữ nguyên; trích dẫn tới tài liệu này hiển thị "Tài liệu đã được gỡ" (E-22).

| Mục | Nội dung |
|---|---|
| Quy tắc nghiệp vụ | BR-017 (hoàn tất trong ≤ 1 ngày làm việc kể từ khi nhận yêu cầu); BRU-001; BRU-002; BRU-007 (chỉ thông tin mô tả) |
| Dữ liệu | Mã tài liệu, tên file, lý do gỡ, người yêu cầu, người thực hiện, thời điểm yêu cầu, thời điểm hoàn tất |
| Truy vết | US-020, AC-US020-1..2, AC-US013-2, BR-017, AC-017, G-18 |

---

### UC-21 Tra cứu nhật ký truy cập

| Mục | Nội dung |
|---|---|
| Mô tả | Quản trị viên CNTT tra xem ai đã xem, truy vấn hay thay đổi một bộ tài liệu trong một khoảng thời gian, để chứng minh tuân thủ NDA và quy định bảo vệ dữ liệu khi được yêu cầu. |
| Tác nhân chính / phụ | Quản trị viên CNTT / — |
| Trigger | Pháp chế yêu cầu kiểm tra tuân thủ, hoặc CNTT điều tra một sự cố. |
| Tiền điều kiện | GP-1, GP-3. Người dùng có vai trò quản trị. |
| Hậu điều kiện (thành công) | Quản trị viên nhận được danh sách bản ghi khớp điều kiện lọc. |
| Hậu điều kiện (thất bại) | Không trả dữ liệu; báo lý do. |

**Luồng chính**
1. Quản trị viên chọn bộ tài liệu và khoảng thời gian trong 12 tháng gần nhất.
2. Hệ thống trả về các bản ghi gồm: người dùng, thời điểm, thao tác (tải lên, xác nhận phân loại, xem, truy vấn, gỡ tài liệu, đổi quyền) và tài liệu liên quan (nếu có).
3. Quản trị viên lọc thêm theo người dùng hoặc loại thao tác.
4. Hệ thống trả kết quả đã lọc.

**Luồng thay thế**
- **A1 (từ bước 1):** Khoảng thời gian vượt quá 12 tháng. Hệ thống chỉ trả dữ liệu còn được lưu và báo giới hạn (BRU-004).
- **A2 (từ bước 4):** Quản trị viên yêu cầu xuất kết quả. Hệ thống tạo file CSV chứa đúng các bản ghi đã lọc, không chứa nội dung tài liệu hay câu hỏi, và ghi lượt xuất (người xuất, thời điểm, điều kiện lọc) vào nhật ký. *(P1)* [GĐ: OI-04]

| Mục | Nội dung |
|---|---|
| Quy tắc nghiệp vụ | BRU-004 (lưu 12 tháng; không chứa nội dung tài liệu hay câu hỏi); CON-006 |
| Yêu cầu phi chức năng | NFR-010 |
| Dữ liệu | **Vào:** bộ tài liệu, từ ngày, đến ngày, (tùy chọn) người dùng, loại thao tác. **Ra:** người dùng, thời điểm, thao tác, mã/tên tài liệu; file CSV cùng các cột (A2) |
| Truy vết | BR-016, AC-016, NFR-010 |

---

## 7. Từ điển dữ liệu

| Thực thể | Trường | Ghi chú |
|---|---|---|
| Bộ tài liệu | mã, tên, nhóm truy cập | MVP có 1 bộ: Dự án X |
| Tài liệu | mã, tên file, số trang, dung lượng, trạng thái (Đang tải / Đang xử lý / Sẵn sàng / Lỗi), % tiến trình, lý do lỗi, người tải lên, thời điểm tải lên, mã bộ tài liệu | ≤ 200 trang, ≤ 20 MB; ≤ 50 tài liệu/bộ |
| Hội thoại | mã, người dùng, thời điểm tạo, danh sách lượt | Lưu tối đa 30 ngày (BRU-003) |
| Lượt hỏi đáp | thứ tự, câu hỏi (≤ 2.000 ký tự), ngôn ngữ (vi/en), câu trả lời, loại (answered / not_found / clarification), trạng thái (hoàn tất / đã dừng / chưa hoàn tất), danh sách trích dẫn, thời điểm | |
| Trích dẫn | chỉ số, mã tài liệu, tên file, số trang, đoạn văn nguồn (≤ 300 ký tự) | |
| Đánh giá | mã câu trả lời, người dùng, tích cực/tiêu cực, lý do | Mỗi người 1 đánh giá cho mỗi câu trả lời |
| Bản ghi nhật ký | người dùng, thời điểm, thao tác, mã bộ tài liệu, mã tài liệu (nếu có) | **Không** chứa nội dung; lưu 12 tháng (BRU-004) |
| Phiên | định danh người dùng, vai trò (Thành viên BD / Quản lý bộ tài liệu / Quản trị viên), các bộ tài liệu được phép, thời điểm hết hạn | Hết hạn sau 8 giờ không hoạt động |

---

## 8. Giả định

| ID | Giả định | Ảnh hưởng tới | Nguồn |
|---|---|---|---|
| ASM-001 | ≥ 90% PDF của Dự án X có văn bản trích xuất được | UC-01, UC-02 | BRD §10 |
| ASM-002 | Có dịch vụ AI đáp ứng BRU-005, trong ngân sách | UC-07, UC-08 | BRD §10 |
| ASM-006 | Hồ sơ người dùng đúng như BRD §6.3 | Toàn bộ | BRD §10 |
| ASM-007 | 5 loại kịch bản SC-01..05 đại diện cho câu hỏi thực tế | UC-07 đến UC-12 | BRD §10 |
| UCA-01 | Yêu cầu gỡ tài liệu (UC-20) và thêm/gỡ thành viên (UC-19) được gửi tới CNTT qua kênh nội bộ có sẵn (email, phiếu yêu cầu), không nằm trong công cụ | UC-19, UC-20 | Tài liệu này |
| UCA-02 | Mọi Thành viên BD tải lên được từng file (UC-01). Chỉ người có vai trò Quản lý bộ tài liệu (MVP: Trưởng nhóm BD) được tải lô (UC-02). Lựa chọn an toàn nhằm giảm rủi ro tải nhầm hàng loạt tài liệu "Mật" | UC-01, UC-02, UC-19 | [GĐ: OI-03] |

Mọi số liệu đánh dấu [GĐ] là giả định bài tập (BRD §12).

---

## 9. Vấn đề mở

Mọi vấn đề đã được đóng bằng **giả định bài tập** ngày 2026-10-21, theo hướng an toàn.

| ID | Vấn đề | Ảnh hưởng | Người chịu trách nhiệm | Trạng thái | Quyết định [GĐ] và nơi cập nhật |
|---|---|---|---|---|---|
| OI-01 | BR-013 cấm Quản trị viên "xem" tài liệu (gồm cả tên file), nhưng UC-20 cần thấy tên file để gỡ | UC-20, UC-21, BR-013 | Product Owner + Trưởng phòng CNTT | Resolved | Quản trị viên chỉ thấy thông tin mô tả (tên file, số trang, dung lượng, người tải lên, thời điểm, trạng thái), không xem hay truy vấn được nội dung. Đã cập nhật: BRD v0.4 (BR-013, AC-013, BRU-007 mới); PRD v0.4 (bảng quyền §5.1 D, AC-US013-2, PCON-03) |
| OI-02 | Thông tin không xác định được nguồn có bị loại khỏi câu trả lời không? | UC-09, BR-008 | Product Owner | Resolved | Có. Nếu loại hết thì trả "không tìm thấy". Đã cập nhật: PRD AC-US009-4; UC-09 E1, E2 |
| OI-03 | Tải lô (UC-02) chỉ dành cho Trưởng nhóm BD hay cho mọi thành viên? | UC-01, UC-02, UC-19 | Trưởng nhóm BD | Resolved | Chỉ người có vai trò Quản lý bộ tài liệu (MVP: Trưởng nhóm BD), do CNTT gán qua UC-19, để giảm rủi ro tải nhầm hàng loạt. Đã cập nhật: PRD bảng quyền, AC-US002-4; UC-01 E5, UC-02, UC-19; UCA-02 |
| OI-04 | Có cần xuất kết quả tra cứu nhật ký (UC-21) ra file không? | UC-21 | Pháp chế | Resolved | Có, xuất CSV (P1); chỉ Quản trị viên được xuất; mỗi lần xuất được ghi nhật ký; file không chứa nội dung. Đã cập nhật: PRD NFR-010; UC-21 A2 |
| OI-05 | Cột Test case trong PRD §7 chưa có | Toàn bộ | QA Lead | Resolved (đã giao việc) | QA lập test case từ luồng chính, luồng thay thế và luồng ngoại lệ của tài liệu này, mã `TC-UCxx-yy`, trước 2026-11-30, rồi điền vào PRD §7 |

---

## 10. Phê duyệt

| Vai trò | Họ tên | Quyết định | Ngày |
|---|---|---|---|
| Product Owner | [GĐ] Product Manager | [Phê duyệt / Từ chối] | |
| Trưởng nhóm BD | [GĐ] | [Phê duyệt / Từ chối] | |
| QA Lead | [GĐ] | [Phê duyệt / Từ chối] | |
