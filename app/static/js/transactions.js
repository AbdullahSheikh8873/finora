(function () {
  const currency = window.__FINORA_CURRENCY__ || "PKR";
  let state = { page: 1, pageSize: 15, total: 0 };
  let accountsCache = [];
  let categoriesCache = [];

  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get("search")) document.getElementById("filterSearch").value = urlParams.get("search");

  async function init() {
    [accountsCache, categoriesCache] = await Promise.all([
      Finora.api("/api/accounts"),
      Finora.api("/api/categories"),
    ]);
    populateFilterSelects();
    bindEvents();
    await loadTransactions();
  }

  function populateFilterSelects() {
    const accSel = document.getElementById("filterAccount");
    accountsCache.forEach((a) => {
      const opt = document.createElement("option");
      opt.value = a.id;
      opt.textContent = a.name;
      accSel.appendChild(opt);
    });
    const catSel = document.getElementById("filterCategory");
    categoriesCache.forEach((c) => {
      const opt = document.createElement("option");
      opt.value = c.id;
      opt.textContent = `${c.name} (${c.type})`;
      catSel.appendChild(opt);
    });
  }

  function bindEvents() {
    document.getElementById("addBtn").addEventListener("click", () => Finora.openTransactionModal(null, () => loadTransactions()));
    document.getElementById("emptyAddBtn").addEventListener("click", () => Finora.openTransactionModal(null, () => loadTransactions()));
    document.getElementById("exportBtn").addEventListener("click", exportCsv);
    document.getElementById("clearFiltersBtn").addEventListener("click", clearFilters);

    let searchTimeout;
    document.getElementById("filterSearch").addEventListener("input", () => {
      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(() => { state.page = 1; loadTransactions(); }, 350);
    });
    ["filterType", "filterAccount", "filterCategory", "filterFrom", "filterTo"].forEach((id) => {
      document.getElementById(id).addEventListener("change", () => { state.page = 1; loadTransactions(); });
    });
  }

  function clearFilters() {
    document.getElementById("filterSearch").value = "";
    document.getElementById("filterType").value = "";
    document.getElementById("filterAccount").value = "";
    document.getElementById("filterCategory").value = "";
    document.getElementById("filterFrom").value = "";
    document.getElementById("filterTo").value = "";
    state.page = 1;
    loadTransactions();
  }

  function buildQuery() {
    const p = new URLSearchParams();
    const search = document.getElementById("filterSearch").value.trim();
    if (search) p.set("search", search);
    const type = document.getElementById("filterType").value;
    if (type) p.set("transaction_type", type);
    const account = document.getElementById("filterAccount").value;
    if (account) p.set("account_id", account);
    const category = document.getElementById("filterCategory").value;
    if (category) p.set("category_id", category);
    const from = document.getElementById("filterFrom").value;
    if (from) p.set("date_from", from);
    const to = document.getElementById("filterTo").value;
    if (to) p.set("date_to", to);
    p.set("page", state.page);
    p.set("page_size", state.pageSize);
    return p.toString();
  }

  function exportCsv() {
    const p = new URLSearchParams();
    const from = document.getElementById("filterFrom").value;
    if (from) p.set("date_from", from);
    const to = document.getElementById("filterTo").value;
    if (to) p.set("date_to", to);
    const account = document.getElementById("filterAccount").value;
    if (account) p.set("account_id", account);
    const category = document.getElementById("filterCategory").value;
    if (category) p.set("category_id", category);
    window.location.href = `/api/export/transactions.csv?${p.toString()}`;
  }

  function accountName(id) {
    const a = accountsCache.find((x) => x.id === id);
    return a ? a.name : "—";
  }
  function categoryName(id) {
    const c = categoriesCache.find((x) => x.id === id);
    return c ? c.name : "Uncategorized";
  }

  async function loadTransactions() {
    const tbody = document.getElementById("txnTableBody");
    tbody.innerHTML = '<tr><td colspan="7"><div class="skeleton" style="height:20px;margin:8px 0;"></div></td></tr>';
    let result;
    try {
      result = await Finora.api(`/api/transactions?${buildQuery()}`);
    } catch (e) {
      Finora.toast("Could not load transactions.", "error");
      return;
    }
    state.total = result.total;

    const table = document.getElementById("txnTable");
    const empty = document.getElementById("txnEmptyState");

    if (result.items.length === 0 && state.page === 1 && !hasActiveFilters()) {
      table.classList.add("hidden");
      empty.classList.remove("hidden");
      document.getElementById("pagination").innerHTML = "";
      return;
    }
    table.classList.remove("hidden");
    empty.classList.add("hidden");

    if (result.items.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;color:var(--color-text-muted);padding:32px;">No transactions match your filters.</td></tr>`;
    } else {
      tbody.innerHTML = result.items
        .map((t) => {
          const isIncome = t.transaction_type === "income";
          return `
          <tr>
            <td data-label="Date">${Finora.formatDate(t.transaction_date)}</td>
            <td data-label="Description">${Finora.escapeHtml(t.description)}</td>
            <td data-label="Category">${Finora.escapeHtml(categoryName(t.category_id))}</td>
            <td data-label="Account">${Finora.escapeHtml(accountName(t.account_id))}</td>
            <td data-label="Type"><span class="pill ${isIncome ? "pill-income" : "pill-expense"}">${isIncome ? "Income" : "Expense"}</span></td>
            <td data-label="Amount" style="text-align:right;" class="${isIncome ? "amount-positive" : "amount-negative"} money">${isIncome ? "+" : "-"}${Finora.formatMoney(t.amount, currency)}</td>
            <td data-label="">
              <div class="row-actions">
                <button class="icon-btn btn-sm" style="width:30px;height:30px;" data-edit="${t.id}"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.12 2.12 0 0 1 3 3L12 15l-4 1 1-4Z"/></svg></button>
                <button class="icon-btn btn-sm" style="width:30px;height:30px;" data-delete="${t.id}"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="var(--color-danger)" stroke-width="2"><path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2m3 0-1 14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2L4 6"/></svg></button>
              </div>
            </td>
          </tr>`;
        })
        .join("");

      tbody.querySelectorAll("[data-edit]").forEach((btn) =>
        btn.addEventListener("click", () => {
          const txn = result.items.find((x) => x.id === btn.dataset.edit);
          Finora.openTransactionModal(txn, () => loadTransactions());
        })
      );
      tbody.querySelectorAll("[data-delete]").forEach((btn) =>
        btn.addEventListener("click", () => {
          Finora.confirmDialog(
            "Delete transaction?",
            "This will remove the transaction and reverse its effect on the account balance. This cannot be undone.",
            async () => {
              await Finora.api(`/api/transactions/${btn.dataset.delete}`, { method: "DELETE" });
              Finora.toast("Transaction deleted.", "success");
              loadTransactions();
            }
          );
        })
      );
    }

    renderPagination();
  }

  function hasActiveFilters() {
    return ["filterSearch", "filterType", "filterAccount", "filterCategory", "filterFrom", "filterTo"].some(
      (id) => document.getElementById(id).value
    );
  }

  function renderPagination() {
    const totalPages = Math.max(1, Math.ceil(state.total / state.pageSize));
    const el = document.getElementById("pagination");
    el.innerHTML = `
      <span>Showing page ${state.page} of ${totalPages} (${state.total} total)</span>
      <div class="flex gap-8">
        <button class="btn btn-secondary btn-sm" id="prevPage" ${state.page <= 1 ? "disabled" : ""}>Previous</button>
        <button class="btn btn-secondary btn-sm" id="nextPage" ${state.page >= totalPages ? "disabled" : ""}>Next</button>
      </div>`;
    const prev = document.getElementById("prevPage");
    const next = document.getElementById("nextPage");
    if (prev) prev.addEventListener("click", () => { state.page--; loadTransactions(); });
    if (next) next.addEventListener("click", () => { state.page++; loadTransactions(); });
  }

  init();
})();
