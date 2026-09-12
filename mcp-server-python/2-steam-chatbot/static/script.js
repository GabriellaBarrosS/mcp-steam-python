// Aguarda o DOM carregar completamente
document.addEventListener('DOMContentLoaded', () => {

    // Seleciona os elementos da página
    const chatBox = document.getElementById('chat-box');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');

    // URL da API do backend FastAPI
    const apiUrl = 'http://127.0.0.1:8000/chat';

    // Função para adicionar uma mensagem à caixa de chat
    function addMessage(message, sender) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', `${sender}-message`);
        
        const paragraph = document.createElement('p');
        paragraph.textContent = message;
        messageElement.appendChild(paragraph);
        
        chatBox.appendChild(messageElement);
        
        // Rola a caixa de chat para a última mensagem
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    // Função para enviar a mensagem para o backend
    async function sendMessage() {
        const messageText = userInput.value.trim();

        if (messageText === '') {
            return; // Não envia mensagens vazias
        }

        // Exibe a mensagem do usuário na tela
        addMessage(messageText, 'user');
        userInput.value = ''; // Limpa o campo de input

        try {
            // Adiciona uma mensagem de "digitando..."
            addMessage('Digitando...', 'ai');

            // Faz a requisição para a API
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: messageText }),
            });

            // Remove a mensagem de "digitando..."
            const typingMessage = chatBox.querySelector('.ai-message:last-child');
            if (typingMessage && typingMessage.textContent.includes('Digitando...')) {
                chatBox.removeChild(typingMessage);
            }

            if (!response.ok) {
                throw new Error('A resposta da rede não foi OK.');
            }

            const data = await response.json();
            
            // Exibe a resposta da IA
            if (data.response) {
                addMessage(data.response, 'ai');
            } else if (data.error) {
                addMessage(`Erro: ${data.error}`, 'ai');
            }

        } catch (error) {
             // Remove a mensagem de "digitando..." em caso de erro também
            const typingMessage = chatBox.querySelector('.ai-message:last-child');
            if (typingMessage && typingMessage.textContent.includes('Digitando...')) {
                chatBox.removeChild(typingMessage);
            }
            console.error('Falha ao buscar resposta:', error);
            addMessage('Não foi possível conectar ao servidor. Verifique o console para mais detalhes.', 'ai');
        }
    }

    // Adiciona evento de clique ao botão de enviar
    sendButton.addEventListener('click', sendMessage);

    // Adiciona evento para enviar com a tecla "Enter"
    userInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            sendMessage();
        }
    });
});
