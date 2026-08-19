const password = document.getElementById("password");
const togglePassword = document.getElementById("togglePassword");

togglePassword.addEventListener("click", () => {

    if(password.type === "password"){

        password.type = "text";
        togglePassword.textContent = "Hide";

    }else{

        password.type = "password";
        togglePassword.textContent = "Show";

    }

});