/* Finora core client: theme, API helper, toasts, modal helper, shell wiring. */

const Finora = (() => {
  const CURRENCY_SYMBOLS = { PKR: "PKR", USD: "$", EUR: "€", GBP: "£" };

  function formatMoney(amount, currency = "PKR") {
    const num = typeof amount === "string" ? parseFloat(amount) : amount;
    const symbol = CURRENCY_SYMBOLS[currency] || currency;
    const formatted = Math.abs(num).toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
    const sign = num < 0 ? "-" : "";
    return `${sign}${symbol} ${formatted}`;
  }

  function formatDate(dateStr) {
    const d = new Date(dateStr + (dateStr.length === 10 ? "T00:00:00" : ""));
    return d.toLocaleDateString(undefined, { day: "2-digit", month: "short", year: "numeric" });
  }

  async function api(path, options = {}) {
    const opts = {
      method: options.method || "GET",
      headers: { "Content-Type": "application/json" },
      credentials: "same-origin",
    };
    if (options.body !== undefined) opts.body = JSON.stringify(options.body);

    const resp = await fetch(path, opts);

    if (resp.status === 401) {
      window.location.href = "/login";
      throw new Error("Not authenticated");
    }

    if (resp.status === 204) return null;

    let data = null;
    try {
      data = await resp.json();
    } catch (e) {
      /* no body */
    }

    if (!resp.ok) {
      const message = extractErrorMessage(data) || `Request failed (${resp.status})`;
      throw new ApiError(message, resp.status, data);
    }
    return data;
  }

  function extractErrorMessage(data) {
    if (!data) return null;
    if (typeof data.detail === "string") return data.detail;
    if (Array.isArray(data.detail)) {
      return data.detail.map((e) => `${e.field ? e.field + ": " : ""}${e.message}`).join(" · ");
    }
    return null;
  }

  class ApiError extends Error {
    constructor(message, status, data) {
      super(message);
      this.status = status;
      this.data = data;
    }
  }

  function toast(message, type = "info") {
    const stack = document.getElementById("toastStack");
    if (!stack) return;
    const el = document.createElement("div");
    el.className = `toast ${type}`;
    el.textContent = message;
    stack.appendChild(el);
    setTimeout(() => {
      el.style.transition = "opacity 0.25s ease";
      el.style.opacity = "0";
      setTimeout(() => el.remove(), 250);
    }, 3800);
  }

  function openModal(html) {
    const overlay = document.createElement("div");
    overlay.className = "modal-overlay";
    overlay.innerHTML = html;
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) closeModal();
    });
    document.body.appendChild(overlay);
    document.body.style.overflow = "hidden";
    return overlay;
  }

  function closeModal() {
    document.querySelectorAll(".modal-overlay").forEach((el) => el.remove());
    document.body.style.overflow = "";
  }

  function confirmDialog(title, message, onConfirm, confirmLabel = "Delete", danger = true) {
    const overlay = openModal(`
      <div class="modal" style="max-width:380px;">
        <div class="modal-header">
          <div class="modal-title">${title}</div>
        </div>
        <div class="modal-body">
          <p class="text-muted" style="margin:0;">${message}</p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" data-cancel>Cancel</button>
          <button class="btn ${danger ? "btn-danger" : "btn-primary"}" data-confirm>${confirmLabel}</button>
        </div>
      </div>
    `);
    overlay.querySelector("[data-cancel]").addEventListener("click", closeModal);
    overlay.querySelector("[data-confirm]").addEventListener("click", async () => {
      const btn = overlay.querySelector("[data-confirm]");
      btn.disabled = true;
      btn.textContent = "Please wait…";
      try {
        await onConfirm();
        closeModal();
      } catch (err) {
        toast(err.message || "Something went wrong.", "error");
        btn.disabled = false;
        btn.textContent = confirmLabel;
      }
    });
  }

  function escapeHtml(str) {
    if (str === null || str === undefined) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  // -------------------- Theme --------------------
  function initTheme() {
    const saved = localStorage.getItem("finora-theme") || "light";
    document.documentElement.setAttribute("data-theme", saved);
    updateThemeIcon(saved);
  }

  function updateThemeIcon(theme) {
    const sun = document.getElementById("themeIconSun");
    const moon = document.getElementById("themeIconMoon");
    if (!sun || !moon) return;
    if (theme === "dark") {
      sun.classList.add("hidden");
      moon.classList.remove("hidden");
    } else {
      sun.classList.remove("hidden");
      moon.classList.add("hidden");
    }
  }

  async function toggleTheme() {
    const current = document.documentElement.getAttribute("data-theme");
    const next = current === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("finora-theme", next);
    updateThemeIcon(next);
    try {
      await api("/api/users/me/preferences", {
        method: "PUT",
        body: { currency: window.__FINORA_CURRENCY__ || "PKR", date_format: "DD MMM YYYY", theme: next },
      });
    } catch (e) {
      /* non-fatal */
    }
  }

  // -------------------- Shell wiring --------------------
  function initShell() {
    initTheme();

    const themeToggle = document.getElementById("themeToggle");
    if (themeToggle) themeToggle.addEventListener("click", toggleTheme);

    const logoutBtn = document.getElementById("logoutBtn");
    if (logoutBtn) {
      logoutBtn.addEventListener("click", async () => {
        await api("/api/auth/logout", { method: "POST" });
        window.location.href = "/login";
      });
    }

    const hamburger = document.getElementById("hamburgerBtn");
    const sidebar = document.getElementById("sidebar");
    const backdrop = document.getElementById("sidebarBackdrop");
    if (hamburger && sidebar && backdrop) {
      hamburger.addEventListener("click", () => {
        sidebar.classList.add("open");
        backdrop.classList.add("open");
      });
      backdrop.addEventListener("click", () => {
        sidebar.classList.remove("open");
        backdrop.classList.remove("open");
      });
    }

    const search = document.getElementById("globalSearch");
    if (search) {
      search.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && search.value.trim()) {
          window.location.href = `/transactions?search=${encodeURIComponent(search.value.trim())}`;
        }
      });
    }

    refreshNotifBadge();
  }

  async function refreshNotifBadge() {
    const badge = document.getElementById("notifBadge");
    if (!badge) return;
    try {
      const res = await api("/api/notifications/unread-count");
      if (res.count > 0) badge.classList.remove("hidden");
      else badge.classList.add("hidden");
    } catch (e) {
      /* ignore */
    }
  }

  // -------------------- Shared: Add/Edit Transaction Modal --------------------
  async function openTransactionModal(existing, onSaved) {
    let accounts = [];
    let categories = [];
    try {
      [accounts, categories] = await Promise.all([
        api("/api/accounts"),
        api("/api/categories"),
      ]);
    } catch (e) {
      toast("Could not load accounts/categories.", "error");
      return;
    }

    if (accounts.length === 0) {
      toast("Create an account first before adding transactions.", "error");
      return;
    }

    const isEdit = !!existing;
    const type0 = existing ? existing.transaction_type : "expense";

    function categoryOptions(type) {
      return categories
        .filter((c) => c.type === type)
        .map((c) => `<option value="${c.id}" ${existing && existing.category_id === c.id ? "selected" : ""}>${escapeHtml(c.name)}</option>`)
        .join("");
    }

    const overlay = openModal(`
      <div class="modal">
        <div class="modal-header">
          <div class="modal-title">${isEdit ? "Edit Transaction" : "Add Transaction"}</div>
          <button class="icon-btn" data-close style="width:30px;height:30px;">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18M6 6l12 12"/></svg>
          </button>
        </div>
        <div class="modal-body">
          <form id="txnForm">
            <div class="form-group">
              <label class="field-label">Type</label>
              <div class="flex gap-8">
                <label class="btn btn-secondary btn-sm" style="flex:1;justify-content:center;" id="typeExpenseLabel">
                  <input type="radio" name="ttype" value="expense" style="margin-right:6px;" ${type0 === "expense" ? "checked" : ""}/> Expense
                </label>
                <label class="btn btn-secondary btn-sm" style="flex:1;justify-content:center;" id="typeIncomeLabel">
                  <input type="radio" name="ttype" value="income" style="margin-right:6px;" ${type0 === "income" ? "checked" : ""}/> Income
                </label>
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label class="field-label">Amount</label>
                <input type="number" step="0.01" min="0.01" class="field-input" id="txnAmount" value="${existing ? existing.amount : ""}" required />
              </div>
              <div class="form-group">
                <label class="field-label">Date</label>
                <input type="date" class="field-input" id="txnDate" value="${existing ? existing.transaction_date : new Date().toISOString().slice(0,10)}" required />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label class="field-label">Account</label>
                <select class="field-select" id="txnAccount" required>
                  ${accounts.map((a) => `<option value="${a.id}" ${existing && existing.account_id === a.id ? "selected" : ""}>${escapeHtml(a.name)}</option>`).join("")}
                </select>
              </div>
              <div class="form-group">
                <label class="field-label">Category</label>
                <select class="field-select" id="txnCategory">${categoryOptions(type0)}</select>
              </div>
            </div>
            <div class="form-group">
              <label class="field-label">Description</label>
              <input type="text" class="field-input" id="txnDescription" value="${existing ? escapeHtml(existing.description) : ""}" required maxlength="255" />
            </div>
            <div class="form-group">
              <label class="field-label">Notes (optional)</label>
              <textarea class="field-textarea" id="txnNotes" rows="2">${existing && existing.notes ? escapeHtml(existing.notes) : ""}</textarea>
            </div>
            <div id="txnFormError" class="field-error hidden"></div>
          </form>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" data-close>Cancel</button>
          <button class="btn btn-primary" id="txnSaveBtn">${isEdit ? "Save Changes" : "Add Transaction"}</button>
        </div>
      </div>
    `);

    overlay.querySelectorAll("[data-close]").forEach((b) => b.addEventListener("click", closeModal));

    function refreshCategoryOptions() {
      const type = overlay.querySelector('input[name="ttype"]:checked').value;
      overlay.querySelector("#txnCategory").innerHTML = categoryOptions(type);
    }
    overlay.querySelectorAll('input[name="ttype"]').forEach((r) => r.addEventListener("change", refreshCategoryOptions));

    overlay.querySelector("#txnSaveBtn").addEventListener("click", async () => {
      const btn = overlay.querySelector("#txnSaveBtn");
      const errEl = overlay.querySelector("#txnFormError");
      errEl.classList.add("hidden");
      const payload = {
        transaction_type: overlay.querySelector('input[name="ttype"]:checked').value,
        amount: overlay.querySelector("#txnAmount").value,
        account_id: overlay.querySelector("#txnAccount").value,
        category_id: overlay.querySelector("#txnCategory").value || null,
        transaction_date: overlay.querySelector("#txnDate").value,
        description: overlay.querySelector("#txnDescription").value,
        notes: overlay.querySelector("#txnNotes").value || null,
      };
      btn.disabled = true;
      btn.textContent = "Saving…";
      try {
        if (isEdit) {
          await api(`/api/transactions/${existing.id}`, { method: "PUT", body: payload });
          toast("Transaction updated.", "success");
        } else {
          await api("/api/transactions", { method: "POST", body: payload });
          toast("Transaction added.", "success");
        }
        closeModal();
        if (onSaved) onSaved();
      } catch (err) {
        errEl.textContent = err.message || "Could not save transaction.";
        errEl.classList.remove("hidden");
        btn.disabled = false;
        btn.textContent = isEdit ? "Save Changes" : "Add Transaction";
      }
    });
  }

  document.addEventListener("DOMContentLoaded", initShell);

  return {
    api,
    ApiError,
    toast,
    openModal,
    closeModal,
    confirmDialog,
    formatMoney,
    formatDate,
    escapeHtml,
    refreshNotifBadge,
    openTransactionModal,
  };
})();

function openAddTransactionModal(onSaved) {
  Finora.openTransactionModal(null, onSaved || (() => window.location.reload()));
}
