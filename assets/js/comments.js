(() => {
  const container = document.querySelector('.giscus');
  if (!container) return;

  const theme = () => document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light';
  const script = document.createElement('script');
  script.src = 'https://giscus.app/client.js';
  script.async = true;
  script.crossOrigin = 'anonymous';
  Object.assign(script.dataset, container.dataset, { theme: theme() });
  container.appendChild(script);

  new MutationObserver(() => {
    container.querySelector('iframe')?.contentWindow?.postMessage(
      { giscus: { setConfig: { theme: theme() } } },
      'https://giscus.app'
    );
  }).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
})();
