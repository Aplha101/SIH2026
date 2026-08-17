document.addEventListener('DOMContentLoaded', async () => {
    try {
        const response = await fetch('/api/student/dashboard', {
            method: 'GET',
            credentials: 'include'
        });

        if (response.status === 401 || response.status === 403) {
            window.location.href = '/login.html';
            return;
        }

        const data = await response.json();

        document.getElementById('student-name').textContent = data.user.username || 'Student';
        
        if (data.assignedCounselor) {
            document.getElementById('counselor-info').textContent = 
                `${data.assignedCounselor.name} (${data.assignedCounselor.email})`;
        } else {
            document.getElementById('counselor-info').textContent = 'No counselor assigned yet.';
        }

    } catch (err) {
        console.error('Error initializing student dashboard:', err);
    }
});