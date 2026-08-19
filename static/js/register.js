// Client-side validation only — form submits to Django if all checks pass
const registerForm = document.getElementById("registerForm");
const registerMessage = document.getElementById("registerMessage");

if (registerForm) {
    registerForm.addEventListener("submit", function (event) {

        const firstName = document.getElementById("firstName").value.trim();
        const lastName  = document.getElementById("lastName").value.trim();
        const email     = document.getElementById("email").value.trim();
        const phone     = document.getElementById("phone").value.trim();
        const password  = document.getElementById("password").value;
        const confirmPassword = document.getElementById("confirmPassword").value;

        // Required fields
        if (!firstName || !lastName || !email || !phone || !password || !confirmPassword) {
            event.preventDefault();
            registerMessage.style.color = "red";
            registerMessage.textContent = "Please fill in all required fields.";
            return;
        }

        // Password length
        if (password.length < 8) {
            event.preventDefault();
            registerMessage.style.color = "red";
            registerMessage.textContent = "Password must be at least 8 characters.";
            return;
        }

        // Password match
        if (password !== confirmPassword) {
            event.preventDefault();
            registerMessage.style.color = "red";
            registerMessage.textContent = "Passwords do not match.";
            return;
        }

        // Egyptian phone
        const egyptPhone = /^01[0125][0-9]{8}$/;
        if (!egyptPhone.test(phone)) {
            event.preventDefault();
            registerMessage.style.color = "red";
            registerMessage.textContent = "Please enter a valid Egyptian phone number (e.g. 01012345678).";
            return;
        }

        // All good — let the form submit to Django
    });
}