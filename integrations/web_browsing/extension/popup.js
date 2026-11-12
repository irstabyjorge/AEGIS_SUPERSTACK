const page = document.getElementById("page");
let tabInfo = null;

(async () => {
  const [tab] = await chrome.tabs.query({active: true, currentWindow: true});
  if (!tab || !/^https?:$/.test(new URL(tab.url || "about:blank").protocol)) {
    page.textContent = "Open a public HTTP(S) page first.";
    return;
  }
  tabInfo = {url: tab.url, title: tab.title || tab.url};
  page.textContent = tabInfo.title + " — " + tabInfo.url;
})();

document.getElementById("research").addEventListener("click", () => {
  if (!tabInfo) return;
  const prompt = "Please research this public webpage. Summarize its key claims, assess source reliability, and cite supporting sources.\n\nTitle: " + tabInfo.title + "\nURL: " + tabInfo.url;
  chrome.tabs.create({url: "https://chatgpt.com/?q=" + encodeURIComponent(prompt)});
});
