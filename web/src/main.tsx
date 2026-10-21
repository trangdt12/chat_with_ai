import React, { useEffect, useState } from "react";
import ReactDOM from "react-dom/client";
import "./styles/tokens.css";
import "./styles/components.css";

// Khung tạm của T-01: kiểm tra proxy /api. T-04 thay bằng App có router.
function Health() {
  const [status, setStatus] = useState("đang kiểm tra…");
  useEffect(() => {
    fetch("/api/v1/health")
      .then((r) => r.json())
      .then((b) => setStatus(b.status))
      .catch(() => setStatus("không kết nối được API"));
  }, []);
  return (
    <main className="empty">
      <h1>Chat với tài liệu</h1>
      <p className="muted">API: {status}</p>
    </main>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <Health />
  </React.StrictMode>,
);
