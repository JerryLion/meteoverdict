// Czech and English texts of the web pages (roadmap 4.6). Model names come from
// meta.json and are not translated.

export const STRINGS = {
  cs: {
    "page.compare": "Porovnání modelů",
    "page.map": "Mapa",
    "page.forecast": "Předpověď",
    "control.okres": "Okres",
    "forecast.title": "Předpověď",
    "forecast.titleFor": "Předpověď pro okres {okres}",
    "forecast.note":
      "Naše předpověď kombinuje aktuální předpovědi všech modelů: každý model má váhu podle toho, jak přesný byl v tomto okrese za posledních 90 dní, a teplotu a vítr opravujeme o jeho průměrnou chybu. S málo dny se váhy blíží prostému průměru. Zda kombinace poráží nejlepší model, teprve ověřujeme.",
    "forecast.loading": "Načítám předpovědi modelů…",
    "forecast.unavailable": "Předpovědi z Open-Meteo se nepodařilo načíst; zkuste to později.",
    "forecast.noWeights": "Pro tento okres zatím nejsou skóre, ze kterých by šly spočítat váhy.",
    "forecast.col.day": "Den",
    "forecast.col.tmin": "Min. °C",
    "forecast.col.tmax": "Max. °C",
    "forecast.col.precipitation": "Srážky mm",
    "forecast.col.wind": "Vítr max. m/s",
    "forecast.temperature_2m": "Teplota (2 m)",
    "forecast.precipitation": "Srážky za hodinu",
    "forecast.wind_speed_10m": "Vítr (10 m)",
    "forecast.legend": "Černě naše kombinace, barevně nejlepší model v okrese ({best}), šedě ostatní modely; přerušovaná čára je teď.",
    "forecast.weights": "Které modely tu mají největší váhu",
    "forecast.weightsNote": "Váhy pro zítřek (D+1); pro další dny se liší podle přesnosti modelů na delší předstih.",
    "forecast.variable": "Veličina",
    "forecast.top": "Největší váhy",
    "forecast.link": "Předpověď pro okres",
    "status.none": "Zatím žádná skóre: mapa se plní, jak se doplňuje historie.",
    "status.scores": "Skóre do {asOf} · aktualizováno {updated}",
    "control.variable": "Veličina",
    "control.lead": "Předstih",
    "control.window": "Období",
    "variable.temperature_2m": "Teplota (2 m)",
    "variable.temperature_2m_hourly": "Teplota (2 m), každá hodina modelu (bez pořadí)",
    "variable.wind_speed_10m_hourly": "Vítr (10 m), každá hodina modelu (bez pořadí)",
    "variable.temperature_2m_06utc": "Teplota v 06 UTC (noc)",
    "variable.temperature_2m_12utc": "Teplota ve 12 UTC (odpoledne)",
    "variable.temperature_max": "Denní maximum teploty",
    "variable.wind_speed_10m": "Vítr (10 m)",
    "variable.precipitation_24h": "Srážky za 24 h (06–06 UTC, se srážkoměry)",
    "variable.precipitation_daily": "Srážky za den (UTC)",
    "window.90d": "Posledních 90 dní",
    "window.season": "Tato sezóna",
    "window.all": "Celé období",
    "window.djf": "Všechny zimy",
    "window.mam": "Všechna jara",
    "window.jja": "Všechna léta",
    "window.son": "Všechny podzimy",
    "legend.tooFew": "příliš málo stanic",
    "legend.noData": "bez dat",
    "describe.noData": "bez dat",
    "describe.tooFew": "příliš málo stanic pro pořadí",
    "describe.best": "nejlepší: {model} (MAE {mae}{how}){tied}",
    "describe.unranked": ", nejnižší MAE, bez testu významnosti",
    "describe.tied": "; ne významně horší: {models}",
    "describe.borrowed": "; stanice ze sousedních okresů: {n}",
    "chart.close": "Zavřít graf",
    "chart.y": "MAE (7denní průměr)",
    "chart.leadNote": "Denní chyby se zveřejňují jen pro D+1 a D+2.",
    "chart.empty": "Pro tuto stanici a veličinu nejsou za posledních 90 dní žádné denní chyby.",
    "compare.ranking": "Pořadí pro Česko",
    "compare.rankingNote":
      "Střední absolutní chyba (MAE), bias (předpověď minus měření) a RMSE na stanicích a ve dnech, které pokrývají všechny modely. „≈“ značí modely, jejichž rozdíl MAE od nejlepšího není významný (95% bootstrapový interval přes dny). Průměr všech modelů je srovnávací základ, nemá pořadí.",
    "compare.bias": "Bias podle nadmořské výšky",
    "compare.biasNote": "Kladný: model předpovídá příliš vysoké hodnoty, např. příliš teplo na horách.",
    "compare.empty": "Pro tuto volbu zatím nejsou žádná skóre.",
    "compare.best": "nejlepší",
    "compare.interval": "({low} až {high})",
    "model.blend": "Průměr všech modelů",
    "table.rank": "#",
    "table.model": "Model",
    "table.mae": "MAE",
    "table.diff": "oproti nejlepšímu (95% interval)",
    "table.bias": "Bias",
    "table.rmse": "RMSE",
    "table.stations": "Stanic",
    "table.days": "Dní",
    "elevation.lowland": "Nížiny (< 400 m)",
    "elevation.upland": "Pahorkatiny (400–800 m)",
    "elevation.mountain": "Hory (> 800 m)",
    "footer.observations": "Pozorování",
    "footer.forecasts": "Předpovědi",
    "footer.boundaries": "Hranice",
    "footer.scores": "Skóre",
    "footer.method": "Zdroj a metoda",
    "language.switch": "English",
  },
  en: {
    "page.compare": "Compare models",
    "page.map": "Map",
    "page.forecast": "Forecast",
    "control.okres": "Okres",
    "forecast.title": "Forecast",
    "forecast.titleFor": "Forecast for okres {okres}",
    "forecast.note":
      "Our forecast combines the current forecasts of all models: each model is weighted by how accurate it was in this okres over the last 90 days, and temperature and wind are corrected by its mean error there. With few days the weights stay close to a plain mean. Whether the combination beats the best model is still being checked.",
    "forecast.loading": "Loading the model forecasts…",
    "forecast.unavailable": "Could not load the forecasts from Open-Meteo; try again later.",
    "forecast.noWeights": "No scores for this okres yet to weight the models with.",
    "forecast.col.day": "Day",
    "forecast.col.tmin": "Min °C",
    "forecast.col.tmax": "Max °C",
    "forecast.col.precipitation": "Rain mm",
    "forecast.col.wind": "Max wind m/s",
    "forecast.temperature_2m": "Temperature (2 m)",
    "forecast.precipitation": "Precipitation per hour",
    "forecast.wind_speed_10m": "Wind (10 m)",
    "forecast.legend": "Black: our combination; colour: the best model in this okres ({best}); grey: the other models; dashed line: now.",
    "forecast.weights": "Which models count most here",
    "forecast.weightsNote": "Weights for tomorrow (D+1); later days differ with each model's accuracy at longer lead times.",
    "forecast.variable": "Variable",
    "forecast.top": "Largest weights",
    "forecast.link": "Forecast for this okres",
    "status.none": "No scores yet: the map fills as the history is backfilled.",
    "status.scores": "Scores up to {asOf} · updated {updated}",
    "control.variable": "Variable",
    "control.lead": "Lead time",
    "control.window": "Period",
    "variable.temperature_2m": "Temperature (2 m)",
    "variable.temperature_2m_hourly": "Temperature (2 m), every model hour (not ranked)",
    "variable.wind_speed_10m_hourly": "Wind (10 m), every model hour (not ranked)",
    "variable.temperature_2m_06utc": "Temperature at 06 UTC (night)",
    "variable.temperature_2m_12utc": "Temperature at 12 UTC (afternoon)",
    "variable.temperature_max": "Daily maximum temperature",
    "variable.wind_speed_10m": "Wind (10 m)",
    "variable.precipitation_24h": "Precipitation, 24 h (06-06 UTC, with rain gauges)",
    "variable.precipitation_daily": "Precipitation, UTC day",
    "window.90d": "Last 90 days",
    "window.season": "This season",
    "window.all": "All time",
    "window.djf": "All winters",
    "window.mam": "All springs",
    "window.jja": "All summers",
    "window.son": "All autumns",
    "legend.tooFew": "too few stations",
    "legend.noData": "no data",
    "describe.noData": "no data",
    "describe.tooFew": "too few stations to rank",
    "describe.best": "best: {model} (MAE {mae}{how}){tied}",
    "describe.unranked": ", lowest MAE, no significance test",
    "describe.tied": "; not significantly worse: {models}",
    "describe.borrowed": "; stations from neighbouring okresy: {n}",
    "chart.close": "Close the chart",
    "chart.y": "MAE (7-day mean)",
    "chart.leadNote": "Daily errors are published for D+1 and D+2 only.",
    "chart.empty": "No daily errors for this station and variable in the last 90 days.",
    "compare.ranking": "Ranking for Czechia",
    "compare.rankingNote":
      'Mean absolute error (MAE), bias (forecast minus observed) and RMSE over the stations and days every model covers. "≈" marks models whose MAE difference from the best is not significant (95 % bootstrap interval over days). The mean of all models is a baseline, not ranked.',
    "compare.bias": "Bias by elevation",
    "compare.biasNote": "Positive: the model forecasts too high, e.g. too warm in the mountains.",
    "compare.empty": "No scores for this choice yet.",
    "compare.best": "best",
    "compare.interval": "({low} to {high})",
    "model.blend": "Mean of all models",
    "table.rank": "#",
    "table.model": "Model",
    "table.mae": "MAE",
    "table.diff": "vs best (95 % interval)",
    "table.bias": "Bias",
    "table.rmse": "RMSE",
    "table.stations": "Stations",
    "table.days": "Days",
    "elevation.lowland": "Lowland (< 400 m)",
    "elevation.upland": "Upland (400-800 m)",
    "elevation.mountain": "Mountain (> 800 m)",
    "footer.observations": "Observations",
    "footer.forecasts": "Forecasts",
    "footer.boundaries": "Boundaries",
    "footer.scores": "Scores",
    "footer.method": "Source and method",
    "language.switch": "Česky",
  },
};

export const LANGUAGES = Object.keys(STRINGS);

/** The stored choice if valid, else Czech for Czech and Slovak browsers, else English. */
export function pickLanguage(stored, browserLanguage) {
  if (LANGUAGES.includes(stored)) return stored;
  return /^(cs|sk)\b/i.test(browserLanguage ?? "") ? "cs" : "en";
}

/** t(key, {name: value}) in one language, falling back to English, then to the key. */
export function translator(language) {
  const strings = STRINGS[language] ?? STRINGS.en;
  return (key, params = {}) =>
    (strings[key] ?? STRINGS.en[key] ?? key).replace(/\{(\w+)\}/g, (_, name) =>
      String(params[name] ?? ""),
    );
}

const STORAGE_KEY = "meteoverdict.language";

// the choice is a per-browser convenience; storage may be unavailable
export function storedLanguage() {
  try {
    return window.localStorage.getItem(STORAGE_KEY);
  } catch {
    return null;
  }
}

function storeLanguage(language) {
  try {
    window.localStorage.setItem(STORAGE_KEY, language);
  } catch {
    // keep working without storage
  }
}

/** Language of this page view; sets <html lang>, the [data-i18n] texts and the switch. */
export function setUpLanguage() {
  const language = pickLanguage(storedLanguage(), navigator.language);
  const t = translator(language);
  document.documentElement.lang = language;
  for (const element of document.querySelectorAll("[data-i18n]")) {
    element.textContent = t(element.dataset.i18n);
  }
  for (const element of document.querySelectorAll("[data-i18n-aria]")) {
    element.setAttribute("aria-label", t(element.dataset.i18nAria));
  }
  const toggle = document.getElementById("language");
  if (toggle) {
    toggle.textContent = t("language.switch");
    toggle.addEventListener("click", () => {
      storeLanguage(language === "cs" ? "en" : "cs");
      window.location.reload();
    });
  }
  return t;
}
