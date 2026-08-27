(function () {
  async function load() {
    let expense, income;
    try {
      [expense, income] = await Promise.all([
        Finora.api("/api/categories?type=expense"),
        Finora.api("/api/categories?type=income"),
      ]);
    } catch (e) {
      Finora.toast("Could not load categories.", "error");
      return;
    }
    renderList("expenseCategories", expense);
    renderList("incomeCategories", income);
  }

  function renderList(containerId, categories) {
    const el = document.getElementById(containerId);
    if (!categories.length) {
      el.innerHTML = `<div class="text-muted" style="font-size:13px;padding:20px 0;text-align:center;">No categories yet.</div>`;
      return;
    }
    el.innerHTML = categories
      .map((c) => `
        <div class="flex-between" style="padding:10px 4px;border-bottom:1px solid var(--color-border);">
          <div class="flex gap-12" style="align-items:center;">
            <span style="width:10px;height:10px;border-radius:50%;background:${c.color};display:inline-block;"></span>
            <span style="font-size:13.5px;font-weight:500;">${Finora.escapeHtml(c.name)}</span>
          </div>
        </div>`)
      .join("");
  }

  function openCategoryModal() {
    const overlay = Finora.openModal(`
      <div class="modal">
        <div class="modal-header">
          <div class="modal-title">New Category</div>
          <button class="icon-btn" data-close style="width:30px;height:30px;"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18M6 6l12 12"/></svg></button>
        </div>
        <div class="modal-body">
          <form id="catForm">
            <div class="form-group">
              <label class="field-label">Name</label>
              <input type="text" class="field-input" id="catName" required maxlength="80" placeholder="e.g. Subscriptions" />
            </div>
            <div class="form-group">
              <label class="field-label">Type</label>
              <select class="field-select" id="catType">
                <option value="expense">Expense</option>
                <option value="income">Income</option>
              </select>
            </div>
            <div class="form-group">
              <label class="field-label">Color</label>
              <input type="color" class="field-input" id="catColor" value="#1F6F54" style="height:40px;padding:4px;" />
            </div>
            <div id="catFormError" class="field-error hidden"></div>
          </form>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" data-close>Cancel</button>
          <button class="btn btn-primary" id="catSaveBtn">Create Category</button>
        </div>
      </div>
    `);
    overlay.querySelectorAll("[data-close]").forEach((b) => b.addEventListener("click", Finora.closeModal));
    overlay.querySelector("#catSaveBtn").addEventListener("click", async () => {
      const btn = overlay.querySelector("#catSaveBtn");
      const errEl = overlay.querySelector("#catFormError");
      errEl.classList.add("hidden");
      btn.disabled = true;
      btn.textContent = "Creating…";
      try {
        await Finora.api("/api/categories", {
          method: "POST",
          body: {
            name: overlay.querySelector("#catName").value,
            type: overlay.querySelector("#catType").value,
            color: overlay.querySelector("#catColor").value,
            icon: "tag",
          },
        });
        Finora.toast("Category created.", "success");
        Finora.closeModal();
        load();
      } catch (err) {
        errEl.textContent = err.message || "Could not create category.";
        errEl.classList.remove("hidden");
        btn.disabled = false;
        btn.textContent = "Create Category";
      }
    });
  }

  document.getElementById("addCategoryBtn").addEventListener("click", openCategoryModal);
  load();
})();
