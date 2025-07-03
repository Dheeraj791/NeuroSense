window.addEventListener("DOMContentLoaded", function () {
    particlesJS("particles-js", {
  particles: {
      number: { value: 80, density: { enable: true, value_area: 800 } },
      color: { value: "#00c0b5" }, /* Green particles */
      shape: { type: "circle" },
      opacity: { value: 0.7, random: false },
      size: { value: 3, random: true },
      line_linked: { enable: true, distance: 150, color: "#00c0b5", opacity: 0.6, width: 1 },
      move: { enable: true, speed: 2, direction: "none", random: false, straight: false }
  },
  interactivity: {
      detect_on: "canvas",
      events: {
          onhover: { enable: true, mode: "repulse" },
          onclick: { enable: true, mode: "push" }
      },
      modes: {
          repulse: { distance: 100, duration: 0.4 },
          push: { particles_nb: 4 }
      }
  }
});
});
