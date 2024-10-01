document.addEventListener("DOMContentLoaded", (e) => {
  let searchField = document.querySelector(".school-search-field");
  let filtersCard = document.querySelector(".filters-card");
  let schoolHiddenField = document.querySelector(".school-hidden-field");
  let headingContainer = document.querySelector(".hero-heading-container");
  let orderSummaryForm = document.querySelector("#order-summary-form");

  // search field events
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

    if (filtersCard.classList.contains("display")) {
      headingContainer.style.display = "none";
    } else {
      headingContainer.style.display = "grid";
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
          let pk = link.getAttribute("data-school-pk");
          schoolHiddenField.value = pk;
          htmx.process(schoolHiddenField);
          htmx.process(orderSummaryForm);
          console.log(schoolHiddenField.value);

          if (pk) {
            searchField.value = link.innerText;
          } else {
            searchField.value = "";
            searchField.focus();
          }
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

  // validate search filters before getting vacancy result
});

function validateAndProceed(event) {
  const roomTypes = document.querySelectorAll(
    "input[name='room-type']:checked"
  );
  const schoolField = document.getElementById("school-field").value;
  const minPrice = document.getElementById("min-price").value;
  const maxPrice = document.getElementById("max-price").value;
  const regions = document.querySelectorAll("input[name='regions']:checked");

  if (!schoolField) {
    alert("Please select a school.");
    event.preventDefault();
    return;
  }

  if (regions.length === 0) {
    alert("Please select at least one region.");
    event.preventDefault();
    return;
  }

  if (roomTypes.length === 0) {
    alert("Please select at least one room type.");
    event.preventDefault();
    return;
  }

  if (!minPrice || !maxPrice) {
    event.preventDefault();
    alert("Please provide both minimum and maximum price.");
    return;
  }
}
