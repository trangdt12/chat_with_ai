import { afterEach, describe, expect, it } from "vitest";
import { saveDraft, setDraftGetter, takeDraft } from "./draftStore";

afterEach(() => setDraftGetter(null));

describe("draftStore", () => {
  it("saveDraft rồi takeDraft trả nội dung, lần 2 rỗng", () => {
    setDraftGetter(() => "Thời hạn thanh toán là bao lâu?");
    saveDraft();
    expect(takeDraft()).toBe("Thời hạn thanh toán là bao lâu?");
    expect(takeDraft()).toBe("");
  });

  it("không lưu bản nháp rỗng", () => {
    setDraftGetter(() => "   ");
    saveDraft();
    expect(takeDraft()).toBe("");
  });
});
