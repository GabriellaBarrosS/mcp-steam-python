// Aguarda o DOM carregar completamente
document.addEventListener('DOMContentLoaded', () => {

    // Seleciona os elementos da página
    const chatBox = document.getElementById('chat-box');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');

    // URL da API do backend FastAPI
    const apiUrl = 'http://127.0.0.1:8000/chat';

    // Escapa caracteres HTML para nunca injetar tags indesejadas
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Converte um texto simples (com **negrito**, listas "- " ou "1. " e
    // quebras de linha) em HTML formatado, sem depender de bibliotecas externas.
    function formatMessage(rawText) {
        const escaped = escapeHtml(rawText);
        const lines = escaped.split('\n');

        let html = '';
        let listBuffer = [];
        let listType = null; // 'ul' ou 'ol'

        function flushList() {
            if (listBuffer.length > 0) {
                html += `<${listType}>` + listBuffer.map(item => `<li>${item}</li>`).join('') + `</${listType}>`;
                listBuffer = [];
                listType = null;
            }
        }

        function applyInlineFormatting(line) {
            // **negrito**
            line = line.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
            // links em markdown [texto](url)
            line = line.replace(/\[(.+?)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
            return line;
        }

        for (const rawLine of lines) {
            const line = rawLine.trim();

            const bulletMatch = line.match(/^[-*]\s+(.*)/);
            const numberedMatch = line.match(/^\d+[.)]\s+(.*)/);

            if (bulletMatch) {
                if (listType !== 'ul') { flushList(); listType = 'ul'; }
                listBuffer.push(applyInlineFormatting(bulletMatch[1]));
            } else if (numberedMatch) {
                if (listType !== 'ol') { flushList(); listType = 'ol'; }
                listBuffer.push(applyInlineFormatting(numberedMatch[1]));
            } else {
                flushList();
                if (line === '') {
                    html += '<br>';
                } else {
                    html += `<p>${applyInlineFormatting(line)}</p>`;
                }
            }
        }
        flushList();

        return html || '<p></p>';
    }

    // Função para adicionar uma mensagem à caixa de chat
    function addMessage(message, sender) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', `${sender}-message`);

        if (sender === 'ai') {
            // Mensagens da IA podem vir com listas, negrito, etc -- formata
            messageElement.innerHTML = formatMessage(message);
        } else {
            // Mensagem do usuário: texto puro, sem interpretar formatação
            const paragraph = document.createElement('p');
            paragraph.textContent = message;
            messageElement.appendChild(paragraph);
        }

        chatBox.appendChild(messageElement);

        // Rola a caixa de chat para a última mensagem
        chatBox.scrollTop = chatBox.scrollHeight;
        return messageElement;
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
        sendButton.disabled = true;

        // Adiciona uma mensagem de "digitando..." e guarda a referência direta
        const typingElement = addMessage('Digitando...', 'ai');
        typingElement.classList.add('typing-indicator');

        try {
            // Faz a requisição para a API
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: messageText }),
            });

            // Remove a mensagem de "digitando..."
            typingElement.remove();

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
            typingElement.remove();
            console.error('Falha ao buscar resposta:', error);
            addMessage('Não foi possível conectar ao servidor. Verifique o console para mais detalhes.', 'ai');
        } finally {
            sendButton.disabled = false;
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
