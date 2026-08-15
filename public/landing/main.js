document.addEventListener('DOMContentLoaded', () => {
    const usernameInput = document.getElementById('username');
    const submitBtn = document.querySelector('.submit-btn');

    function proceedToDialogue() {
        const name = usernameInput.value.trim() || 'Friend';
        localStorage.setItem('breathUserName', name);
        window.location.href = '/landing/dialogue.html'; // or '/AUTH/dialogue.html' depending on where it sits
    }

    if (submitBtn) {
        submitBtn.addEventListener('click', proceedToDialogue);
    }

    if (usernameInput) {
        usernameInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                proceedToDialogue();
            }
        });
    }
});

document.addEventListener('DOMContentLoaded', () => {
    const userName = localStorage.getItem('breathUserName') || 'Friend';
    const dialogueText = document.getElementById('dialogueText');
    const nextBtn = document.getElementById('nextBtn');

    const script = [
        `Welcome, ${userName}. Take a moment to settle in.`,
        `Whatever brought you here today, you can leave it at the door.`,
        `Right now, there is nothing you need to solve or fix.`,
        `Just take one slow, deep breath...you're not alone`,
        `You are doing just fine, ${userName}.`
    ];

    let currentStep = 0;

    function typeSentence(text, callback) {
        dialogueText.textContent = '';
        nextBtn.classList.remove('show');
        let index = 0;
        
        const timer = setInterval(() => {
            if (index < text.length) {
                dialogueText.textContent += text.charAt(index);
                index++;
            } else {
                clearInterval(timer);
                if (callback) callback();
            }
        }, 40);
    }
    
        function showNextDialogue() {
        if (currentStep < script.length) {
            typeSentence(script[currentStep], () => {
                nextBtn.classList.add('show');
            });
            currentStep++;
        } else {
            window.location.href = 'index.html';
        }
    }
    nextBtn.addEventListener('click', showNextDialogue);
    showNextDialogue();
});

const skip = document.getElementById('Skip');
if (skip) {
    skip.addEventListener('click', () => {

window.location.href = "../AUTH/signin.html";
    });
}