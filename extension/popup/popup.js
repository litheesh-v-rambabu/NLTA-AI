const BACKEND_URL = "http://localhost:8000";

const button = document.getElementById("check");
const status = document.getElementById("status");

button.addEventListener("click", async () => {
  status.textContent = "Checking...";
  try {
    const response = await fetch(`${BACKEND_URL}/health`);
    if (!response.ok) throw new Error(`Server answered ${response.status}`);
    const data = await response.json();
    status.textContent = `Server is ${data.status}.`;
  } catch (err) {
    status.textContent = `Cannot reach the server: ${err.message}`;
  }
});
document.getElementById("scan").addEventListener("click", async () => {
  const out = document.getElementById("scan-result");
  out.textContent = "Scanning...";
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const [{ result }] = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      files: ["content.js"],
    });
    out.textContent = `Found ${result.count} text pieces. First: ${result.sample.join(" | ")}`;
  } catch (err) {
    out.textContent = `Scan failed: ${err.message}`;
  }
});
document.getElementById("translate").addEventListener("click", async () => {
  const out = document.getElementById("translate-result");
  const target = document.getElementById("target").value;
  out.textContent = "Finding text...";
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    // 1. Collect the visible text on the page.
    const [{ result }] = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      files: ["content.js"],
    });
    if (!result.texts.length) {
      out.textContent = "No text found on this page.";
      return;
    }

    // 2. Send it to your server for translation.
    out.textContent = `Translating ${result.texts.length} pieces... (the first time can take a while)`;
    const response = await fetch(`${BACKEND_URL}/translate/batch`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ texts: result.texts, target_lang: target }),
    });
    if (!response.ok) throw new Error(`Server answered ${response.status}`);
    const data = await response.json();

    // 3. Write the translations back into the same text nodes.
    await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: (translations) => {
        const { nodes, originals } = window.__nlta;
        nodes.forEach((node, i) => {
          const lead = originals[i].match(/^\s*/)[0];
          const trail = originals[i].match(/\s*$/)[0];
          node.nodeValue = lead + translations[i] + trail;
        });
      },
      args: [data.translations],
    });

    out.textContent = `Translated ${data.translations.length} pieces from ${data.source_lang} to ${data.target_lang}.`;
  } catch (err) {
    out.textContent = `Translate failed: ${err.message}`;
  }
});