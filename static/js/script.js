document.getElementById('send-btn').addEventListener('click', sendMessage);
document.getElementById('user-input').addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

function sendMessage() {
    const userInput = document.getElementById('user-input');
    const chatBox = document.getElementById('chat-box');

    if (userInput.value.trim() === '') {
        return;
    }

    // Exibe a mensagem do usuário
    const userMessage = document.createElement('div');
    userMessage.classList.add('message', 'user');
    userMessage.innerHTML = `<p>${userInput.value}</p>`;
    chatBox.appendChild(userMessage);

    // Limpa o campo de entrada
    const question = userInput.value;
    userInput.value = '';

    // Faz a requisição para o backend
    fetch('/ask', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question: question }),
    })
    .then(response => response.json())
    .then(data => {
        // Exibe a resposta do bot
        const botMessage = document.createElement('div');
        botMessage.classList.add('message', 'bot');
        botMessage.innerHTML = `<p>${data.response}</p>`;
        chatBox.appendChild(botMessage);

        // Rola a tela para a última mensagem
        chatBox.scrollTop = chatBox.scrollHeight;
    })
    .catch(error => {
        console.error('Erro:', error);
    });
}