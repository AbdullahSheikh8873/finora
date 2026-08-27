(async function () {
  const currency = window.__FINORA_CURRENCY__ || "PKR";
  let data;
  try {
    data = await Finora.api("/api/reports/dashboard");
  } catch (e) {
    Finora.toast("Could not load dashboard data.", "error");
    return;
  }

  renderStats(data.summary);
  renderTrendChart(data.trend);
  renderBreakdownChart(data.expense_breakdown);
  renderCashFlowChart(data.cash_flow);
  renderBudgetOverview();

  function trendPill(pct) {
    const up = pct >= 0;
    const arrow = up
      ? '<svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="3"><path d="M12 19V5M5 12l7-7 7 7"/></svg>'
      : '<svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="3"><path d="M12 5v14M5 12l7 7 7-7"/></svg>';
    return `<span class="stat-trend ${up ? "up" : "down"}">${arrow} ${Math.abs(pct).toFixed(1)}% <span class="trend-context">vs last period</span></span>`;
  }

  function renderStats(summary) {
    const grid = document.getElementById("statGrid");
    grid.innerHTML = `
      <div class="stat-card">
        <div class="stat-label"><span class="stat-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="6" width="20" height="14" rx="2"/><path d="M2 10h20"/></svg></span>Total Balance</div>
        <div class="stat-value money">${Finora.formatMoney(summary.total_balance, currency)}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label"><span class="stat-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 19V5M5 12l7-7 7 7"/></svg></span>Income</div>
        <div class="stat-value money">${Finora.formatMoney(summary.income, currency)}</div>
        ${trendPill(summary.income_change_pct)}
      </div>
      <div class="stat-card">
        <div class="stat-label"><span class="stat-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12l7 7 7-7"/></svg></span>Expenses</div>
        <div class="stat-value money">${Finora.formatMoney(summary.expenses, currency)}</div>
        ${trendPill(-summary.expenses_change_pct)}
      </div>
      <div class="stat-card">
        <div class="stat-label"><span class="stat-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 3"/></svg></span>Net Savings</div>
        <div class="stat-value money">${Finora.formatMoney(summary.net_savings, currency)}</div>
        <span class="stat-trend ${summary.savings_rate >= 0 ? "up" : "down"}">${summary.savings_rate.toFixed(1)}% savings rate</span>
      </div>
    `;
  }

  function chartColors() {
    const styles = getComputedStyle(document.documentElement);
    return {
      primary: styles.getPropertyValue("--color-primary").trim(),
      secondary: styles.getPropertyValue("--color-secondary").trim(),
      danger: styles.getPropertyValue("--color-danger").trim(),
      text: styles.getPropertyValue("--color-text-muted").trim(),
      border: styles.getPropertyValue("--color-border").trim(),
    };
  }

  function renderTrendChart(trend) {
    const c = chartColors();
    new Chart(document.getElementById("trendChart"), {
      type: "bar",
      data: {
        labels: trend.labels,
        datasets: [
          { label: "Income", data: trend.income, backgroundColor: c.primary, borderRadius: 4, maxBarThickness: 22 },
          { label: "Expenses", data: trend.expenses, backgroundColor: c.secondary, borderRadius: 4, maxBarThickness: 22 },
        ],
      },
      options: {
        responsive: true,
        plugins: { legend: { position: "bottom", labels: { color: c.text, boxWidth: 10, font: { size: 11 } } } },
        scales: {
          x: { grid: { display: false }, ticks: { color: c.text, font: { size: 11 } } },
          y: { grid: { color: c.border }, ticks: { color: c.text, font: { size: 11 } } },
        },
      },
    });
  }

  function renderBreakdownChart(breakdown) {
    if (!breakdown.labels.length) {
      document.getElementById("breakdownChart").classList.add("hidden");
      document.getElementById("breakdownEmpty").classList.remove("hidden");
      return;
    }
    const c = chartColors();
    const palette = [c.primary, c.secondary, "#5B8A6B", "#C98A2C", "#8A6BC9", "#C0442E", "#4B9BC9", "#9AA85C"];
    new Chart(document.getElementById("breakdownChart"), {
      type: "doughnut",
      data: {
        labels: breakdown.labels,
        datasets: [{ data: breakdown.values, backgroundColor: palette, borderWidth: 0 }],
      },
      options: {
        responsive: true,
        cutout: "65%",
        plugins: { legend: { position: "bottom", labels: { color: c.text, boxWidth: 10, font: { size: 11 } } } },
      },
    });
  }

  function renderCashFlowChart(flow) {
    const c = chartColors();
    new Chart(document.getElementById("cashFlowChart"), {
      type: "line",
      data: {
        labels: flow.labels,
        datasets: [
          {
            label: "Balance",
            data: flow.balances,
            borderColor: c.primary,
            backgroundColor: c.primary + "22",
            fill: true,
            tension: 0.35,
            pointRadius: 3,
          },
        ],
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false }, ticks: { color: c.text, font: { size: 11 } } },
          y: { grid: { color: c.border }, ticks: { color: c.text, font: { size: 11 } } },
        },
      },
    });
  }

  async function renderBudgetOverview() {
    const container = document.getElementById("budgetOverview");
    const today = new Date();
    let budgets;
    try {
      budgets = await Finora.api(`/api/budgets?month=${today.getMonth() + 1}&year=${today.getFullYear()}`);
    } catch (e) {
      container.innerHTML = '<div class="text-muted" style="font-size:13px;">Could not load budgets.</div>';
      return;
    }
    if (!budgets.length) {
      container.innerHTML = `
        <div class="empty-state" style="padding:24px 12px;">
          <p style="margin-bottom:12px;">No budgets set for this month yet.</p>
          <a href="/budgets" class="btn btn-primary btn-sm">Create a Budget</a>
        </div>`;
      return;
    }
    container.innerHTML = budgets
      .slice(0, 5)
      .map((b) => {
        const pct = Math.min(b.usage_percent, 100);
        const barColor = b.status === "critical" ? "var(--color-danger)" : b.status === "warning" ? "var(--color-warning)" : "var(--color-primary)";
        return `
          <div style="margin-bottom:14px;">
            <div class="flex-between" style="font-size:13px;margin-bottom:5px;">
              <span style="font-weight:600;">${Finora.escapeHtml(b.category_name)}</span>
              <span class="text-muted money">${Finora.formatMoney(b.spent, currency)} / ${Finora.formatMoney(b.amount, currency)}</span>
            </div>
            <div style="height:7px;border-radius:4px;background:var(--color-bg);overflow:hidden;">
              <div style="height:100%;width:${pct}%;background:${barColor};border-radius:4px;"></div>
            </div>
          </div>`;
      })
      .join("");
  }
})();
