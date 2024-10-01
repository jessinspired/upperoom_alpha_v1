document.addEventListener("DOMContentLoaded", (e) => {
  let roleTabBtns = document.querySelectorAll(".roles-tab-container > *");

  console.log(roleTabBtns);
  roleTabBtns.forEach((btn) => {
    btn.addEventListener("click", (e) => {
      if (btn.classList.contains("active")) {
        return;
      }
      let activeBtn = document.querySelector(".roles-tab-container > .active");
      let activeArticle = document.querySelector(".roles-article > .active");

      let currentRole = btn.getAttribute("data-role");
      let currentArticle = document.querySelector(
        `ol[data-role=${currentRole}]`
      );

      activeBtn.classList.remove("active");
      btn.classList.add("active");

      activeArticle.classList.remove("active");
      currentArticle.classList.add("active");
    });
  });
});
