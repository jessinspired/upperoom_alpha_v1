document.addEventListener("DOMContentLoaded", (e) => {
  let searchField = document.querySelector(".school-search-field");
  let filtersCard = document.querySelector(".filters-card");

  searchField.addEventListener("focus", (e) => {
    filtersCard.classList.add("display");
  });

  document.addEventListener("click", (e) => {
    if (
      !filtersCard.contains(e.target) &&
      filtersCard.classList.contains("display") &&
      e.target !== searchField &&
      !e.target.classList.contains("school-url")
    ) {
      filtersCard.classList.remove("display");
    }
  });

  //   htmx triggered events
  document.addEventListener(
    "addSearchFieldEvents",
    (e) => {
      schoolsLink = document.querySelectorAll(".school-url");
      let schoolsDropdown = document.querySelector(".schools-dropdown");

      schoolsLink.forEach((link) => {
        link.addEventListener("click", (e) => {
          schoolsDropdown.classList.remove("display");
        });
      });

      document.addEventListener("click", (e) => {
        if (!e.target.classList.contains("school-url")) {
          schoolsDropdown.classList.remove("display");
        }
      });
    },
    true
  );
});
