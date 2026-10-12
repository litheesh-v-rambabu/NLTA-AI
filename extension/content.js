(() => {
    const SKIP_TAGS = new Set(["SCRIPT", "STYLE", "NOSCRIPT", "TEXTAREA", "INPUT", "CODE", "PRE"]);
    const margin = window.innerHeight; // one extra screen above and below
  
    function isNearViewport(el) {
      const rect = el.getBoundingClientRect();
      if (rect.width === 0 && rect.height === 0) return false; // display:none or collapsed
      return rect.bottom > -margin && rect.top < window.innerHeight + margin;
    }
  
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
      acceptNode(node) {
        const text = node.nodeValue.trim();
        if (text.length < 2) return NodeFilter.FILTER_REJECT;
        if (!/\p{L}/u.test(text)) return NodeFilter.FILTER_REJECT;
        const parent = node.parentElement;
        if (!parent) return NodeFilter.FILTER_REJECT;
        if (SKIP_TAGS.has(parent.tagName.toUpperCase())) return NodeFilter.FILTER_REJECT;
        if (parent.isContentEditable) return NodeFilter.FILTER_REJECT;
        if (!isNearViewport(parent)) return NodeFilter.FILTER_REJECT;
        if (!parent.checkVisibility({ visibilityProperty: true, opacityProperty: true })) return NodeFilter.FILTER_REJECT;
        return NodeFilter.FILTER_ACCEPT;
      },
    });
  
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
  
    return {
      count: nodes.length,
      sample: nodes.slice(0, 5).map((n) => n.nodeValue.trim().slice(0, 40)),
    };
  })();