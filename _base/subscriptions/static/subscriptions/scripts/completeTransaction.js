document.addEventListener("completeTransaction", (e) => {
  const popup = new PaystackPop();
  popup.resumeTransaction(e.detail.access_code);
});
