// chatbot.js - A simple widget for embedding a chatbot interface on websites

const ChatbotWidget = {
  // Configuration and state
  config: {
    apiUrl: "https://rk-nature-backend.onrender.com/submit_query",
    sessionId: null,
    isMobile: false,
  },

  elements: {
    container: null,
    floatingButton: null,
    messages: null,
    input: null,
  },

  state: {
    isOpen: false,
  },

  // Initialization
  init(config = {}) {
    // Set up configuration
    if (config.url) this.config.apiUrl = config.url
    this.config.sessionId =
      sessionStorage.getItem("chatbotSessionId") ||
      `sess_${Math.random().toString(36).substr(2, 9)}`
    sessionStorage.setItem("chatbotSessionId", this.config.sessionId)

    // Check device type
    this.updateDeviceType()

    // Create UI and bind events
    this.createUI()
    this.bindEvents()
  },

  // Detect mobile/desktop
  updateDeviceType() {
    this.config.isMobile = window.innerWidth <= 768
  },

  // UI Creation
  createUI() {
    this.createFloatingButton()
    this.createChatContainer()
    this.createHeader()
    this.createMessagesArea()
    this.createInputArea()
    this.createFooter()

    // Add welcome message
    this.addBotMessage("Hi 👋 How can I help you?")
  },

  createFloatingButton() {
    const button = document.createElement("div")
    button.id = "chatbot-floating-button"
    button.innerHTML = "💬"

    const style = {
      position: "fixed",
      bottom: this.config.isMobile ? "10px" : "20px",
      right: this.config.isMobile ? "10px" : "20px",
      width: this.config.isMobile ? "45px" : "50px",
      height: this.config.isMobile ? "45px" : "50px",
      background: "linear-gradient(135deg, #007bff, #00c4ff)",
      borderRadius: "50%",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      color: "white",
      fontSize: this.config.isMobile ? "22px" : "24px",
      cursor: "pointer",
      boxShadow: "0 2px 10px rgba(0,0,0,0.3)",
      zIndex: "1000",
      touchAction: "manipulation",
    }

    Object.assign(button.style, style)
    document.body.appendChild(button)
    this.elements.floatingButton = button
  },

  createChatContainer() {
    const container = document.createElement("div")
    container.id = "chatbot-container"

    const style = {
      position: "fixed",
      bottom: this.config.isMobile ? "60px" : "80px",
      right: this.config.isMobile ? "10px" : "20px",
      width: this.config.isMobile ? "90vw" : "360px",
      height: this.config.isMobile ? "80vh" : "500px",
      maxWidth: "400px",
      maxHeight: "90vh",
      minWidth: "280px",
      minHeight: "300px",
      borderRadius: "15px",
      background: "#fff",
      boxShadow: "0 0 15px rgba(0,0,0,0.1)",
      display: "none",
      flexDirection: "column",
      overflow: "hidden",
      zIndex: "1001",
    }

    Object.assign(container.style, style)
    document.body.appendChild(container)
    this.elements.container = container
  },

  createHeader() {
    const header = document.createElement("div")
    header.id = "chatbot-header"

    header.innerHTML = `
            <div style="display: flex; align-items: center;">
                <img src="./face.png" style="width: 40px; height: 40px; border-radius: 50%; margin-right: 10px;" alt="RK Nature">
                <div>
                    <h3 style="margin: 0; color: white; font-size: ${
                      this.config.isMobile ? "16px" : "18px"
                    };">Chat with RK Nature</h3>
                    <p style="margin: 0; color: white; font-size: ${
                      this.config.isMobile ? "12px" : "14px"
                    };">We are online!</p>
                </div>
            </div>
            <span id="chatbot-close" style="position: absolute; right: 15px; top: 50%; transform: translateY(-50%); color: white; cursor: pointer; font-size: 20px;">×</span>
        `

    const style = {
      background: "linear-gradient(135deg, #007bff, #00c4ff)",
      padding: "10px 15px",
      borderTopLeftRadius: "15px",
      borderTopRightRadius: "15px",
      position: "relative",
    }

    Object.assign(header.style, style)
    this.elements.container.appendChild(header)
  },

  createMessagesArea() {
    const messages = document.createElement("div")
    messages.id = "chatbot-messages"

    const style = {
      flex: "1",
      padding: "15px",
      overflowY: "auto",
      background: "#f5f7fa",
      display: "flex",
      flexDirection: "column",
      WebkitOverflowScrolling: "touch",
    }

    Object.assign(messages.style, style)
    this.elements.container.appendChild(messages)
    this.elements.messages = messages
  },

  createInputArea() {
    const inputArea = document.createElement("div")
    inputArea.style.cssText = `
            padding: 10px;
            display: flex;
            align-items: center;
            border-top: 1px solid #eee;
            background: #fff;
        `

    // Create input field
    const input = document.createElement("input")
    input.type = "text"
    input.id = "chatbot-input"
    input.placeholder = "Enter your message..."
    input.style.cssText = `
            flex: 1;
            padding: 10px;
            border: none;
            outline: none;
            font-size: ${this.config.isMobile ? "14px" : "16px"};
            border-radius: 10px;
            background: #f0f0f0;
            margin-right: 10px;
        `

    // Create send button
    const sendButton = document.createElement("button")
    sendButton.innerHTML = "➤"
    sendButton.style.cssText = `
            width: ${this.config.isMobile ? "40px" : "45px"};
            height: ${this.config.isMobile ? "40px" : "45px"};
            background: linear-gradient(135deg, #007bff, #00c4ff);
            border: none;
            border-radius: 50%;
            color: white;
            font-size: ${this.config.isMobile ? "18px" : "20px"};
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            touch-action: manipulation;
        `

    inputArea.appendChild(input)
    inputArea.appendChild(sendButton)
    this.elements.container.appendChild(inputArea)
    this.elements.input = input
  },

  createFooter() {
    const footer = document.createElement("div")
    footer.innerHTML = `Powered by <span style="color: #007bff;">R K Nature</span>`

    const style = {
      textAlign: "center",
      padding: "5px",
      fontSize: this.config.isMobile ? "12px" : "14px",
      color: "#666",
      borderTop: "1px solid #eee",
    }

    Object.assign(footer.style, style)
    this.elements.container.appendChild(footer)
  },

  // Event Handling
  bindEvents() {
    // Toggle chat open/close
    this.elements.floatingButton.addEventListener("click", () =>
      this.toggleChat(true)
    )
    document
      .getElementById("chatbot-close")
      .addEventListener("click", () => this.toggleChat(false))

    // Send message events
    const sendButton = this.elements.container.querySelector("button")
    const input = this.elements.input

    sendButton.addEventListener("click", () => this.sendMessage())
    input.addEventListener("keypress", (e) => {
      if (e.key === "Enter") this.sendMessage()
    })

    // Handle window resizing
    window.addEventListener("resize", () => {
      this.updateDeviceType()
      this.updateResponsiveLayout()
    })
  },

  toggleChat(open) {
    this.state.isOpen = open !== undefined ? open : !this.state.isOpen
    this.elements.container.style.display = this.state.isOpen ? "flex" : "none"
    this.elements.floatingButton.style.display = this.state.isOpen
      ? "none"
      : "flex"

    if (this.state.isOpen) {
      this.elements.input.focus()
    }
  },

  updateResponsiveLayout() {
    // Update container sizing
    this.elements.container.style.width = this.config.isMobile
      ? "90vw"
      : "360px"
    this.elements.container.style.height = this.config.isMobile
      ? "80vh"
      : "500px"
    this.elements.container.style.bottom = this.config.isMobile
      ? "60px"
      : "80px"
    this.elements.container.style.right = this.config.isMobile ? "10px" : "20px"

    // Update floating button position
    this.elements.floatingButton.style.bottom = this.config.isMobile
      ? "10px"
      : "20px"
    this.elements.floatingButton.style.right = this.config.isMobile
      ? "10px"
      : "20px"
  },

  // Message Handling
  sendMessage() {
    const query = this.elements.input.value.trim()
    if (!query) return

    this.addUserMessage(query)
    this.elements.input.value = ""
    this.showTypingIndicator()

    // Send to backend
    fetch(this.config.apiUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        SessionId: this.config.sessionId,
        Query: query,
      }),
    })
      .then((response) => response.json())
      .then((data) => {
        this.removeTypingIndicator()
        this.addBotMessage(data.response)
      })
      .catch((error) => {
        this.removeTypingIndicator()
        this.addErrorMessage("Error: Could not get response")
      })
  },

  addUserMessage(text) {
    const msg = document.createElement("div")
    msg.textContent = text

    const style = {
      background: "linear-gradient(135deg, #007bff, #00c4ff)",
      color: "white",
      padding: "10px 15px",
      borderRadius: "15px",
      margin: "5px 0",
      maxWidth: "80%",
      alignSelf: "flex-end",
      fontSize: this.config.isMobile ? "14px" : "16px",
      lineHeight: "1.4",
    }

    Object.assign(msg.style, style)
    this.elements.messages.appendChild(msg)
    this.scrollToBottom()
  },

  addBotMessage(text) {
    const msg = document.createElement("div")
    msg.textContent = text

    const style = {
      background: "#e6f0ff",
      color: "#333",
      padding: "10px 15px",
      borderRadius: "15px",
      margin: "5px 0",
      maxWidth: "80%",
      alignSelf: "flex-start",
      fontSize: this.config.isMobile ? "14px" : "16px",
      lineHeight: "1.4",
    }

    Object.assign(msg.style, style)
    this.elements.messages.appendChild(msg)
    this.scrollToBottom()
  },

  addErrorMessage(text) {
    const msg = document.createElement("div")
    msg.textContent = text

    const style = {
      background: "#ffe6e6",
      color: "#d32f2f",
      padding: "10px 15px",
      borderRadius: "15px",
      margin: "5px 0",
      maxWidth: "80%",
      alignSelf: "flex-start",
      fontSize: this.config.isMobile ? "14px" : "16px",
      lineHeight: "1.4",
    }

    Object.assign(msg.style, style)
    this.elements.messages.appendChild(msg)
    this.scrollToBottom()
  },

  showTypingIndicator() {
    const typingMsg = document.createElement("div")
    typingMsg.textContent = "Typing..."
    typingMsg.id = "typing-indicator"

    const style = {
      background: "#e6f0ff",
      color: "#666",
      padding: "10px 15px",
      borderRadius: "15px",
      margin: "5px 0",
      maxWidth: "80%",
      alignSelf: "flex-start",
      fontSize: this.config.isMobile ? "14px" : "16px",
      fontStyle: "italic",
      lineHeight: "1.4",
    }

    Object.assign(typingMsg.style, style)
    this.elements.messages.appendChild(typingMsg)
    this.scrollToBottom()
  },

  removeTypingIndicator() {
    const typingIndicator = document.getElementById("typing-indicator")
    if (typingIndicator) typingIndicator.remove()
  },

  scrollToBottom() {
    this.elements.messages.scrollTop = this.elements.messages.scrollHeight
  },
}

// Auto-initialize
const scriptTag = document.currentScript
if (scriptTag && scriptTag.dataset.url) {
  ChatbotWidget.init({ url: scriptTag.dataset.url })
} else {
  ChatbotWidget.init({})
}
