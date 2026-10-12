import "./style.css";

import { setUpLanguage } from "./i18n.js";
import { displayName } from "./tv.js";

const t = setUpLanguage();

async function get(path, as = "json") {
  try {
    const response = await fetch(path);
    if (!response.ok) return null;
    return as === "json" ? await response.json() : await response.text();
  } catch {
    return null;
  }
}

async function main() {
  const index = await get("api/v1/index.json");
  const status = document.getElementById("status");
  const select = document.getElementById("okres");
  if (!index) {
    status.textContent = t("api.none");
    select.disabled = true;
    return;
  }
  status.textContent = t("tv.updated", {
    time: new Intl.DateTimeFormat(document.documentElement.lang, {
      dateStyle: "short", timeStyle: "short", timeZone: "Europe/Prague",
    }).format(new Date(index.generated)),
  });
  const okresy = index.okresy.slice().sort((a, b) => displayName(a.name).localeCompare(displayName(b.name), "cs"));
  select.replaceChildren(
    ...okresy.map((o) => Object.assign(document.createElement("option"), { value: o.code, textContent: `${displayName(o.name)} (${o.code})` })),
  );
  async function show(code) {
    const okres = okresy.find((o) => o.code === code);
    const links = document.getElementById("links");
    links.replaceChildren(
      ...[["JSON", okres.json], ["CSV", okres.csv]].map(([label, href]) => {
        const li = document.createElement("li");
        const a = Object.assign(document.createElement("a"), { href, textContent: href });
        li.append(`${label}: `, a);
        return li;
      }),
    );
    const csv = await get(`api/v1/okresy/${code}.csv`, "text");
    document.getElementById("preview").textContent = csv ? `${csv.split("\n").slice(0, 8).join("\n")}\n…` : "";
    window.history.replaceState(null, "", `#${code}`);
  }
  const wanted = window.location.hash.slice(1);
  select.value = okresy.some((o) => o.code === wanted) ? wanted : (okresy.find((o) => o.code === "CZ0100") ?? okresy[0]).code;
  select.addEventListener("change", () => show(select.value));
  await show(select.value);
}

main();
