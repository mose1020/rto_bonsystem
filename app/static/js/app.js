(() => {
  const cart = new Map(); // id -> {id, name, price, deposit, quantity}
  let tendered = null;    // null oder Zahl in EUR

  const list = document.getElementById("cart-list");
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
  const printerStatus = document.getElementById("printer-status");

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
      const depositHint = deposit > 0
        ? `<small class="cart__deposit-hint">inkl. ${fmt(deposit)} Pfand</small>`
        : "";
      li.innerHTML = `
        <button class="qty" type="button" aria-label="weniger" data-act="dec" data-id="${id}">−</button>
        <div>
          <div class="cart__name">${name}</div>
          <small>${fmt(unitTotal)} × ${quantity}</small>
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
    // Buttons-Highlight aktualisieren
    tenderButtons.forEach((b) => {
      const v = parseFloat(b.dataset.value);
      b.classList.toggle("btn-tender--active", tendered !== null && v === tendered);
    });
    // Custom-Input nur leeren, wenn die Aktion vom Button kam
    if (source === "button") {
      tenderCustom.value = "";
    } else if (source === "clear") {
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
      // Zweiter Klick auf den gleichen Wert hebt ihn auf
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
      }
    } catch (err) {
      feedback.textContent = `Netzwerkfehler: ${err.message}`;
      feedback.className = "cart__feedback cart__feedback--error";
    } finally {
      submitBtn.disabled = cart.size === 0;
    }
  });

  async function pollPrinter() {
    try {
      const res = await fetch("/api/health/printer");
      if (res.ok) {
        printerStatus.textContent = "Drucker: bereit";
        printerStatus.className = "status status--ok";
      } else {
        printerStatus.textContent = "Drucker: offline";
        printerStatus.className = "status status--error";
      }
    } catch {
      printerStatus.textContent = "Drucker: ?";
      printerStatus.className = "status status--error";
    }
  }
  pollPrinter();
  setInterval(pollPrinter, 15000);

  render();
})();
