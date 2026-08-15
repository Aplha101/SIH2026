async function fetchUsers() {
    try {
        const res = await fetch('/api/get-all');
        const data = await res.json();
        
        console.log("Users inside function:", data.users);
        return data.users; 
    } catch (error) {
        console.error("Fetch error:", error);
    }
}

async function main() {
    let res = await fetchUsers();
    console.log("Returned result:", res); 
}

main();