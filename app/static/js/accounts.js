(function () {
  const currency = window.__FINORA_CURRENCY__ || "PKR";
  const ACCOUNT_TYPE_LABELS = {
    cash: "Cash", bank: "Bank Account", savings: "Savings", credit_card: "Credit Card", wallet: "Wallet",
  };
  const ACCOUNT_ICONS = {
    cash: '<path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>',
    bank: '<path d="M3 21h18M3 10h18M5 6l7-3 7 3M4 10v11M20 10v11M8 14v3M12 14v3M16 14v3"/>',
    savings: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 3"/>',
    credit_card: '<rect x="2" y="6" width="20" height="14" rx="2"/><path d="M2 10h20"/>',
    wallet: '<path d="M20 12V8H6a2 2 0 0 1 0-4h12v4"/><path d="M4 6v12a2 2 0 0 0 2 2h14v-4"/><circle cx="16" cy="14" r="1"/>',
  };

  let accounts = [];

  async function load() {
    try {
      accounts = await Finora.api("/api/accounts");
    } catch (e) {
      Finora.toast("Could not load accounts.", "error");
      return;
    }
    render();
  }

  function render() {
    const grid = document.getElementById("accountsGrid");
    const empty = document.getElementById("accountsEmpty");
    if (accounts.length === 0) {
      grid.classList.add("hidden");
      empty.classList.remove("hidden");
      return;
    }
    grid.classList.remove("hidden");
    empty.classList.add("hidden");

    grid.innerHTML = accounts
      .map((a) => `
        <div class="card card-pad" style="${a.is_active ? "" : "opacity:0.55;"}">
          <div class="flex-between mb-16">
            <div class="stat-icon" style="width:34px;height:34px;">
              <svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="2">${ACCOUNT_ICONS[a.account_type] || ""}</svg>
            </div>
            <div class="row-actions">
              <button class="icon-btn btn-sm" style="width:30px;height:30px;" data-edit="${a.id}"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.12 2.12 0 0 1 3 3L12 15l-4 1 1-4Z"/></svg></button>
              ${a.is_active ? `<button class="icon-btn btn-sm" style="width:30px;height:30px;" data-archive="${a.id}" title="Archive"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="var(--color-danger)" stroke-width="2"><rect x="2" y="4" width="20" height="5" rx="1"/><path d="M4 9v9a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9"/><path d="M10 13h4"/></svg></button>` : `<span class="pill" style="background:var(--color-bg);color:var(--color-text-faint);">Archived</span>`}
            </div>
          </div>
          <div style="font-weight:700;font-size:15px;margin-bottom:2px;">${Finora.escapeHtml(a.name)}</div>
          <div class="text-faint" style="font-size:12px;margin-bottom:14px;">${ACCOUNT_TYPE_LABELS[a.account_type] || a.account_type}</div>
          <div class="text-faint" style="font-size:11px;text-transform:uppercase;letter-spacing:0.05em;">Balance</div>
          <div class="stat-value money" style="font-size:23px;">${Finora.formatMoney(a.current_balance, a.currency)}</div>
        </div>`)
      .join("");

    grid.querySelectorAll("[data-edit]").forEach((btn) =>
      btn.addEventListener("click", () => openAccountModal(accounts.find((x) => x.id === btn.dataset.edit)))
    );
    grid.querySelectorAll("[data-archive]").forEach((btn) =>
      btn.addEventListener("click", () => {
        Finora.confirmDialog(
          "Archive account?",
          "Archived accounts are hidden from new transactions but their history is kept.",
          async () => {
            await Finora.api(`/api/accounts/${btn.dataset.archive}/archive`, { method: "POST" });
            Finora.toast("Account archived.", "success");
            load();
          },
          "Archive",
          false
        );
      })
    );
  }

  function openAccountModal(existing) {
    const isEdit = !!existing;
    const overlay = Finora.openModal(`
      <div class="modal">
        <div class="modal-header">
          <div class="modal-title">${isEdit ? "Edit Account" : "Add Account"}</div>
          <button class="icon-btn" data-close style="width:30px;height:30px;"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18M6 6l12 12"/></svg></button>
        </div>
        <div class="modal-body">
          <form id="accForm">
            <div class="form-group">
              <label class="field-label">Account Name</label>
              <input type="text" class="field-input" id="accName" value="${existing ? Finora.escapeHtml(existing.name) : ""}" required maxlength="120" placeholder="e.g. HBL Bank" />
            </div>
            <div class="form-row">
              <div class="form-group">
                <label class="field-label">Account Type</label>
                <select class="field-select" id="accType">
                  ${Object.entries(ACCOUNT_TYPE_LABELS).map(([v, l]) => `<option value="${v}" ${existing && existing.account_type === v ? "selected" : ""}>${l}</option>`).join("")}
                </select>
              </div>
              <div class="form-group">
                <label class="field-label">Currency</label>
                <select class="field-select" id="accCurrency">
                  ${["PKR", "USD", "EUR", "GBP"].map((c) => `<option value="${c}" ${existing && existing.currency === c ? "selected" : ""}>${c}</option>`).join("")}
                </select>
              </div>
            </div>
            ${!isEdit ? `
            <div class="form-group">
              <label class="field-label">Opening Balance</label>
              <input type="number" step="0.01" class="field-input" id="accBalance" value="0.00" required />
            </div>` : ""}
            <div id="accFormError" class="field-error hidden"></div>
          </form>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" data-close>Cancel</button>
          <button class="btn btn-primary" id="accSaveBtn">${isEdit ? "Save Changes" : "Add Account"}</button>
        </div>
      </div>
    `);
    overlay.querySelectorAll("[data-close]").forEach((b) => b.addEventListener("click", Finora.closeModal));
    overlay.querySelector("#accSaveBtn").addEventListener("click", async () => {
      const btn = overlay.querySelector("#accSaveBtn");
      const errEl = overlay.querySelector("#accFormError");
      errEl.classList.add("hidden");
      btn.disabled = true;
      btn.textContent = "Saving…";
      try {
        if (isEdit) {
          await Finora.api(`/api/accounts/${existing.id}`, {
            method: "PUT",
            body: {
              name: overlay.querySelector("#accName").value,
              account_type: overlay.querySelector("#accType").value,
              currency: overlay.querySelector("#accCurrency").value,
            },
          });
          Finora.toast("Account updated.", "success");
        } else {
          await Finora.api("/api/accounts", {
            method: "POST",
            body: {
              name: overlay.querySelector("#accName").value,
              account_type: overlay.querySelector("#accType").value,
              currency: overlay.querySelector("#accCurrency").value,
              opening_balance: overlay.querySelector("#accBalance").value,
            },
          });
          Finora.toast("Account created.", "success");
        }
        Finora.closeModal();
        load();
        Finora.refreshNotifBadge();
      } catch (err) {
        errEl.textContent = err.message || "Could not save account.";
        errEl.classList.remove("hidden");
        btn.disabled = false;
        btn.textContent = isEdit ? "Save Changes" : "Add Account";
      }
    });
  }

  function openTransferModal() {
    if (accounts.length < 2) {
      Finora.toast("You need at least two accounts to transfer money.", "error");
      return;
    }
    const overlay = Finora.openModal(`
      <div class="modal">
        <div class="modal-header">
          <div class="modal-title">Transfer Money</div>
          <button class="icon-btn" data-close style="width:30px;height:30px;"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18M6 6l12 12"/></svg></button>
        </div>
        <div class="modal-body">
          <form id="transferForm">
            <div class="form-row">
              <div class="form-group">
                <label class="field-label">From</label>
                <select class="field-select" id="fromAccount">${accounts.map((a) => `<option value="${a.id}">${Finora.escapeHtml(a.name)}</option>`).join("")}</select>
              </div>
              <div class="form-group">
                <label class="field-label">To</label>
                <select class="field-select" id="toAccount">${accounts.map((a, i) => `<option value="${a.id}" ${i === 1 ? "selected" : ""}>${Finora.escapeHtml(a.name)}</option>`).join("")}</select>
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label class="field-label">Amount</label>
                <input type="number" step="0.01" min="0.01" class="field-input" id="transferAmount" required />
              </div>
              <div class="form-group">
                <label class="field-label">Date</label>
                <input type="date" class="field-input" id="transferDate" value="${new Date().toISOString().slice(0,10)}" required />
              </div>
            </div>
            <div class="form-group">
              <label class="field-label">Description (optional)</label>
              <input type="text" class="field-input" id="transferDescription" maxlength="255" />
            </div>
            <div id="transferFormError" class="field-error hidden"></div>
          </form>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" data-close>Cancel</button>
          <button class="btn btn-primary" id="transferSaveBtn">Transfer</button>
        </div>
      </div>
    `);
    overlay.querySelectorAll("[data-close]").forEach((b) => b.addEventListener("click", Finora.closeModal));
    overlay.querySelector("#transferSaveBtn").addEventListener("click", async () => {
      const btn = overlay.querySelector("#transferSaveBtn");
      const errEl = overlay.querySelector("#transferFormError");
      errEl.classList.add("hidden");
      const fromId = overlay.querySelector("#fromAccount").value;
      const toId = overlay.querySelector("#toAccount").value;
      if (fromId === toId) {
        errEl.textContent = "Source and destination accounts must be different.";
        errEl.classList.remove("hidden");
        return;
      }
      btn.disabled = true;
      btn.textContent = "Transferring…";
      try {
        await Finora.api("/api/transfers", {
          method: "POST",
          body: {
            from_account_id: fromId,
            to_account_id: toId,
            amount: overlay.querySelector("#transferAmount").value,
            transfer_date: overlay.querySelector("#transferDate").value,
            description: overlay.querySelector("#transferDescription").value || null,
          },
        });
        Finora.toast("Transfer completed.", "success");
        Finora.closeModal();
        load();
      } catch (err) {
        errEl.textContent = err.message || "Transfer failed.";
        errEl.classList.remove("hidden");
        btn.disabled = false;
        btn.textContent = "Transfer";
      }
    });
  }

  document.getElementById("addAccountBtn").addEventListener("click", () => openAccountModal(null));
  document.getElementById("emptyAddAccountBtn").addEventListener("click", () => openAccountModal(null));
  document.getElementById("transferBtn").addEventListener("click", openTransferModal);

  load();
})();
