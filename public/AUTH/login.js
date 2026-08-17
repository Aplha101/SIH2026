const loginForm = document.getElementById("loginForm");

async function userlogin() {

    const formdata = new FormData(loginForm);

    const user = {
        email: formdata.get("data[email]"),
        password: formdata.get("data[password]")
    };
    try {
        const res = await fetch("http://localhost:5000/login", {
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
        data.user.role == "student" ? window.location.href = "../student/index.html" : window.location.href = "../counsellor/index.html"
    } catch (err) {
        console.error("Login error:", err);
    }
}
loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    await userlogin();
});