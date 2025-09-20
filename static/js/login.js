// static/login.js

document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("loginForm");
  if (!form) return;

  const emailInput = document.getElementById("email");
  const passwordInput = document.getElementById("password");
  const loginBtn = document.getElementById("loginBtn");

  form.addEventListener("submit", function (e) {
    const email = emailInput.value.trim();
    const password = passwordInput.value.trim();

    // ✅ Validation
    if (!email || !password) {
      e.preventDefault();
      showMessage("⚠️ Please enter both Email and Password.", "error");
      return false;
    }

    // ✅ Disable button while submitting
    loginBtn.disabled = true;
    loginBtn.innerText = "Logging in...";
    return true; // allow normal submit
  });
});

// ✅ Helper to show message
function showMessage(message, type) {
  const msgBox = document.getElementById("messageBox");
  if (msgBox) {
    msgBox.innerText = message;
    msgBox.className = type === "success" ? "msg success" : "msg error";
    msgBox.style.display = "block";

    // Auto hide after 4s
    setTimeout(() => {
      msgBox.style.display = "none";
    }, 4000);
  }
}
