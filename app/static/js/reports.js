(function () {
  const currency = window.__FINORA_CURRENCY__ || "PKR";
  let chartInstance = null;

  const periodSelect = document.getElementById("periodSelect");
  const customFrom = document.getElementById("customFrom");
  const customTo = document.getElementById("customTo");

  periodSelect.addEventListener("change", () => {
    const isCustom = periodSelect.value === "custom";
    customFrom.classList.toggle("hidden", !isCustom);
    customTo.classList.toggle("hidden", !isCustom);
    if (!isCustom || (customFrom.value && customTo.value)) load();
  });
  customFrom.addEventListener("change", () => { if (customTo.value) load(); });
  customTo.addEventListener("change", () => { if (customFrom.value) load(); });

  function trendPill(pct) {
    const up = pct >= 0;
    const arrow = up ? "▲" : "▼";
    return `<span class="stat-trend ${up ? "up" : "down"}">${arrow} ${Math.abs(pct).toFixed(1)}% <span class="trend-context">vs previous period</span></span>`;
  }

  async function load() {
    const params = new URLSearchParams({ period: periodSelect.value });
    if (periodSelect.value === "custom") {
      if (!customFrom.value || !customTo.value) return;
      params.set("date_from", customFrom.value);
      params.set("date_to", customTo.value);
    }
    let data;
    try {
      data = await Finora.api(`/api/reports/summary?${params.toString()}`);
    } catch (e) {
      Finora.toast("Could not load report.", "error");
      return;
    }
    renderStats(data.summary);
    renderChart(data.expense_breakdown);
  }

  function renderStats(summary) {
    document.getElementById("reportStats").innerHTML = `
      <div class="stat-card">
        <div class="stat-label">Total Balance</div>
        <div class="stat-value money">${Finora.formatMoney(summary.total_balance, currency)}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Income</div>
        <div class="stat-value money">${Finora.formatMoney(summary.income, currency)}</div>
        ${trendPill(summary.income_change_pct)}
      </div>
      <div class="stat-card">
        <div class="stat-label">Expenses</div>
        <div class="stat-value money">${Finora.formatMoney(summary.expenses, currency)}</div>
        ${trendPill(-summary.expenses_change_pct)}
      </div>
      <div class="stat-card">
        <div class="stat-label">Net Savings</div>
        <div class="stat-value money">${Finora.formatMoney(summary.net_savings, currency)}</div>
        <span class="stat-trend ${summary.savings_rate >= 0 ? "up" : "down"}">${summary.savings_rate.toFixed(1)}% savings rate</span>
      </div>`;
  }

  function renderChart(breakdown) {
    const canvas = document.getElementById("reportBreakdownChart");
    const emptyEl = document.getElementById("reportBreakdownEmpty");
    if (chartInstance) { chartInstance.destroy(); chartInstance = null; }

    if (!breakdown.labels.length) {
      canvas.classList.add("hidden");
      emptyEl.classList.remove("hidden");
      return;
    }
    canvas.classList.remove("hidden");
    emptyEl.classList.add("hidden");

    const styles = getComputedStyle(document.documentElement);
    const text = styles.getPropertyValue("--color-text-muted").trim();
    const border = styles.getPropertyValue("--color-border").trim();
    const primary = styles.getPropertyValue("--color-primary").trim();

    chartInstance = new Chart(canvas, {
      type: "bar",
      data: {
        labels: breakdown.labels,
        datasets: [{ label: "Spent", data: breakdown.values, backgroundColor: primary, borderRadius: 4, maxBarThickness: 32 }],
      },
      options: {
        indexAxis: "y",
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { color: border }, ticks: { color: text, font: { size: 11 } } },
          y: { grid: { display: false }, ticks: { color: text, font: { size: 11 } } },
        },
      },
    });
  }

  load();
})();
