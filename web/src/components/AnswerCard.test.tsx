import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { CitationRef, Turn } from "../api/types";
import { LAN, jsonResponse, mockFetch, renderWithProviders } from "../test/utils";
import { AnswerCard } from "./AnswerCard";

const cite: CitationRef = { idx: 1, citation_id: "c1", document_id: "d1", filename: "HopDongKhung.pdf", page: 14 };

function turn(over: Partial<Turn>): Turn {
  return {
    key: "t1",
    question: "Thời hạn thanh toán?",
    messageId: "m1",
    spans: [{ text: "Thời hạn thanh toán là **30 ngày**.", citations: [cite] }],
    status: "completed",
    answerType: "answered",
    citations: [cite],
    pendingDocuments: [],
    failCode: null,
    feedback: null,
    ...over,
  };
}

function renderCard(t: Turn, onRegenerate = vi.fn()) {
  renderWithProviders(
    <AnswerCard turn={t} index={0} onRegenerate={onRegenerate} onFeedback={vi.fn()} onCitationRemoved={vi.fn()} />,
    { me: LAN },
  );
  return { onRegenerate };
}

afterEach(() => vi.unstubAllGlobals());

describe("AnswerCard", () => {
  it("answered: nội dung, [1], nguồn, sao chép, đánh giá", () => {
    renderCard(turn({}));
    expect(screen.getByText("30 ngày").tagName).toBe("STRONG");
    expect(screen.getByRole("button", { name: "Nguồn 1: HopDongKhung.pdf trang 14" })).toHaveTextContent("1");
    expect(screen.getByText("HopDongKhung.pdf · trang 14")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Sao chép kèm nguồn/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Câu trả lời hữu ích" })).toBeInTheDocument();
  });

  it("not_found: thông điệp + 2 gợi ý, không có nút sao chép", () => {
    renderCard(turn({ answerType: "not_found", spans: [], citations: [] }));
    expect(screen.getByText("Không tìm thấy thông tin này trong các tài liệu đã tải lên.")).toBeInTheDocument();
    expect(screen.getAllByRole("listitem")).toHaveLength(2);
    expect(screen.queryByRole("button", { name: /Sao chép/ })).not.toBeInTheDocument();
  });

  it("pending_documents → ghi chú tài liệu chưa dùng", () => {
    renderCard(turn({ pendingDocuments: [{ id: "x", filename: "BaoGia_v3.pdf" }] }));
    expect(screen.getByText(/chưa được dùng để trả lời vì đang xử lý/)).toBeInTheDocument();
    expect(screen.getByText("BaoGia_v3.pdf")).toBeInTheDocument();
  });

  it("stopped: giữ nội dung + nhãn đã dừng, không có đánh giá", () => {
    renderCard(turn({ status: "stopped", answerType: null }));
    expect(screen.getByText(/Đã dừng theo yêu cầu của bạn/)).toBeInTheDocument();
    expect(screen.getByText(/Thời hạn thanh toán là/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Câu trả lời hữu ích" })).not.toBeInTheDocument();
  });

  it("failed: nhãn gián đoạn + Tạo lại, không có sao chép", async () => {
    const { onRegenerate } = renderCard(turn({ status: "failed", answerType: null, failCode: "AI_UNAVAILABLE" }));
    expect(screen.getByText("Câu trả lời bị gián đoạn — chưa hoàn tất")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Sao chép/ })).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /Tạo lại câu trả lời/ }));
    expect(onRegenerate).toHaveBeenCalledWith("Thời hạn thanh toán?");
  });

  it("nội dung <script>/<img onerror> hiển thị dạng chữ", () => {
    renderCard(turn({ spans: [{ text: 'Xem <script>alert(1)</script> <img src=x onerror="alert(2)">', citations: [cite] }] }));
    expect(document.querySelector("script")).toBeNull();
    expect(document.querySelector("img")).toBeNull();
    expect(screen.getByText(/<script>/)).toBeInTheDocument();
  });

  it("bấm [1] mở popover có đoạn trích; Esc đóng và trả focus", async () => {
    mockFetch({
      "GET /citations/c1": () =>
        jsonResponse({ document_id: "d1", filename: "HopDongKhung.pdf", page: 14, snippet: "Thanh toán trong 30 ngày" }),
    });
    renderCard(turn({}));
    const btn = screen.getByRole("button", { name: "Nguồn 1: HopDongKhung.pdf trang 14" });
    await userEvent.click(btn);
    expect(await screen.findByText("“Thanh toán trong 30 ngày”")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Mở tài liệu gốc tại trang 14/ })).toBeInTheDocument();
    await userEvent.keyboard("{Escape}");
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(btn).toHaveFocus();
  });

  it("trích dẫn tới tài liệu đã gỡ (410) → popover báo đã gỡ, không có nút mở", async () => {
    mockFetch({ "GET /citations/c1": () => jsonResponse({ code: "DOCUMENT_REMOVED", message: "" }, 410) });
    renderCard(turn({}));
    await userEvent.click(screen.getByRole("button", { name: /Nguồn 1/ }));
    expect(await screen.findByText("Tài liệu đã được gỡ khỏi bộ tài liệu.")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Mở tài liệu gốc/ })).not.toBeInTheDocument();
  });

  it("👎 mở 4 lý do, gửi xong đánh dấu aria-pressed", async () => {
    const fetch = mockFetch({
      "PUT /messages/m1/feedback": () => jsonResponse({ turn_id: "m1", rating: "down", reason: "missing" }),
    });
    const onFeedback = vi.fn();
    renderWithProviders(
      <AnswerCard turn={turn({})} index={0} onRegenerate={vi.fn()} onFeedback={onFeedback} onCitationRemoved={vi.fn()} />,
      { me: LAN },
    );
    await userEvent.click(screen.getByRole("button", { name: "Câu trả lời chưa tốt" }));
    expect(screen.getAllByRole("radio")).toHaveLength(4);
    await userEvent.click(screen.getByLabelText("Thiếu thông tin"));
    await userEvent.click(screen.getByRole("button", { name: "Gửi đánh giá" }));
    expect(JSON.parse(fetch.mock.calls[0][1]!.body as string)).toEqual({ rating: "down", reason: "missing" });
    expect(onFeedback).toHaveBeenCalledWith("t1", { rating: "down", reason: "missing" });
  });
});
