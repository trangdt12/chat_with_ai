/* Tương tác tối thiểu cho file thiết kế (KHÔNG phải mã sản phẩm).
   - Chuyển trạng thái màn hình: nút [data-state] trong .state-switcher đặt <body data-state="...">;
     phần tử có data-show-in="a b" chỉ hiện khi trạng thái hiện tại nằm trong danh sách.
   - Ngăn kéo thanh tài liệu (768–1279px): nút .drawer-toggle bật/tắt .docs-panel.is-open.
   - Bộ đếm ký tự cho textarea[data-counter] (UI-006: tối đa 2.000, hiện khi còn ≤ 200). */
(function () {
  function applyState(state) {
    document.body.dataset.state = state;
    document.querySelectorAll("[data-show-in]").forEach(function (el) {
      var states = el.getAttribute("data-show-in").split(/\s+/);
      el.hidden = states.indexOf(state) === -1;
    });
    document.querySelectorAll(".state-switcher [data-state]").forEach(function (b) {
      b.setAttribute("aria-pressed", String(b.dataset.state === state));
    });
    // Như ứng dụng chat thật: luôn hiển thị tin nhắn mới nhất
    document.querySelectorAll(".chat-scroll").forEach(function (el) { el.scrollTop = el.scrollHeight; });
  }

  document.addEventListener("DOMContentLoaded", function () {
    // ?clean: ẩn thanh chuyển trạng thái và ghi chú thiết kế (dùng khi chụp ảnh cho tài liệu)
    if (/[?&]clean\b/.test(location.search)) document.body.classList.add("clean");
    var first = document.querySelector(".state-switcher [data-state]");
    var fromHash = location.hash.replace("#", "");
    if (first) {
      var valid = document.querySelector('.state-switcher [data-state="' + fromHash + '"]');
      applyState(valid ? fromHash : first.dataset.state);
    }
    document.querySelectorAll(".state-switcher [data-state]").forEach(function (b) {
      b.addEventListener("click", function () {
        applyState(b.dataset.state);
        history.replaceState(null, "", "#" + b.dataset.state);
      });
    });

    var toggle = document.querySelector(".drawer-toggle");
    var panel = document.querySelector(".docs-panel");
    if (toggle && panel) {
      toggle.addEventListener("click", function () {
        var open = panel.classList.toggle("is-open");
        toggle.setAttribute("aria-expanded", String(open));
      });
    }

    document.querySelectorAll("textarea[data-counter]").forEach(function (ta) {
      var max = Number(ta.dataset.max || 2000);   // không dùng maxlength để còn hiển thị được trạng thái vượt (E-15)
      var out = document.getElementById(ta.dataset.counter);
      var send = document.getElementById(ta.dataset.send);
      function update() {
        var left = max - ta.value.length;
        if (out) {
          out.hidden = left > 200;
          out.textContent = ta.value.length.toLocaleString("vi-VN") + " / " + max.toLocaleString("vi-VN");
          out.classList.toggle("over", left < 0);
        }
        if (send && !send.dataset.locked) {
          var empty = ta.value.trim().length === 0;
          send.disabled = empty || left < 0;          // E-14 rỗng, E-15 vượt 2.000
        }
      }
      ta.addEventListener("input", update);
      ta.addEventListener("keydown", function (e) {
        if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); }
      });
      update();
    });
  });
})();
