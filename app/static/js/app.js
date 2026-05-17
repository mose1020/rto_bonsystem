(() => {
  // ── Printer-Bar (immer da, Bestell- und Übersichts-Seite) ───────────
  const printerStatus = document.getElementById("printer-status");
  const printerSelect = document.getElementById("printer-select");
  const STORAGE_KEY = "bonsystem.printerId";

  if (printerSelect) {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      const exists = Array.from(printerSelect.options).some(o => o.value === stored);
      if (exists) printerSelect.value = stored;
    }
    printerSelect.addEventListener("change", () => {
      localStorage.setItem(STORAGE_KEY, printerSelect.value);
      pollPrinter();
    });
  }

  function currentPrinterId() {
    return printerSelect ? printerSelect.value : null;
  }

  async function pollPrinter() {
    if (!printerStatus) return;
    const id = currentPrinterId();
    const url = id ? `/api/health/printer/${encodeURIComponent(id)}` : "/api/health/printer";
    try {
      const res = await fetch(url);
      if (res.ok) {
        printerStatus.textContent = "bereit";
        printerStatus.className = "status status--ok";
        printerStatus.title = "Drucker erreichbar";
      } else {
        const data = await res.json().catch(() => ({}));
        printerStatus.textContent = "offline";
        printerStatus.className = "status status--error";
        printerStatus.title = data.error || "Drucker nicht erreichbar";
      }
    } catch {
      printerStatus.textContent = "?";
      printerStatus.className = "status status--error";
      printerStatus.title = "Status unbekannt";
    }
  }
  if (printerStatus) {
    pollPrinter();
    setInterval(pollPrinter, 15000);
  }

  // ── Cart-Logik nur auf der Bestell-Seite ────────────────────────────
  const list = document.getElementById("cart-list");
  if (!list) return;  // wir sind auf der Übersicht (oder einer anderen Seite)

  // ── Live-Bestand: Produktkarten anhand /api/reports/inventory einfärben
  async function refreshInventoryStatus() {
    try {
      const res = await fetch("/api/reports/inventory");
      if (!res.ok) return;
      const data = await res.json();
      const statusById = {};
      for (const cat of data.categories || []) {
        for (const it of cat.items || []) statusById[it.id] = it;
      }
      document.querySelectorAll(".product").forEach((btn) => {
        const id = btn.dataset.id;
        const info = statusById[id];
        btn.classList.remove("product--warn", "product--critical");
        // Bestehender Badge wird durch Status-Badge ersetzt
        const existing = btn.querySelector(".product__stock");
        if (existing) existing.remove();
        if (!info || !info.critical) return;
        if (info.status === "critical") {
          btn.classList.add("product--critical");
          appendStockBadge(btn, `nur noch ${Math.max(0, info.remaining)}`, "critical");
        } else if (info.status === "warn") {
          btn.classList.add("product--warn");
          appendStockBadge(btn, `noch ${info.remaining}`, "warn");
        }
      });
    } catch (err) {
      // still – Bestand ist nice-to-have
    }
  }
  function appendStockBadge(btn, text, kind) {
    // Badge inline in die Preis-Zeile einhängen (flex-wrap), damit es
    // nicht mit dem Artikelnamen kollidieren kann.
    const priceEl = btn.querySelector(".product__price") || btn;
    const span = document.createElement("span");
    span.className = `product__stock product__stock--${kind}`;
    span.textContent = text;
    priceEl.appendChild(span);
  }
  refreshInventoryStatus();
  setInterval(refreshInventoryStatus, 20000);

  const cart = new Map(); // id -> {id, name, price, deposit, quantity}
  let tendered = null;    // null oder Zahl in EUR

  const subtotalEl = document.getElementById("cart-subtotal");
  const subtotalRow = document.getElementById("cart-subtotal-row");
  const depositEl = document.getElementById("cart-deposit");
  const depositRow = document.getElementById("cart-deposit-row");
  const totalEl = document.getElementById("cart-total");
  const changeEl = document.getElementById("cart-change");
  const changeRow = document.getElementById("cart-change-row");
  const feedback = document.getElementById("cart-feedback");
  const submitBtn = document.getElementById("cart-submit");
  const clearBtn = document.getElementById("cart-clear");
  const tenderButtons = document.querySelectorAll(".btn-tender");
  const tenderCustom = document.getElementById("cart-tendered-custom");
  const tenderClear = document.getElementById("cart-tendered-clear");

  const fmt = (v) => `${v.toFixed(2).replace(".", ",")} €`;

  function currentTotal() {
    let total = 0;
    for (const { price, deposit, quantity } of cart.values()) {
      total += (price + deposit) * quantity;
    }
    return total;
  }

  function render() {
    list.innerHTML = "";
    let subtotal = 0;
    let depositTotal = 0;
    for (const { id, name, price, deposit, quantity } of cart.values()) {
      subtotal += price * quantity;
      depositTotal += deposit * quantity;
      const li = document.createElement("li");
      li.className = "cart__row";
      const unitTotal = price + deposit;
      const isGratis = unitTotal === 0;
      const depositHint = deposit > 0
        ? `<small class="cart__deposit-hint">inkl. ${fmt(deposit)} Pfand</small>`
        : "";
      const priceLine = isGratis
        ? `<small class="cart__gratis-tag">GRATIS × ${quantity}</small>`
        : `<small>${fmt(unitTotal)} × ${quantity}</small>`;
      li.innerHTML = `
        <button class="qty" type="button" aria-label="weniger" data-act="dec" data-id="${id}">−</button>
        <div>
          <div class="cart__name">${name}</div>
          ${priceLine}
          ${depositHint}
        </div>
        <button class="qty" type="button" aria-label="mehr" data-act="inc" data-id="${id}">+</button>
      `;
      list.appendChild(li);
    }
    const total = subtotal + depositTotal;
    const hasDeposit = depositTotal > 0;
    subtotalEl.textContent = fmt(subtotal);
    depositEl.textContent = fmt(depositTotal);
    subtotalRow.hidden = !hasDeposit;
    depositRow.hidden = !hasDeposit;
    totalEl.textContent = fmt(total);
    submitBtn.disabled = cart.size === 0;
    renderChange(total);
  }

  function renderChange(total) {
    if (tendered === null || isNaN(tendered)) {
      changeRow.hidden = true;
      changeRow.classList.remove("cart__row-total--short");
      return;
    }
    const diff = tendered - total;
    changeRow.hidden = false;
    if (diff < 0) {
      changeEl.textContent = `fehlt ${fmt(Math.abs(diff))}`;
      changeRow.classList.add("cart__row-total--short");
    } else {
      changeEl.textContent = fmt(diff);
      changeRow.classList.remove("cart__row-total--short");
    }
  }

  function setTendered(value, { source } = {}) {
    if (value === null || value === undefined || value === "" || isNaN(value) || value < 0) {
      tendered = null;
    } else {
      tendered = Number(value);
    }
    tenderButtons.forEach((b) => {
      const v = parseFloat(b.dataset.value);
      b.classList.toggle("btn-tender--active", tendered !== null && v === tendered);
    });
    if (source === "button" || source === "clear") {
      tenderCustom.value = "";
    }
    renderChange(currentTotal());
  }

  function add(id, name, price, deposit) {
    const existing = cart.get(id);
    if (existing) existing.quantity += 1;
    else cart.set(id, { id, name, price, deposit, quantity: 1 });
    render();
  }

  function bump(id, delta) {
    const entry = cart.get(id);
    if (!entry) return;
    entry.quantity += delta;
    if (entry.quantity <= 0) cart.delete(id);
    render();
  }

  document.querySelectorAll(".product").forEach((btn) => {
    btn.addEventListener("click", () => {
      add(
        btn.dataset.id,
        btn.dataset.name,
        parseFloat(btn.dataset.price),
        parseFloat(btn.dataset.deposit || "0"),
      );
    });
  });

  list.addEventListener("click", (e) => {
    const t = e.target.closest("button[data-act]");
    if (!t) return;
    bump(t.dataset.id, t.dataset.act === "inc" ? 1 : -1);
  });

  tenderButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const value = parseFloat(btn.dataset.value);
      if (tendered === value) setTendered(null, { source: "clear" });
      else setTendered(value, { source: "button" });
    });
  });

  tenderCustom.addEventListener("input", () => {
    const v = parseFloat(tenderCustom.value);
    setTendered(isNaN(v) ? null : v, { source: "custom" });
  });

  tenderClear.addEventListener("click", () => {
    setTendered(null, { source: "clear" });
  });

  clearBtn.addEventListener("click", () => {
    cart.clear();
    setTendered(null, { source: "clear" });
    feedback.textContent = "";
    feedback.className = "cart__feedback";
    render();
  });

  submitBtn.addEventListener("click", async () => {
    submitBtn.disabled = true;
    feedback.textContent = "Sende Bestellung …";
    feedback.className = "cart__feedback";
    try {
      const res = await fetch("/api/orders", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          items: [...cart.values()].map(({ id, quantity }) => ({ id, quantity })),
          tendered: tendered,
          printer_id: currentPrinterId(),
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        feedback.textContent = data.error || data.print_error || "Fehler";
        feedback.className = "cart__feedback cart__feedback--error";
      } else {
        feedback.textContent = `Gedruckt: ${data.order.id}`;
        feedback.className = "cart__feedback cart__feedback--ok";
        cart.clear();
        setTendered(null, { source: "clear" });
        render();
        refreshInventoryStatus();  // Bestand direkt nach Druck aktualisieren
      }
    } catch (err) {
      feedback.textContent = `Netzwerkfehler: ${err.message}`;
      feedback.className = "cart__feedback cart__feedback--error";
    } finally {
      submitBtn.disabled = cart.size === 0;
    }
  });

  render();
})();
