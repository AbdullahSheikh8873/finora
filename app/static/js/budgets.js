(function () {
  const currency = window.__FINORA_CURRENCY__ || "PKR";
  const MONTH_NAMES = ["January","February","March","April","May","June","July","August","September","October","November","December"];

  const now = new Date();
  let selectedMonth = now.getMonth() + 1;
  let selectedYear = now.getFullYear();
  let categories = [];
  let currentBudgets = [];

  function populateMonthSelect() {
    const sel = document.getElementById("monthSelect");
    const options = [];
    for (let i = -6; i <= 3; i++) {
      const d = new Date(now.getFullYear(), now.getMonth() + i, 1);
      const m = d.getMonth() + 1, y = d.getFullYear();
      options.push(`<option value="${m}-${y}" ${m === selectedMonth && y === selectedYear ? "selected" : ""}>${MONTH_NAMES[d.getMonth()]} ${y}</option>`);
    }
    sel.innerHTML = options.join("");
    sel.addEventListener("change", () => {
      const [m, y] = sel.value.split("-").map(Number);
      selectedMonth = m; selectedYear = y;
      load();
    });
  }

  async function load() {
    try {
      [categories, currentBudgets] = await Promise.all([
        Finora.api("/api/categories?type=expense"),
        Finora.api(`/api/budgets?month=${selectedMonth}&year=${selectedYear}`),
      ]);
    } catch (e) {
      Finora.toast("Could not load budgets.", "error");
      return;
    }
    render();
  }

  function render() {
    const grid = document.getElementById("budgetsGrid");
    const empty = document.getElementById("budgetsEmpty");
    if (currentBudgets.length === 0) {
      grid.classList.add("hidden");
      empty.classList.remove("hidden");
      return;
    }
    grid.classList.remove("hidden");
    empty.classList.add("hidden");

    grid.innerHTML = currentBudgets
      .map((b) => {
        const pct = Math.min(b.usage_percent, 100);
        const pillClass = `pill-${b.status}`;
        const barColor = b.status === "critical" ? "var(--color-danger)" : b.status === "warning" ? "var(--color-warning)" : "var(--color-primary)";
        return `
        <div class="card card-pad">
          <div class="flex-between mb-16">
            <div style="font-weight:700;font-size:15px;">${Finora.escapeHtml(b.category_name)}</div>
            <div class="flex gap-8" style="align-items:center;">
              <span class="pill ${pillClass}">${b.status}</span>
              <button class="icon-btn btn-sm" style="width:28px;height:28px;" data-delete="${b.id}"><svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="var(--color-danger)" stroke-width="2"><path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2m3 0-1 14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2L4 6"/></svg></button>
            </div>
          </div>
          <div class="flex-between" style="font-size:13px;margin-bottom:6px;">
            <span class="money">${Finora.formatMoney(b.spent, currency)}</span>
            <span class="text-faint money">of ${Finora.formatMoney(b.amount, currency)}</span>
          </div>
          <div style="height:8px;border-radius:4px;background:var(--color-bg);overflow:hidden;margin-bottom:8px;">
            <div style="height:100%;width:${pct}%;background:${barColor};border-radius:4px;transition:width 0.3s ease;"></div>
          </div>
          <div class="text-faint" style="font-size:12px;">${Finora.formatMoney(b.remaining, currency)} remaining · ${b.usage_percent.toFixed(0)}% used</div>
        </div>`;
      })
      .join("");

    grid.querySelectorAll("[data-delete]").forEach((btn) =>
      btn.addEventListener("click", () => {
        Finora.confirmDialog("Delete budget?", "This won't affect any transactions, only the budget limit.", async () => {
          await Finora.api(`/api/budgets/${btn.dataset.delete}`, { method: "DELETE" });
          Finora.toast("Budget deleted.", "success");
          load();
        });
      })
    );
  }

  function openBudgetModal() {
    const usedCategoryIds = new Set(currentBudgets.map((b) => b.category_id));
    const available = categories.filter((c) => !usedCategoryIds.has(c.id));
    if (available.length === 0) {
      Finora.toast("Every expense category already has a budget for this month.", "error");
      return;
    }
    const overlay = Finora.openModal(`
      <div class="modal">
        <div class="modal-header">
          <div class="modal-title">New Budget</div>
          <button class="icon-btn" data-close style="width:30px;height:30px;"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18M6 6l12 12"/></svg></button>
        </div>
        <div class="modal-body">
          <form id="budgetForm">
            <div class="form-group">
              <label class="field-label">Category</label>
              <select class="field-select" id="budgetCategory">${available.map((c) => `<option value="${c.id}">${Finora.escapeHtml(c.name)}</option>`).join("")}</select>
            </div>
            <div class="form-group">
              <label class="field-label">Monthly Limit</label>
              <input type="number" step="0.01" min="0.01" class="field-input" id="budgetAmount" required />
            </div>
            <div class="field-hint">For ${MONTH_NAMES[selectedMonth - 1]} ${selectedYear}</div>
            <div id="budgetFormError" class="field-error hidden mt-8"></div>
          </form>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" data-close>Cancel</button>
          <button class="btn btn-primary" id="budgetSaveBtn">Create Budget</button>
        </div>
      </div>
    `);
    overlay.querySelectorAll("[data-close]").forEach((b) => b.addEventListener("click", Finora.closeModal));
    overlay.querySelector("#budgetSaveBtn").addEventListener("click", async () => {
      const btn = overlay.querySelector("#budgetSaveBtn");
      const errEl = overlay.querySelector("#budgetFormError");
      errEl.classList.add("hidden");
      btn.disabled = true;
      btn.textContent = "Creating…";
      try {
        await Finora.api("/api/budgets", {
          method: "POST",
          body: {
            category_id: overlay.querySelector("#budgetCategory").value,
            amount: overlay.querySelector("#budgetAmount").value,
            month: selectedMonth,
            year: selectedYear,
          },
        });
        Finora.toast("Budget created.", "success");
        Finora.closeModal();
        load();
      } catch (err) {
        errEl.textContent = err.message || "Could not create budget.";
        errEl.classList.remove("hidden");
        btn.disabled = false;
        btn.textContent = "Create Budget";
      }
    });
  }

  document.getElementById("addBudgetBtn").addEventListener("click", openBudgetModal);
  document.getElementById("emptyAddBudgetBtn").addEventListener("click", openBudgetModal);

  populateMonthSelect();
  load();
})();
