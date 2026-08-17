const signupForm = document.getElementById("signupForm");

async function signupUser() {
    const formdata = new FormData(signupForm);
    const user = {
        full_name: formdata.get("data[full_name]"),
        email: formdata.get("data[email]"),
        password: formdata.get("data[password]"),
        role: formdata.get("data[role]")
    };
    try {
        const res = await fetch("http://localhost:5000/signup",{
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(user)
            });

        const data = await res.json();
        if (!res.ok) {
            console.error( "Signup failed:",data.error);
            alert(data.error);
            return;
        }
        console.log("Account created:",data.user);
        alert("Account created successfully! You can now log in." );
        window.location.href = "login.html";
    } catch (error) {
        console.error("Signup error:",error);
        alert("Unable to connect to the server.");
    }
}