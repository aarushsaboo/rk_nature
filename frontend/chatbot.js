const ChatbotWidget = {
    init(config) {
        this.apiUrl = config.url || 'https://backend-rk.onrender.com/submit_query';
        this.sessionId = sessionStorage.getItem('chatbotSessionId') || `sess_${Math.random().toString(36).substr(2, 9)}`;
        sessionStorage.setItem('chatbotSessionId', this.sessionId);
        this.isOpen = false;
        this.createChatbot();
        this.bindEvents();
    },

    createChatbot() {
        const viewportWidth = window.innerWidth;
        const isMobile = viewportWidth <= 768; // Adjusted breakpoint for mobile/tablet

        // Floating button
        const floatingButton = document.createElement('div');
        floatingButton.id = 'chatbot-floating-button';
        floatingButton.innerHTML = '💬';
        floatingButton.style.cssText = `
            position: fixed; bottom: ${isMobile ? '10px' : '20px'}; right: ${isMobile ? '10px' : '20px'};
            width: ${isMobile ? '45px' : '50px'}; height: ${isMobile ? '45px' : '50px'};
            background: linear-gradient(135deg, #007bff, #00c4ff); border-radius: 50%;
            display: flex; align-items: center; justify-content: center; color: white;
            font-size: ${isMobile ? '22px' : '24px'}; cursor: pointer; box-shadow: 0 2px 10px rgba(0,0,0,0.3);
            z-index: 1000; touch-action: manipulation;
        `;
        document.body.appendChild(floatingButton);

        // Main container
        const container = document.createElement('div');
        container.id = 'chatbot-container';
        container.style.cssText = `
            position: fixed; bottom: ${isMobile ? '60px' : '80px'}; right: ${isMobile ? '10px' : '20px'};
            width: ${isMobile ? '90vw' : '360px'}; height: ${isMobile ? '80vh' : '500px'};
            max-width: 400px; max-height: 90vh; min-width: 280px; min-height: 300px;
            border-radius: 15px; background: #fff; box-shadow: 0 0 15px rgba(0,0,0,0.1);
            display: none; flex-direction: column; overflow: hidden; z-index: 1001;
        `;

        // Header
        const header = document.createElement('div');
        header.id = 'chatbot-header';
        header.innerHTML = `
            <div style="display: flex; align-items: center;">
                <img src="./face.png" style="width: 40px; height: 40px; border-radius: 50%; margin-right: 10px;" alt="RK Nature">
                <div>
                    <h3 style="margin: 0; color: white; font-size: ${isMobile ? '16px' : '18px'};">Chat with RK Nature</h3>
                    <p style="margin: 0; color: white; font-size: ${isMobile ? '12px' : '14px'};">We are online!</p>
                </div>
            </div>
            <span style="position: absolute; right: 15px; top: 50%; transform: translateY(-50%); color: white; cursor: pointer; font-size: 20px;">×</span>
        `;
        header.style.cssText = `
            background: linear-gradient(135deg, #007bff, #00c4ff); padding: 10px 15px;
            border-top-left-radius: 15px; border-top-right-radius: 15px; position: relative;
        `;
        container.appendChild(header);

        // Messages area
        const messages = document.createElement('div');
        messages.id = 'chatbot-messages';
        messages.style.cssText = `
            flex: 1; padding: 15px; overflow-y: auto; background: #f5f7fa;
            display: flex; flex-direction: column; -webkit-overflow-scrolling: touch;
        `;
        container.appendChild(messages);

        // Welcome message
        const welcomeMsg = document.createElement('div');
        welcomeMsg.textContent = `Hi 👋 How can I help you?`;
        welcomeMsg.style.cssText = `
            background: #e6f0ff; color: #333; padding: 10px 15px; border-radius: 15px;
            margin-bottom: 10px; max-width: 80%; align-self: flex-start;
            font-size: ${isMobile ? '14px' : '16px'}; line-height: 1.4;
        `;
        messages.appendChild(welcomeMsg);

        // Input area
        const inputArea = document.createElement('div');
        inputArea.style.cssText = `
            padding: 10px; display: flex; align-items: center; border-top: 1px solid #eee;
            background: #fff;
        `;
        
        const input = document.createElement('input');
        input.type = 'text';
        input.id = 'chatbot-input';
        input.placeholder = 'Enter your message...';
        input.style.cssText = `
            flex: 1; padding: 10px; border: none; outline: none; font-size: ${isMobile ? '14px' : '16px'};
            border-radius: 10px; background: #f0f0f0; margin-right: 10px;
        `;
        
        const sendButton = document.createElement('button');
        sendButton.innerHTML = '➤';
        sendButton.style.cssText = `
            width: ${isMobile ? '40px' : '45px'}; height: ${isMobile ? '40px' : '45px'};
            background: linear-gradient(135deg, #007bff, #00c4ff); border: none; border-radius: 50%;
            color: white; font-size: ${isMobile ? '18px' : '20px'}; cursor: pointer;
            display: flex; align-items: center; justify-content: center; touch-action: manipulation;
        `;

        inputArea.appendChild(input);
        inputArea.appendChild(sendButton);
        container.appendChild(inputArea);

        // Footer
        const footer = document.createElement('div');
        footer.innerHTML = `Powered by <span style="color: #007bff;">R K Nature</span>`;
        footer.style.cssText = `
            text-align: center; padding: 5px; font-size: ${isMobile ? '12px' : '14px'}; color: #666;
            border-top: 1px solid #eee;
        `;
        container.appendChild(footer);

        document.body.appendChild(container);

        // Toggle functionality
        floatingButton.addEventListener('click', () => {
            this.isOpen = !this.isOpen;
            container.style.display = this.isOpen ? 'flex' : 'none';
            floatingButton.style.display = this.isOpen ? 'none' : 'flex';
        });

        header.querySelector('span').addEventListener('click', () => {
            this.isOpen = false;
            container.style.display = 'none';
            floatingButton.style.display = 'flex';
        });

        // Dynamic resize handler
        window.addEventListener('resize', () => {
            const newViewportWidth = window.innerWidth;
            const newIsMobile = newViewportWidth <= 768;
            container.style.width = newIsMobile ? '90vw' : '360px';
            container.style.height = newIsMobile ? '80vh' : '500px';
            container.style.bottom = newIsMobile ? '60px' : '80px';
            container.style.right = newIsMobile ? '10px' : '20px';
            floatingButton.style.bottom = newIsMobile ? '10px' : '20px';
            floatingButton.style.right = newIsMobile ? '10px' : '20px';
        });
    },

    bindEvents() {
        const sendButton = document.querySelector('#chatbot-container button');
        const input = document.querySelector('#chatbot-input');
        const messages = document.querySelector('#chatbot-messages');

        const isMobile = window.innerWidth <= 768;

        const sendMessage = () => {
            const query = input.value.trim();
            if (!query) return;

            const userMsg = document.createElement('div');
            userMsg.textContent = query;
            userMsg.style.cssText = `
                background: linear-gradient(135deg, #007bff, #00c4ff); color: white;
                padding: 10px 15px; border-radius: 15px; margin: 5px 0; max-width: 80%;
                align-self: flex-end; font-size: ${isMobile ? '14px' : '16px'}; line-height: 1.4;
            `;
            messages.appendChild(userMsg);
            input.value = '';

            const typingMsg = document.createElement('div');
            typingMsg.textContent = 'Typing...';
            typingMsg.id = 'typing-indicator';
            typingMsg.style.cssText = `
                background: #e6f0ff; color: #666; padding: 10px 15px; border-radius: 15px;
                margin: 5px 0; max-width: 80%; align-self: flex-start;
                font-size: ${isMobile ? '14px' : '16px'}; font-style: italic; line-height: 1.4;
            `;
            messages.appendChild(typingMsg);
            messages.scrollTop = messages.scrollHeight;

            fetch(this.apiUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    SessionId: this.sessionId,
                    Query: query
                })
            })
            .then(response => response.json())
            .then(data => {
                const typingIndicator = document.getElementById('typing-indicator');
                if (typingIndicator) typingIndicator.remove();

                const botMsg = document.createElement('div');
                botMsg.textContent = data.response;
                botMsg.style.cssText = `
                    background: #e6f0ff; color: #333; padding: 10px 15px; border-radius: 15px;
                    margin: 5px 0; max-width: 80%; align-self: flex-start;
                    font-size: ${isMobile ? '14px' : '16px'}; line-height: 1.4;
                `;
                messages.appendChild(botMsg);
                messages.scrollTop = messages.scrollHeight;
            })
            .catch(error => {
                const typingIndicator = document.getElementById('typing-indicator');
                if (typingIndicator) typingIndicator.remove();

                const errorMsg = document.createElement('div');
                errorMsg.textContent = `Error: Could not get response`;
                errorMsg.style.cssText = `
                    background: #ffe6e6; color: #d32f2f; padding: 10px 15px; border-radius: 15px;
                    margin: 5px 0; max-width: 80%; align-self: flex-start;
                    font-size: ${isMobile ? '14px' : '16px'}; line-height: 1.4;
                `;
                messages.appendChild(errorMsg);
                messages.scrollTop = messages.scrollHeight;
            });
        };

        sendButton.addEventListener('click', sendMessage);
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
    }
};

// Auto-initialize
const scriptTag = document.currentScript;
if (scriptTag && scriptTag.dataset.url) {
    ChatbotWidget.init({ url: scriptTag.dataset.url });
} else {
    ChatbotWidget.init({});
}
