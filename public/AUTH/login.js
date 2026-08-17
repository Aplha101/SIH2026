const loginForm = document.getElementById("loginForm");

async function userlogin() {
    const formdata = new FormData(loginForm);

    const user = {
        email: formdata.get("data[email]"),
        password: formdata.get("data[password]")
    };

    console.log("Email:", user.email);
    console.log("Password exists:", !!user.password);
    console.log("Password length:", user.password ? user.password.length : 0);

    try {
        const res = await fetch("https://mindfulu-api.onrender.com/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(user)
        });

        const data = await res.json();

        if (!res.ok) {
            console.error("Login failed:", data.error);
            alert(data.error);
            return;
        }

        console.log("Login successful:", data);

        localStorage.setItem("token", data.token);
        localStorage.setItem("user", JSON.stringify(data.user));

        window.location.href = "../dashboard/dashboard.html";

    } catch (err) {
        console.error("Login error:", err);
    }
}

loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    await userlogin();
});