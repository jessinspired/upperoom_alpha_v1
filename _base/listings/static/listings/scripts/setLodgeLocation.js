function getCoordinates(event) {
  event.preventDefault();

  if (!navigator.geolocation) {
    alert("Geolocation is not supported by this browser.");
    return;
  }
  let csrfToken = document.querySelector('input[name="csrf-hidden"]');

  navigator.geolocation.getCurrentPosition(
    (position) => {
      let latitude = position.coords.latitude;
      let longitude = position.coords.longitude;

      htmx.ajax(
        "POST",
        `https://upperoom.ng${event.target.getAttribute("data-url")}`,
        {
          headers: {
            "X-CSRFToken": csrfToken,
          },
          target: "#location-handler",
          swap: "outerHTML",
          values: {
            latitude: latitude,
            longitude: longitude,
          },
        }
      );
    },
    (error) => {
      console.error("Error getting location: ", error);
      alert("Error getting location");
    }
  );
}
