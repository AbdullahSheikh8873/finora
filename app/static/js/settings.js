(function () {
  document.getElementById("prefTheme").value = localStorage.getItem("finora-theme") || "light";

  document.getElementById("profileForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const errEl = document.getElementById("profileError");
    errEl.classList.add("hidden");
    try {
      await Finora.api("/api/users/me", {
        method: "PUT",
        body: {
          full_name: document.getElementById("profileName").value,
          email: document.getElementById("profileEmail").value,
        },
      });
      Finora.toast("Profile updated.", "success");
    } catch (err) {
      errEl.textContent = err.message;
      errEl.classList.remove("hidden");
    }
  });

  document.getElementById("prefsForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const errEl = document.getElementById("prefsError");
    errEl.classList.add("hidden");
    const theme = document.getElementById("prefTheme").value;
    try {
      await Finora.api("/api/users/me/preferences", {
        method: "PUT",
        body: {
          currency: document.getElementById("prefCurrency").value,
          date_format: document.getElementById("prefDateFormat").value,
          theme,
        },
      });
      localStorage.setItem("finora-theme", theme);
      document.documentElement.setAttribute("data-theme", theme);
      Finora.toast("Preferences saved. Reloading…", "success");
      setTimeout(() => window.location.reload(), 700);
    } catch (err) {
      errEl.textContent = err.message;
      errEl.classList.remove("hidden");
    }
  });

  document.getElementById("passwordForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const errEl = document.getElementById("passwordError");
    errEl.classList.add("hidden");
    try {
      await Finora.api("/api/auth/change-password", {
        method: "POST",
        body: {
          current_password: document.getElementById("currentPassword").value,
          new_password: document.getElementById("newPassword").value,
          confirm_new_password: document.getElementById("confirmNewPassword").value,
        },
      });
      Finora.toast("Password changed successfully.", "success");
      document.getElementById("passwordForm").reset();
    } catch (err) {
      errEl.textContent = err.message;
      errEl.classList.remove("hidden");
    }
  });

  document.getElementById("deleteAccountBtn").addEventListener("click", () => {
    Finora.confirmDialog(
      "Delete your account?",
      "This permanently deletes your account and all accounts, transactions, budgets, and history. This cannot be undone.",
      async () => {
        await Finora.api("/api/auth/account", { method: "DELETE" });
        window.location.href = "/login";
      },
      "Delete Forever"
    );
  });
})();
