(() => {
  const config = window.AYUVAN_LEGAL || {};
  document.querySelectorAll("[data-legal]").forEach((element) => {
    const value = config[element.dataset.legal];
    if (!value) return;
    if (element.dataset.legal.endsWith("Email")) {
      element.textContent = value;
      element.href = `mailto:${value}`;
    } else {
      element.textContent = value;
    }
  });
  document.querySelectorAll("[data-year]").forEach((element) => {
    element.textContent = new Date().getFullYear();
  });
})();
