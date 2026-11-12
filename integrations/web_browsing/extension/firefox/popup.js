"use strict";
const input=document.getElementById("conversation"),status=document.getElementById("status");
document.getElementById("openConversation").addEventListener("click",async()=>{try{const r=await browser.runtime.sendMessage({type:"OPEN_CHATGPT_CONVERSATION",url:input.value.trim()});status.textContent=r?.ok?"Opening conversation…":(r?.error||"Could not open link.");}catch{status.textContent="Could not open link."; }});
document.getElementById("newChat").addEventListener("click",async()=>{try{const r=await browser.runtime.sendMessage({type:"OPEN_CHATGPT_PROMPT",prompt:"Start a new chat."});status.textContent=r?.ok?"Opening ChatGPT…":(r?.error||"Could not open ChatGPT.");}catch{status.textContent="Could not open ChatGPT."; }});
