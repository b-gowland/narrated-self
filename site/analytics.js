// Plausible visit counts (no cookies, no personal data). Kept out of index.html because the CSP blocks inline scripts.
// Not loaded at all for players who chose "Don't record my guesses".
(() => {
  let optedOut = false;
  try { optedOut = localStorage.getItem("tns-optout") === "1"; } catch {}
  if (optedOut) return;
  window.plausible = window.plausible || function () { (plausible.q = plausible.q || []).push(arguments); };
  plausible.init = plausible.init || function (i) { plausible.o = i || {}; };
  plausible.init();
  const s = document.createElement("script");
  s.async = true;
  s.src = "https://plausible.io/js/pa-CACYAMslGoZmmPqy26tTs.js";
  document.head.append(s);
})();
