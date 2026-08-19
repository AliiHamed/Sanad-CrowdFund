const navbar = document.querySelector(".navbar");

window.addEventListener("scroll", function () {

    if (window.scrollY > 50) {

        navbar.style.background = "#0b5ed7";
        navbar.style.transition = "0.4s";

    } else {

        navbar.style.background = "#ffffff";

    }

});
const sections = document.querySelectorAll("section");

window.addEventListener("scroll", () => {

    sections.forEach(section => {

        const sectionTop = section.getBoundingClientRect().top;

        if (sectionTop < window.innerHeight - 100) {
            section.classList.add("animate");
        }

    });

});