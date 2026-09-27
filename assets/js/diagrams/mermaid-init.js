(() => {
  const nodes = document.querySelectorAll(".mermaid-diagram pre.mermaid");

  if (nodes.length === 0) {
    return;
  }

  mermaid.initialize({
    startOnLoad: false,
    securityLevel: "strict",
    theme: "neutral",
  });

  mermaid.run({ nodes }).catch((error) => {
    console.error("Mermaid could not render a diagram; its source remains available below.", error);
  });
})();
