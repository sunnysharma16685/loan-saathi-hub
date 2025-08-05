<script>
async function loginUser(event) {
  event.preventDefault();

  // Get form inputs
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;

  // Basic UX validation
  if (!email || !password) {
    showMessage("कृपया सभी फ़ील्ड भरें।", "error");
    return;
  }

  // Disable button to prevent multiple submissions
  const loginBtn = document.getElementById("loginBtn");
  loginBtn.disabled = true;
  loginBtn.innerText = "लॉगिन हो रहा है...";

  try {
    // Mock login logic (replace with real fetch or Supabase logic)
    const response = await fakeLogin(email, password);

    if (response.success) {
      showMessage("लॉगिन सफल हुआ!", "success");
      setTimeout(() => {
        window.location.href = "/dashboard";  // Your Flask route here
      }, 1000);
    } else {
      showMessage("गलत ईमेल या पासवर्ड।", "error");
    }
  } catch (err) {
    console.error(err);
    showMessage("कुछ गलत हो गया। बाद में कोशिश करें।", "error");
  } finally {
    loginBtn.disabled = false;
    loginBtn.innerText = "Login";
  }
}

// Fake login logic to simulate success/failure
async function fakeLogin(email, password) {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({ success: email === "test@example.com" && password === "123456" });
    }, 1000);
  });
}

// UX-friendly message display
function showMessage(message, type) {
  const msgBox = document.getElementById("messageBox");
  msgBox.innerText = message;
  msgBox.className = type === "success" ? "msg success" : "msg error";
  msgBox.style.display = "block";
}
</script>
