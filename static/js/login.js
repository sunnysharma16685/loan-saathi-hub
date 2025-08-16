async function loginUser(event) {
  event.preventDefault();

  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;
  const userType = document.querySelector("input[name='user_type']:checked")?.value || "user";

  if (!email || !password) {
    showMessage("कृपया सभी फ़ील्ड भरें।", "error");
    return;
  }

  const loginBtn = document.getElementById("loginBtn");
  loginBtn.disabled = true;
  loginBtn.innerText = "Login हो रहा है...";

  try {
    const response = await fakeLogin(email, password, userType);

    if (response.success) {
      showMessage("लॉगिन सफल हुआ!", "success");
      setTimeout(() => {
        if (response.role === "user") {
          window.location.href = "/dashboard_user";
        } else {
          window.location.href = "/dashboard_agent";
        }
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

// Mock login (replace later with real backend/Supabase)
async function fakeLogin(email, password, userType) {
  return new Promise((resolve) => {
    setTimeout(() => {
      if (email === "test@example.com" && password === "123456") {
        resolve({ success: true, role: userType });
      } else {
        resolve({ success: false });
      }
    }, 1000);
  });
}

function showMessage(message, type) {
  const msgBox = document.getElementById("messageBox");
  msgBox.innerText = message;
  msgBox.className = type === "success" ? "msg success" : "msg error";
  msgBox.style.display = "block";
}
