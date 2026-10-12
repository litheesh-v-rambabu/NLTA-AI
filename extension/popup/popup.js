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
