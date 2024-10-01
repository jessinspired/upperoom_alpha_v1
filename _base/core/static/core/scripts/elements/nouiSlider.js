// from nouislider codepen
const keypressSlider = document.querySelector(".slider-keypress");
const input0 = document.querySelector(".input-with-keypress-0");
const input1 = document.querySelector(".input-with-keypress-1");
const inputs = [input0, input1];

noUiSlider.create(keypressSlider, {
  start: [0, 500000],
  connect: true,
  step: 1000,
  range: {
    min: [0],
    max: [1000000],
  },
  format: {
    to: function (value) {
      return value.toLocaleString("en-US");
    },
    from: function (value) {
      return Number(value.replace(",", ""));
    },
  },
});

/* begin Inputs  */

/* end Inputs  */
keypressSlider.noUiSlider.on("update", function (values, handle) {
  inputs[handle].value = values[handle];

  /* begin Listen to keypress on the input */
  function setSliderHandle(i, value) {
    const r = [null, null];
    r[i] = value;
    keypressSlider.noUiSlider.set(r);
  }

  // Listen to keydown events on the input field.
  inputs.forEach(function (input, handle) {
    input.addEventListener("change", function () {
      setSliderHandle(handle, this.value);
    });

    input.addEventListener("keydown", function (e) {
      const values = keypressSlider.noUiSlider.get();
      const value = Number(values[handle]);

      //   [
      //     [handle0_down, handle0_up],
      //     [handle1_down, handle1_up],
      //   ];
      const steps = keypressSlider.noUiSlider.steps();

      //   [down, up];
      const step = steps[handle];

      let position;

      // 13 is enter,
      // 38 is key up,
      // 40 is key down.
      switch (e.which) {
        case 13:
          e.preventDefault();
          setSliderHandle(handle, this.value);
          break;

        case 38:
          // Get step to go increase slider value (up)
          position = step[1];

          // false = no step is set
          if (position === false) {
            position = 1;
          }

          // null = edge of slider
          if (position !== null) {
            setSliderHandle(handle, value + position);
          }

          break;

        case 40:
          position = step[0];

          if (position === false) {
            position = 1;
          }

          if (position !== null) {
            setSliderHandle(handle, value - position);
          }

          break;
      }
    });
  });
  /* end Listen to keypress on the input */
});
