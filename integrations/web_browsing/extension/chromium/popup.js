"use strict";
const input = document.getElementById("conversation"), status = document.getElementById("status");
document.getElementById("openConversation").addEventListener("click", () => chrome.runtime.sendMessage({type:"OPEN_CHATGPT_CONVERSATION",url:input.value.trim()}, r => {status.textContent = r?.ok ? "Opening conversation…" : (r?.error || "Could not open link.");}));
document.getElementById("newChat").addEventListener("click", () => chrome.runtime.sendMessage({type:"OPEN_CHATGPT_PROMPT",prompt:"Start a new chat."}, r => {status.textContent = r?.ok ? "Opening ChatGPT…" : (r?.error || "Could not open ChatGPT.");}));
