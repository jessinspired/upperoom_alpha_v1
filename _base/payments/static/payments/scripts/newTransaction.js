document.addEventListener("newTransaction", (e) => {
  const popup = new PaystackPop();

  popup.newTransaction({
    key: e.detail.key,
    email: e.detail.email,
    amount: e.detail.amount,
    reference: e.detail.reference,
    onSuccess: (transaction) => {
      window.location.replace(e.detail.redirect_url);
    },
    onLoad: (response) => {
      console.log("onLoad: ", response);
    },
    onCancel: () => {
      let abortUrl = e.detail.abort_url;
      let csrfToken = document
        .querySelector('meta[name="csrf-token"]')
        .getAttribute("content");
      htmx.ajax("POST", abortUrl, {
        headers: {
          "X-CSRFToken": csrfToken,
        },
        target: "#global-response-message-htmx",
        swap: "outerHTML",
      });
    },
    onError: (error) => {
      console.log("Error: ", error.message);
    },
  });
});
