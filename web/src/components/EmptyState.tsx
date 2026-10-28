import { Icon } from "./Icon";
import { UploadDropzone } from "./UploadDropzone";

/** Màn 02: chưa có tài liệu (E-01) hoặc mọi tài liệu đang xử lý (E-02). */
export function EmptyState({
  kind,
  processingCount,
  canBatch,
  onFiles,
}: {
  kind: "empty" | "processing";
  processingCount: number;
  canBatch: boolean;
  onFiles: (files: File[]) => void;
}) {
  if (kind === "processing") {
    return (
      <section className="empty" aria-labelledby="proc-title">
        <div className="empty-illus">
          <Icon name="file" />
        </div>
        <h1 id="proc-title">Đang xử lý {processingCount} tài liệu</h1>
        <p className="muted">
          Bạn có thể hỏi ngay khi ít nhất một tài liệu ở trạng thái “Sẵn sàng”. Danh sách bên trái tự cập nhật, không
          cần tải lại trang.
        </p>
      </section>
    );
  }
  return (
    <section className="empty" aria-labelledby="empty-title">
      <div className="empty-illus">
        <Icon name="message" />
      </div>
      <h1 id="empty-title">Tải lên tài liệu PDF đầu tiên để bắt đầu hỏi đáp</h1>
      <p className="muted">
        Sau khi tài liệu được xử lý, bạn có thể hỏi bằng tiếng Việt hoặc tiếng Anh và nhận câu trả lời kèm tên tài liệu,
        số trang nguồn.
      </p>
      <ol className="steps">
        <li>
          <span className="step-no">1</span>
          <div>
            <strong>Tải tài liệu lên</strong>
            <p className="muted small">
              Kéo thả file PDF vào khu vực bên trái. Chỉ tải tài liệu loại Công khai hoặc Nội bộ.
            </p>
          </div>
        </li>
        <li>
          <span className="step-no">2</span>
          <div>
            <strong>Chờ xử lý xong</strong>
            <p className="muted small">Tài liệu chuyển sang trạng thái “Sẵn sàng”, thường dưới 2 phút cho 50 trang.</p>
          </div>
        </li>
        <li>
          <span className="step-no">3</span>
          <div>
            <strong>Đặt câu hỏi</strong>
            <p className="muted small">Ví dụ: “Thời hạn thanh toán trong hợp đồng khung là bao lâu?”</p>
          </div>
        </li>
      </ol>
      <UploadDropzone canBatch={canBatch} onFiles={onFiles} large />
    </section>
  );
}
