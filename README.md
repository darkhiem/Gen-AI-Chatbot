# Gen-AI-Chatbot
Voice Assistant with AI text &amp; image generation. Features speech recognition, Gemini AI integration, Stable Diffusion image creation, voice output, and MongoDB conversation storage. Built with Streamlit for an intuitive interface. The perfect personal AI assistant for both voice and text interactions.
# Voice Assistant

![Python](https://img.shields.io/badge/Python-3.8+-green.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.20+-red.svg)

A powerful, feature-rich AI voice assistant with text and image generation capabilities built using Streamlit, Google's Gemini API, and Stable Diffusion.

## ✨ Features

- **Voice Interaction**: Speak commands and receive spoken responses
- **Text Generation**: Powered by Google's Gemini 1.5 Flash for intelligent conversations
- **Image Generation**: Create images from text descriptions using Stable Diffusion
- **Conversation Memory**: Save and retrieve past conversations with MongoDB integration
- **Customizable Voice**: Adjust speech rate, volume, and select different voices
- **Web Search**: Access information from Wikipedia and open websites
- **Multi-Modal**: Type your queries or use voice commands seamlessly

## 🖼️ Screenshots

![Voice-Assistant-Screenshot](https://github.com/user-attachments/assets/8ab10981-6c69-4066-9cba-e2415db81f5b)

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Google Gemini API key
- [Optional] Stable Diffusion API key for image generation
- [Optional] MongoDB connection string for conversation storage

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/voice-assistant.git
   cd voice-assistant
   ```

2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file for your API keys (optional):
   ```
   GEMINI_API_KEY=your_gemini_api_key
   STABLE_DIFFUSION_API_KEY=your_stable_diffusion_api_key
   MONGODB_CONNECTION_STRING=your_mongodb_connection_string
   ```

### Running the Application

Start the application with:
```bash
streamlit run genai_chatbot.py
```

## 📋 Usage

1. Enter your Google Gemini API key in the sidebar
2. [Optional] Add Stable Diffusion API key for image generation
3. [Optional] Connect to MongoDB to save conversations
4. Use the microphone button or type your query
5. Try commands like:
   - "What's the time?"
   - "Open YouTube"
   - "Tell me about pandas"
   - "Generate image of a sunset over mountains"
   - "Draw a cat playing piano"
6. Use audio controls to pause/resume/stop speech
7. Click 🔊 next to any message to hear it again

## 🧠 API Integration

### Google Gemini

This project uses the Google Generative AI API (Gemini 1.5 Flash model) to generate intelligent responses. You need to:
1. Get an API key from [AI Google Dev](https://ai.google.dev/)
2. Enter the key in the sidebar of the application

### Stable Diffusion

For image generation capabilities:
1. Get an API key from [Stability AI](https://stability.ai/)
2. Enter the key in the sidebar under "Image Generation Setup"

### MongoDB (Optional)

To enable conversation history:
1. Set up a MongoDB database
2. Enter your MongoDB connection string in the sidebar
3. Use the session management features to start new or load previous conversations

## 📜 Available Commands

- **General Queries**: Ask any question to get an AI-generated response
- **Time**: "What's the time?" returns the current time
- **Web Navigation**: "Open YouTube/Google/StackOverflow"
- **Information**: "Tell me about [topic]" searches Wikipedia
- **Image Generation**: "Generate image of [description]" or "Draw [description]"
- **System**: "Goodbye" or "Exit" to end the session

## 🔧 Customization

### Voice Settings

Adjust the following in the sidebar:
- Voice selection (depends on available system voices)
- Speech rate (100-250)
- Volume (0.0-1.0)

### Session Management

With MongoDB connected:
- Create new conversation sessions
- Load previous conversation sessions
- View current session ID

## 📦 Dependencies

- `streamlit`: Web application framework
- `pyttsx3`: Text-to-speech conversion
- `speech_recognition`: Speech-to-text conversion
- `google.generativeai`: Gemini AI interface
- `requests`: API interaction for image generation
- `pymongo`: MongoDB database interaction
- `Pillow`: Image processing
- `wikipedia`: Information retrieval

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 🙏 Acknowledgments

- Google for the Gemini API
- Stability AI for Stable Diffusion
- Streamlit for the awesome web framework
- All open-source contributors whose libraries make this project possible
