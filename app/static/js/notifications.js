(function () {
  const TYPE_ICONS = {
    budget_warning: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 3"/>',
    budget_exceeded: '<path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z"/><path d="M12 9v4M12 17h.01"/>',
    large_expense: '<path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>',
    account_created: '<rect x="2" y="6" width="20" height="14" rx="2"/><path d="M2 10h20"/>',
    monthly_summary: '<path d="M3 3v18h18"/><path d="M7 15l4-6 3 3 5-8"/>',
    info: '<circle cx="12" cy="12" r="9"/><path d="M12 16v-4M12 8h.01"/>',
  };

  async function load() {
    let items;
    try {
      items = await Finora.api("/api/notifications");
    } catch (e) {
      Finora.toast("Could not load notifications.", "error");
      return;
    }
    render(items);
  }

  function render(items) {
    const list = document.getElementById("notifList");
    const empty = document.getElementById("notifEmpty");
    if (!items.length) {
      list.classList.add("hidden");
      empty.classList.remove("hidden");
      return;
    }
    list.classList.remove("hidden");
    empty.classList.add("hidden");
    list.innerHTML = items
      .map((n) => `
        <div class="flex gap-12" style="padding:16px 20px;border-bottom:1px solid var(--color-border);${n.is_read ? "" : "background:var(--color-primary-soft);"}" data-id="${n.id}">
          <div class="stat-icon" style="width:36px;height:36px;flex-shrink:0;">
            <svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="2">${TYPE_ICONS[n.type] || TYPE_ICONS.info}</svg>
          </div>
          <div style="flex:1;">
            <div class="flex-between">
              <span style="font-weight:600;font-size:13.5px;">${Finora.escapeHtml(n.title)}</span>
              <span class="text-faint" style="font-size:11.5px;">${Finora.formatDate(n.created_at.slice(0, 10))}</span>
            </div>
            <div class="text-muted" style="font-size:13px;margin-top:3px;">${Finora.escapeHtml(n.message)}</div>
          </div>
          ${n.is_read ? "" : '<button class="btn btn-ghost btn-sm" data-mark-read style="align-self:center;">Mark read</button>'}
        </div>`)
      .join("");

    list.querySelectorAll("[data-mark-read]").forEach((btn) => {
      btn.addEventListener("click", async (e) => {
        const row = e.target.closest("[data-id]");
        await Finora.api(`/api/notifications/${row.dataset.id}/read`, { method: "POST" });
        load();
        Finora.refreshNotifBadge();
      });
    });
  }

  document.getElementById("markAllReadBtn").addEventListener("click", async () => {
    await Finora.api("/api/notifications/mark-all-read", { method: "POST" });
    Finora.toast("All notifications marked as read.", "success");
    load();
    Finora.refreshNotifBadge();
  });

  load();
})();
