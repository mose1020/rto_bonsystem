(() => {
  const cart = new Map(); // id -> {id, name, price, quantity}
  const list = document.getElementById("cart-list");
  const totalEl = document.getElementById("cart-total");
  const feedback = document.getElementById("cart-feedback");
  const submitBtn = document.getElementById("cart-submit");
  const clearBtn = document.getElementById("cart-clear");
  const noteEl = document.getElementById("cart-note");
  const printerStatus = document.getElementById("printer-status");

  const fmt = (v) => `${v.toFixed(2).replace(".", ",")} €`;

  function render() {
    list.innerHTML = "";
    let total = 0;
    for (const { id, name, price, quantity } of cart.values()) {
      total += price * quantity;
      const li = document.createElement("li");
      li.className = "cart__row";
      li.innerHTML = `
        <button class="qty" type="button" aria-label="weniger" data-act="dec" data-id="${id}">−</button>
        <div><div>${name}</div><small>${fmt(price)} × ${quantity}</small></div>
        <button class="qty" type="button" aria-label="mehr" data-act="inc" data-id="${id}">+</button>
      `;
      list.appendChild(li);
    }
    totalEl.textContent = fmt(total);
    submitBtn.disabled = cart.size === 0;
  }

  function add(id, name, price) {
    const existing = cart.get(id);
    if (existing) existing.quantity += 1;
    else cart.set(id, { id, name, price, quantity: 1 });
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
      add(btn.dataset.id, btn.dataset.name, parseFloat(btn.dataset.price));
    });
  });

  list.addEventListener("click", (e) => {
    const t = e.target.closest("button[data-act]");
    if (!t) return;
    bump(t.dataset.id, t.dataset.act === "inc" ? 1 : -1);
  });

  clearBtn.addEventListener("click", () => {
    cart.clear();
    noteEl.value = "";
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
          note: noteEl.value,
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
        noteEl.value = "";
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
