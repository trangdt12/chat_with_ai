import { useEffect, useRef, useState } from "react";
import { useActiveDocSet } from "../auth/useMe";
import { AppHeader } from "../components/AppHeader";
import { BatchResultPanel } from "../components/BatchResultPanel";
import { ChatThread } from "../components/ChatThread";
import { Composer } from "../components/Composer";
import { DocumentSidebar } from "../components/DocumentSidebar";
import { EmptyState } from "../components/EmptyState";
import { Icon } from "../components/Icon";
import { useToast } from "../components/Toasts";
import { useDocuments } from "../hooks/useDocuments";
import { useUpload } from "../hooks/useUpload";
import { useChat } from "../state/chat";

export function ChatPage() {
  const docSet = useActiveDocSet()!; // RequireAuth(area="chat") bảo đảm có ít nhất 1 bộ tài liệu
  return <ChatWorkspace key={docSet.id} docSetId={docSet.id} docSetName={docSet.name} canBatch={docSet.role === "manager"} />;
}

function ChatWorkspace({ docSetId, docSetName, canBatch }: { docSetId: string; docSetName: string; canBatch: boolean }) {
  const toast = useToast();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const { documents, readyCount, processingCount, isPending } = useDocuments(docSetId);
  const upload = useUpload(docSetId, { canBatch, existingCount: documents.length });
  const chat = useChat(docSetId);
  const scroll = useRef<HTMLDivElement>(null);

  // Tự cuộn xuống khi có nội dung mới.
  useEffect(() => {
    const el = scroll.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [chat.turns]);

  async function newConversation() {
    try {
      await chat.newConversation();
    } catch {
      toast("Không tạo được hội thoại mới. Hãy thử lại.", "danger");
    }
  }

  const hasDocuments = documents.length > 0 || upload.busy;
  let intro = null;
  if (chat.turns.length === 0 && !isPending) {
    if (!hasDocuments) {
      intro = <EmptyState kind="empty" processingCount={0} canBatch={canBatch} onFiles={upload.start} />;
    } else if (readyCount === 0) {
      intro = <EmptyState kind="processing" processingCount={processingCount} canBatch={canBatch} onFiles={upload.start} />;
    } else if (processingCount > 0) {
      intro = (
        <div className="chat-inner">
          <div className="banner banner-info">
            <Icon name="info" />
            <div>
              <strong className="banner-title">Bạn vẫn hỏi được trong lúc tài liệu đang xử lý</strong>
              Câu trả lời sẽ chỉ dùng các tài liệu “Sẵn sàng” và ghi chú tên các tài liệu chưa được dùng.
            </div>
          </div>
        </div>
      );
    }
  }

  return (
    <div className="app">
      <a className="skip-link" href="#main">
        Bỏ qua tới nội dung chính
      </a>
      <AppHeader
        docSetName={`Bộ tài liệu: ${docSetName}`}
        leading={
          <button
            className="btn btn-ghost btn-icon drawer-toggle"
            type="button"
            aria-label={drawerOpen ? "Đóng danh sách tài liệu" : "Mở danh sách tài liệu"}
            aria-expanded={drawerOpen}
            aria-controls="docs-panel"
            onClick={() => setDrawerOpen((o) => !o)}
          >
            <Icon name="menu" />
          </button>
        }
      />
      <div className="workspace">
        <DocumentSidebar
          documents={documents}
          loading={isPending}
          uploading={upload.uploading}
          canBatch={canBatch}
          onFiles={upload.start}
          onNewConversation={newConversation}
          newConversationDisabled={chat.turns.length === 0}
          open={drawerOpen}
        />
        <main className="chat" id="main" aria-label="Hội thoại">
          <div className="chat-scroll" ref={scroll}>
            {upload.batch && (
              <div style={{ marginBottom: "var(--sp-6)" }}>
                <BatchResultPanel batch={upload.batch} documents={documents} onClose={upload.closeBatch} />
              </div>
            )}
            {intro}
            {chat.turns.length > 0 && (
              <ChatThread
                turns={chat.turns}
                onRegenerate={chat.send}
                onFeedback={chat.setFeedback}
                onCitationRemoved={chat.markCitationRemoved}
              />
            )}
          </div>
          <Composer
            streaming={chat.streaming}
            readyCount={readyCount}
            hasDocuments={hasDocuments}
            onSend={chat.send}
            onStop={chat.stop}
          />
        </main>
      </div>
      {upload.dialog}
    </div>
  );
}
