(() => {
  const inventoryEl = document.getElementById("overview-inventory");
  const ordersEl = document.getElementById("overview-orders");
  const updatedEl = document.getElementById("overview-updated");
  const refreshBtn = document.getElementById("overview-refresh");
  const resetBtn = document.getElementById("overview-reset");
  const statOrders = document.getElementById("stat-orders");
  const statSubtotal = document.getElementById("stat-subtotal");
  const statDeposit = document.getElementById("stat-deposit");
  const statTotal = document.getElementById("stat-total");

  // Reset-Dialog
  const resetDialog = document.getElementById("reset-dialog");
  const resetPasswordEl = document.getElementById("reset-dialog-password");
  const resetErrorEl = document.getElementById("reset-dialog-error");
  const resetForm = document.getElementById("reset-dialog-form");
  const resetCancel = document.getElementById("reset-dialog-cancel");

  // Editor
  const editorOverlay = document.getElementById("limit-editor");
  const editorNameEl = document.getElementById("limit-editor-name");
  const editorCriticalEl = document.getElementById("limit-editor-critical");
  const editorWarnEl = document.getElementById("limit-editor-warn");
  const editorErrorEl = document.getElementById("limit-editor-error");
  const editorForm = document.getElementById("limit-editor-form");
  const editorCancel = document.getElementById("limit-editor-cancel");
  let editorItemId = null;

  const fmt = (v) => `${Number(v).toFixed(2).replace(".", ",")} €`;
  const fmtTime = (iso) => {
    if (!iso) return "";
    const d = new Date(iso);
    if (isNaN(d)) return iso;
    const pad = (n) => String(n).padStart(2, "0");
    return `${pad(d.getDate())}.${pad(d.getMonth() + 1)}. ${pad(d.getHours())}:${pad(d.getMinutes())}`;
  };
  const escapeHtml = (s) => String(s).replace(/[&<>"']/g, c => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));

  function renderInventory(data) {
    // Alle Items kategorieübergreifend flach sammeln
    const flat = [];
    for (const cat of (data.categories || [])) {
      for (const it of (cat.items || [])) {
        flat.push({ ...it, category: cat.name });
      }
    }
    if (flat.length === 0) {
      inventoryEl.innerHTML = `<p class="overview__loading">Kein Bestand konfiguriert.</p>`;
      return;
    }

    // Sortierung: items mit critical-Wert zuerst (höchste Auslastung oben),
    // items ohne critical ans Ende.
    flat.sort((a, b) => {
      const aHas = typeof a.critical === "number";
      const bHas = typeof b.critical === "number";
      if (aHas && !bHas) return -1;
      if (!aHas && bHas) return 1;
      if (!aHas && !bHas) return b.sold - a.sold;
      const aPct = a.sold / Math.max(a.critical, 1);
      const bPct = b.sold / Math.max(b.critical, 1);
      return bPct - aPct;
    });

    const rows = flat.map(it => {
      const hasCritical = typeof it.critical === "number";
      const pct = hasCritical
        ? Math.min(100, Math.round((it.sold / Math.max(it.critical, 1)) * 100))
        : 0;
      let stateClass = "";
      if (it.status === "critical") stateClass = " inv-row--critical";
      else if (it.status === "warn") stateClass = " inv-row--warn";

      const count = hasCritical
        ? `<span class="inv-row__count">${it.sold}/${it.critical}</span>`
        : `<span class="inv-row__count inv-row__count--nomax">${it.sold}</span>`;
      const bar = hasCritical
        ? `<div class="inv-row__bar"><div class="inv-row__fill" style="width:${pct}%"></div></div>`
        : `<div class="inv-row__bar inv-row__bar--nomax"></div>`;

      let metaParts = [];
      metaParts.push(`<span class="inv-row__cat">${escapeHtml(it.category)}</span>`);
      if (hasCritical) {
        metaParts.push(`krit. ${it.critical}${it.warn != null ? ` · warn ${it.warn}` : ""}`);
      } else {
        metaParts.push("kein Limit");
      }
      if (it.status === "critical") {
        metaParts.push(`<span class="inv-row__tag inv-row__tag--crit">kritisch · ${it.remaining < 0 ? Math.abs(it.remaining) + " über Limit" : "0 frei"}</span>`);
      } else if (it.status === "warn") {
        metaParts.push(`<span class="inv-row__tag inv-row__tag--warn">nur noch ${it.remaining}</span>`);
      }

      return `
        <li class="inv-row${stateClass}" data-id="${escapeHtml(it.id)}"
            data-critical="${it.critical ?? ""}" data-warn="${it.warn ?? ""}"
            data-name="${escapeHtml(it.name)}">
          <span class="inv-row__name">${escapeHtml(it.name)}</span>
          ${count}
          <button type="button" class="inv-row__edit" aria-label="Limits bearbeiten">✎</button>
          ${bar}
          <span class="inv-row__meta">${metaParts.join(" · ")}</span>
        </li>`;
    }).join("");
    inventoryEl.innerHTML = `<ul class="inv-list inv-list--flat">${rows}</ul>`;
  }

  function renderOrders(orders) {
    if (!orders || orders.length === 0) {
      ordersEl.innerHTML = `<tr><td colspan="4" class="overview__loading">Noch keine Bestellungen.</td></tr>`;
      return;
    }
    ordersEl.innerHTML = orders.map(o => {
      const items = (o.items || []).map(i => `${i.quantity}× ${escapeHtml(i.name)}`).join(", ");
      const printer = o.printer_name ? escapeHtml(o.printer_name) : "–";
      return `
        <tr>
          <td>${fmtTime(o.created_at)}</td>
          <td>${printer}</td>
          <td class="orders-table__items">${items}</td>
          <td class="orders-table__right">${fmt(o.total)}</td>
        </tr>`;
    }).join("");
  }

  function renderStats(summary) {
    const t = summary.totals || {};
    statOrders.textContent = t.order_count ?? 0;
    statSubtotal.textContent = fmt(t.subtotal_sum ?? 0);
    statDeposit.textContent = fmt(t.deposit_sum ?? 0);
    statTotal.textContent = fmt(t.total_sum ?? 0);
  }

  async function refresh() {
    refreshBtn.disabled = true;
    try {
      const [invRes, ordRes, sumRes] = await Promise.all([
        fetch("/api/reports/inventory"),
        fetch("/api/reports/orders?limit=50"),
        fetch("/api/reports/summary"),
      ]);
      if (invRes.ok) renderInventory(await invRes.json());
      if (ordRes.ok) {
        const d = await ordRes.json();
        renderOrders(d.orders);
      }
      if (sumRes.ok) renderStats(await sumRes.json());
      const now = new Date();
      const pad = (n) => String(n).padStart(2, "0");
      updatedEl.textContent = `Stand: ${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`;
    } catch (err) {
      console.error("Refresh fehlgeschlagen", err);
    } finally {
      refreshBtn.disabled = false;
    }
  }

  // ── Editor ──────────────────────────────────────────────────────────
  function openEditor(itemId, name, critical, warn) {
    editorItemId = itemId;
    editorNameEl.textContent = name;
    editorCriticalEl.value = critical;
    editorWarnEl.value = warn;
    editorErrorEl.hidden = true;
    editorErrorEl.textContent = "";
    editorOverlay.hidden = false;
    editorCriticalEl.focus();
  }
  function closeEditor() {
    editorOverlay.hidden = true;
    editorItemId = null;
  }
  inventoryEl.addEventListener("click", (e) => {
    const btn = e.target.closest(".inv-row__edit");
    if (!btn) return;
    const row = btn.closest(".inv-row");
    if (!row) return;
    openEditor(
      row.dataset.id,
      row.dataset.name,
      row.dataset.critical,
      row.dataset.warn,
    );
  });
  editorCancel.addEventListener("click", closeEditor);
  editorOverlay.addEventListener("click", (e) => {
    if (e.target === editorOverlay) closeEditor();
  });
  editorForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!editorItemId) return;
    const critical = parseInt(editorCriticalEl.value, 10);
    const warn = parseInt(editorWarnEl.value, 10);
    if (isNaN(critical) || isNaN(warn)) {
      editorErrorEl.textContent = "Beide Werte müssen Zahlen sein.";
      editorErrorEl.hidden = false;
      return;
    }
    if (warn >= critical) {
      editorErrorEl.textContent = "Warnwert muss kleiner sein als der kritische Wert.";
      editorErrorEl.hidden = false;
      return;
    }
    try {
      const res = await fetch(`/api/menu/items/${encodeURIComponent(editorItemId)}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ critical, warn }),
      });
      const data = await res.json();
      if (!res.ok) {
        editorErrorEl.textContent = data.error || "Speichern fehlgeschlagen";
        editorErrorEl.hidden = false;
        return;
      }
      closeEditor();
      refresh();
    } catch (err) {
      editorErrorEl.textContent = "Netzwerkfehler";
      editorErrorEl.hidden = false;
    }
  });
  document.addEventListener("keydown", (e) => {
    if (e.key !== "Escape") return;
    if (!editorOverlay.hidden) closeEditor();
    else if (!resetDialog.hidden) closeResetDialog();
  });

  // ── Reset-Dialog ────────────────────────────────────────────────────
  function openResetDialog() {
    resetPasswordEl.value = "";
    resetErrorEl.hidden = true;
    resetErrorEl.textContent = "";
    resetDialog.hidden = false;
    resetPasswordEl.focus();
  }
  function closeResetDialog() {
    resetDialog.hidden = true;
  }
  resetBtn.addEventListener("click", openResetDialog);
  resetCancel.addEventListener("click", closeResetDialog);
  resetDialog.addEventListener("click", (e) => {
    if (e.target === resetDialog) closeResetDialog();
  });
  resetForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const pw = resetPasswordEl.value;
    if (!pw) {
      resetErrorEl.textContent = "Passwort eingeben.";
      resetErrorEl.hidden = false;
      return;
    }
    try {
      const res = await fetch("/api/admin/reset", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password: pw }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        resetErrorEl.textContent = data.error || `Fehler (${res.status})`;
        resetErrorEl.hidden = false;
        return;
      }
      closeResetDialog();
      refresh();
    } catch (err) {
      resetErrorEl.textContent = "Netzwerkfehler";
      resetErrorEl.hidden = false;
    }
  });

  refreshBtn.addEventListener("click", refresh);
  refresh();
  setInterval(refresh, 20000);
})();
