var form = document.getElementById("forgotForm");

var email = document.getElementById("email");

var message = document.getElementById("message");


form.addEventListener("submit", function(event) {

    event.preventDefault();


    if (email.value.trim() === "") {

        message.textContent = "Please enter your email address.";

        return;

    }


    message.textContent =
        "Password reset link has been sent to your email.";

    form.reset();

});