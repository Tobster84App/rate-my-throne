// Inhaltsverzeichnis für lange Seiten (Startseite, Datenschutz).
// PC: Leiste mit allen Abschnitten, bleibt beim Scrollen oben. Handy: Knopf „☰ Inhalt“, der die Liste aufklappt.
// Der Abschnitt, in dem man gerade ist, wird hervorgehoben. Ausgeblendete Abschnitte erscheinen nicht.
function buildToc({ items, title, mount }) {
  const nav = document.createElement("nav");
  nav.className = "toc";
  nav.setAttribute("aria-label", title);
  const links = items.map(i => `<a href="#${i.id}" data-id="${i.id}">${i.label}</a>`).join("");
  nav.innerHTML = `<div class="toc-in">
      <div class="toc-bar">${links}</div>
      <button type="button" class="toc-btn" aria-expanded="false"><span aria-hidden="true">☰</span> <span class="toc-cur">${title}</span></button>
      <div class="toc-menu" hidden>${links}</div>
    </div>`;
  mount(nav);
  const btn = nav.querySelector(".toc-btn"), menu = nav.querySelector(".toc-menu"), cur = nav.querySelector(".toc-cur");
  const close = () => { menu.hidden = true; btn.setAttribute("aria-expanded", "false"); };
  btn.onclick = () => { menu.hidden = !menu.hidden; btn.setAttribute("aria-expanded", String(!menu.hidden)); };
  let clicked = null;   // zuletzt angetippter Eintrag (wichtig für kurze Abschnitte ganz unten)
  nav.addEventListener("click", e => { const a = e.target.closest("a[data-id]"); if (a) clicked = a.dataset.id; });
  menu.addEventListener("click", e => { if (e.target.closest("a")) close(); });
  document.addEventListener("click", e => { if (!nav.contains(e.target)) close(); });
  document.addEventListener("keydown", e => { if (e.key === "Escape") close(); });

  const target = id => document.getElementById(id);
  function update() {
    // Einträge zu ausgeblendeten Abschnitten verstecken (z. B. „Thron der Woche“, solange er nicht geladen ist)
    nav.querySelectorAll("a[data-id]").forEach(a => { const el = target(a.dataset.id); a.hidden = !el || !!el.closest("[hidden]"); });
    // Aktiver Abschnitt: der letzte, dessen Anfang schon oben unter der Leiste liegt
    const offset = nav.getBoundingClientRect().bottom + 24;
    let active = null;
    for (const i of items) {
      const el = target(i.id);
      if (el && !el.closest("[hidden]") && el.getBoundingClientRect().top <= offset) active = i;
    }
    // Ganz unten kann die Seite nicht weiter scrollen: dann den angetippten Abschnitt markieren, wenn er zu sehen ist
    const atBottom = innerHeight + scrollY >= document.documentElement.scrollHeight - 4;
    const c = clicked && target(clicked);
    if (atBottom && c && c.getBoundingClientRect().top < innerHeight) active = items.find(i => i.id === clicked);
    else if (!atBottom) clicked = null;
    nav.querySelectorAll("a[data-id]").forEach(a => a.classList.toggle("on", !!active && a.dataset.id === active.id));
    cur.textContent = active ? active.text : title;
    const on = nav.querySelector(".toc-bar a.on");
    if (on && !on.dataset.seen) {   // aktiven Eintrag in der Leiste sichtbar halten
      nav.querySelectorAll(".toc-bar a").forEach(a => delete a.dataset.seen);
      on.dataset.seen = "1";
      const bar = nav.querySelector(".toc-bar");
      if (bar.scrollWidth > bar.clientWidth) bar.scrollTo({ left: on.offsetLeft - 16, behavior: "smooth" });
    }
  }
  let tick = false;
  addEventListener("scroll", () => { if (!tick) { tick = true; requestAnimationFrame(() => { tick = false; update(); }); } }, { passive: true });
  addEventListener("resize", update);
  update();
  return { update };
}
