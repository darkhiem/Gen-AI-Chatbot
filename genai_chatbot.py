import streamlit as st
import pyttsx3
import speech_recognition as sr
import datetime
import wikipedia
import webbrowser
import os
import smtplib
import google.generativeai as genai
import threading
import time
from io import BytesIO
import base64
import pymongo
import uuid
import queue
import requests
from PIL import Image
import io

# Set page config
st.set_page_config(page_title="Voice Assistant", layout="wide")

# Initialize session state variables if they don't exist
if 'conversation' not in st.session_state:
    st.session_state.conversation = []
if 'listening' not in st.session_state:
    st.session_state.listening = False
if 'initialized' not in st.session_state:
    st.session_state.initialized = False
if 'speaking' not in st.session_state:
    st.session_state.speaking = False
if 'paused' not in st.session_state:
    st.session_state.paused = False
if 'user_input' not in st.session_state:
    st.session_state.user_input = ""
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""
if 'gemini_initialized' not in st.session_state:
    st.session_state.gemini_initialized = False
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if 'mongodb_connected' not in st.session_state:
    st.session_state.mongodb_connected = False
if 'mongo_client' not in st.session_state:
    st.session_state.mongo_client = None
if 'stop_speaking' not in st.session_state:
    st.session_state.stop_speaking = False
if 'speech_queue' not in st.session_state:
    st.session_state.speech_queue = queue.Queue()
if 'speech_thread_running' not in st.session_state:
    st.session_state.speech_thread_running = False
# New state variables for image generation
if 'stable_diffusion_api_key' not in st.session_state:
    st.session_state.stable_diffusion_api_key = ""
if 'image_generation_enabled' not in st.session_state:
    st.session_state.image_generation_enabled = False
if 'generated_images' not in st.session_state:
    st.session_state.generated_images = []

# App title and description
st.title("Voice Assistant")
st.markdown("Your personal AI voice assistant with text and image generation")

# Initialize the voice engine - Modified for better reliability
def init_engine():
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        # Set voice (try to use a female voice if available)
        if len(voices) > 1:
            engine.setProperty('voice', voices[1].id)  # Female voice
        engine.setProperty('rate', 170)  # Adjust speech speed
        engine.setProperty('volume', 1.0)  # Max volume
        return engine
    except Exception as e:
        st.error(f"Error initializing speech engine: {e}")
        return None

# Initialize MongoDB connection
def init_mongodb(connection_string):
    try:
        client = pymongo.MongoClient(connection_string)
        # Test the connection
        client.admin.command('ping')
        st.session_state.mongodb_connected = True
        st.session_state.mongo_client = client
        return client
    except Exception as e:
        st.error(f"Failed to connect to MongoDB: {e}")
        st.session_state.mongodb_connected = False
        return None

# Save conversation to MongoDB
def save_to_mongodb(message):
    if not st.session_state.mongodb_connected or not st.session_state.mongo_client:
        return
    
    try:
        db = st.session_state.mongo_client.assistant_db
        collection = db.conversations
        
        message_data = {
            "session_id": st.session_state.session_id,
            "timestamp": datetime.datetime.now(),
            "role": message["role"],
            "content": message["content"]
        }
        
        # Add image URL if exists
        if "image_url" in message:
            message_data["image_url"] = message["image_url"]
        
        collection.insert_one(message_data)
    except Exception as e:
        st.error(f"Failed to save to MongoDB: {e}")

# Load conversation history from MongoDB
def load_from_mongodb(session_id=None):
    if not st.session_state.mongodb_connected or not st.session_state.mongo_client:
        return []
    
    try:
        db = st.session_state.mongo_client.assistant_db
        collection = db.conversations
        
        if session_id:
            # Load specific session
            cursor = collection.find({"session_id": session_id}).sort("timestamp", 1)
        else:
            # Load list of session IDs
            cursor = collection.distinct("session_id")
            return cursor
        
        conversation = []
        for doc in cursor:
            message = {
                "role": doc["role"],
                "content": doc["content"]
            }
            
            # Add image URL if exists
            if "image_url" in doc:
                message["image_url"] = doc["image_url"]
                
            conversation.append(message)
        
        return conversation
    except Exception as e:
        st.error(f"Failed to load from MongoDB: {e}")
        return []

# Initialize Gemini AI
def init_gemini(api_key):
    if not api_key:
        return False
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash-001')
        convo = model.start_chat()
        return convo
    except Exception as e:
        st.error(f"Error initializing Gemini API: {e}")
        return False

# Initialize Stable Diffusion API
def init_stable_diffusion(api_key):
    if not api_key:
        return False
    
    try:
        # Simple test request to validate API key
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        # Just checking if the API key format is valid, not making a real request
        if len(api_key) < 8:  # Basic validation
            return False
            
        st.session_state.image_generation_enabled = True
        st.session_state.stable_diffusion_api_key = api_key
        return True
    except Exception as e:
        st.error(f"Error initializing Stable Diffusion API: {e}")
        return False

# Text to image generation using Stable Diffusion API
def generate_image(prompt):
    if not st.session_state.image_generation_enabled:
        return None
    
    try:
        url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {st.session_state.stable_diffusion_api_key}"
        }
        
        payload = {
            "text_prompts": [{"text": prompt}],
            "cfg_scale": 7,
            "height": 1024,
            "width": 1024,
            "samples": 1,
            "steps": 30,
        }
        
        with st.spinner("Generating image..."):
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code != 200:
                st.error(f"Non-200 response: {response.text}")
                return None
                
            data = response.json()
            
            # Process and return the image
            for i, image in enumerate(data["artifacts"]):
                image_data = base64.b64decode(image["base64"])
                img = Image.open(io.BytesIO(image_data))
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='PNG')
                img_byte_arr = img_byte_arr.getvalue()
                
                # Add to session state
                img_b64 = base64.b64encode(img_byte_arr).decode()
                return f"data:image/png;base64,{img_b64}"
                
        return None
    except Exception as e:
        st.error(f"Error generating image: {e}")
        return None

# Callback for API key input
def process_api_key():
    api_key = st.session_state.api_key_input
    if api_key:
        with st.spinner("Initializing Gemini API..."):
            st.session_state.convo = init_gemini(api_key)
            if st.session_state.convo:
                st.session_state.gemini_initialized = True
                st.session_state.api_key = api_key  # Save it for later use

# Callback for Stable Diffusion API key
def process_sd_api_key():
    api_key = st.session_state.sd_api_key_input
    if api_key:
        with st.spinner("Initializing Image Generation API..."):
            if init_stable_diffusion(api_key):
                st.success("Image generation enabled!")

# Callback for MongoDB connection
def process_mongodb_connection():
    connection_string = st.session_state.mongodb_connection_string
    if connection_string:
        with st.spinner("Connecting to MongoDB..."):
            client = init_mongodb(connection_string)
            if client:
                st.success("Connected to MongoDB successfully!")

# Fixed speech functions
def speak_worker():
    """Worker thread that processes speech queue"""
    st.session_state.speech_thread_running = True
    
    while True:
        try:
            # Get text from queue with a timeout to allow checking for app exit
            try:
                text = st.session_state.speech_queue.get(timeout=0.5)
            except queue.Empty:
                # No items in queue, check if we should exit
                if not st.session_state.speech_thread_running:
                    break
                continue
            
            # Initialize engine for each speech request to avoid resource issues
            engine = init_engine()
            if not engine:
                st.session_state.speaking = False
                st.session_state.speech_queue.task_done()
                continue
                
            st.session_state.speaking = True
            st.session_state.stop_speaking = False
            
            # Split text into sentences for better pause control
            sentences = text.replace('. ', '.|').replace('? ', '?|').replace('! ', '!|').split('|')
            
            for sentence in sentences:
                if st.session_state.stop_speaking:
                    break
                
                while st.session_state.paused:
                    time.sleep(0.1)
                    if st.session_state.stop_speaking:
                        break
                
                if sentence.strip():
                    try:
                        engine.say(sentence)
                        engine.runAndWait()
                    except Exception as e:
                        st.error(f"Speech error: {e}")
                        break
            
            # Clean up engine after use
            try:
                engine.stop()
            except:
                pass
            
            st.session_state.speaking = False
            st.session_state.paused = False
            st.session_state.speech_queue.task_done()
            
        except Exception as e:
            st.error(f"Speech worker error: {e}")
            st.session_state.speaking = False
            st.session_state.paused = False
            try:
                st.session_state.speech_queue.task_done()
            except:
                pass

def start_speech_worker():
    """Start the speech worker thread if not already running"""
    if not st.session_state.speech_thread_running:
        threading.Thread(target=speak_worker, daemon=True).start()

def speak_text(text):
    """Add text to the speech queue"""
    start_speech_worker()
    st.session_state.speech_queue.put(text)

def pause_resume_speech():
    """Toggle pause/resume of speech"""
    st.session_state.paused = not st.session_state.paused

def stop_speech():
    """Stop speech completely"""
    st.session_state.stop_speaking = True
    st.session_state.paused = False
    
    # Clear the queue
    while not st.session_state.speech_queue.empty():
        try:
            st.session_state.speech_queue.get_nowait()
            st.session_state.speech_queue.task_done()
        except:
            pass

def read_message_aloud(message_idx):
    """Read a specific message from the conversation aloud"""
    if 0 <= message_idx < len(st.session_state.conversation):
        message = st.session_state.conversation[message_idx]["content"]
        speak_text(message)

# Listening function
def listen_for_command():
    """Listens for voice input and converts to text"""
    st.session_state.listening = True
    status_placeholder = st.empty()
    status_placeholder.info("Listening... (Speak now)")
    
    r = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            r.pause_threshold = 1
            r.adjust_for_ambient_noise(source)
            audio = r.listen(source, timeout=5, phrase_time_limit=5)
        
        status_placeholder.info("Processing your speech...")
        query = r.recognize_google(audio, language='en-in')
        status_placeholder.success(f"I heard: {query}")
        st.session_state.listening = False
        return query.lower()
    except sr.UnknownValueError:
        status_placeholder.error("Sorry, I didn't catch that.")
    except sr.RequestError:
        status_placeholder.error("Speech recognition service is unavailable.")
    except Exception as e:
        status_placeholder.error(f"Error: {str(e)}")
    
    st.session_state.listening = False
    return None

def query_gemini(query):
    """Queries the Gemini AI model, falls back to Wikipedia if unavailable"""
    if not st.session_state.gemini_initialized:
        try:
            results = wikipedia.summary(query, sentences=2)
            return f"According to Wikipedia: {results}"
        except:
            return "I couldn't find information on that. Please initialize Gemini API for better responses."
    
    try:
        st.session_state.convo.send_message(query)
        response = st.session_state.convo.last.text.replace('*', '')
        return response
    except Exception as e:
        return f"Sorry, I couldn't process that request. Error: {str(e)}"

def handle_command(query):
    """Process the command and return a response"""
    if not query:
        return "I didn't hear anything. Please try again."
    
    # Check if this is an image generation request
    generate_img = False
    img_prompt = None
    
    if query.startswith("generate image") or query.startswith("create image") or "draw" in query or "picture of" in query:
        generate_img = True
        # Extract the prompt from the query
        if query.startswith("generate image"):
            img_prompt = query.replace("generate image", "", 1).strip()
        elif query.startswith("create image"):
            img_prompt = query.replace("create image", "", 1).strip()
        elif "draw" in query:
            img_prompt = query.replace("draw", "", 1).strip()
        elif "picture of" in query:
            img_prompt = query.replace("picture of", "", 1).strip()
        
        # If no specific prompt, use the whole query
        if not img_prompt:
            img_prompt = query
    
    # Add user query to conversation
    user_message = {"role": "user", "content": query}
    st.session_state.conversation.append(user_message)
    
    # Save to MongoDB if connected
    if st.session_state.mongodb_connected:
        save_to_mongodb(user_message)
    
    # Process different commands
    if generate_img and st.session_state.image_generation_enabled:
        response = f"Generating an image based on: {img_prompt}"
        img_url = generate_image(img_prompt)
        if img_url:
            assistant_message = {
                "role": "assistant", 
                "content": response,
                "image_url": img_url
            }
        else:
            assistant_message = {
                "role": "assistant", 
                "content": "I'm sorry, I couldn't generate that image. Please try a different description."
            }
    
    elif 'wikipedia' in query:
        response = "Searching Wikipedia..."
        query = query.replace("wikipedia", "")
        try:
            results = wikipedia.summary(query, sentences=2)
            response = f"According to Wikipedia: {results}"
        except:
            response = "Sorry, I couldn't find any results on Wikipedia."
        assistant_message = {"role": "assistant", "content": response}
    
    elif 'open youtube' in query:
        response = "Opening YouTube in a new tab."
        webbrowser.open_new_tab("https://youtube.com")
        assistant_message = {"role": "assistant", "content": response}
    
    elif 'open google' in query:
        response = "Opening Google in a new tab."
        webbrowser.open_new_tab("https://google.com")
        assistant_message = {"role": "assistant", "content": response}
    
    elif 'open stackoverflow' in query:
        response = "Opening Stack Overflow in a new tab."
        webbrowser.open_new_tab("https://stackoverflow.com")
        assistant_message = {"role": "assistant", "content": response}
    
    elif 'the time' in query:
        strTime = datetime.datetime.now().strftime("%H:%M:%S")
        response = f"The time is {strTime}"
        assistant_message = {"role": "assistant", "content": response}
    
    elif 'goodbye' in query or 'exit' in query:
        response = "Have a good day! Refresh the page to start a new session."
        assistant_message = {"role": "assistant", "content": response}
    
    else:
        # Handle general queries using Gemini AI or Wikipedia
        response = query_gemini(query)
        assistant_message = {"role": "assistant", "content": response}
    
    # Add assistant response to conversation
    st.session_state.conversation.append(assistant_message)
    
    # Save to MongoDB if connected
    if st.session_state.mongodb_connected:
        save_to_mongodb(assistant_message)
    
    # Speak the response (text part only)
    speak_text(assistant_message["content"])
    
    return response

# Callback function to handle user input
def submit_text():
    if st.session_state.user_input:
        query = st.session_state.user_input
        st.session_state.user_input = ""  # Clear the input
        handle_command(query)

# Initialize speech engine - done once at page load, but not cached
engine = init_engine()

# Sidebar controls
with st.sidebar:
    st.header("Voice Settings")
    
    # Voice selection - modified to handle potential errors
    if engine:
        try:
            voices = engine.getProperty('voices')
            voice_options = {voice.name: i for i, voice in enumerate(voices)}
            selected_voice = st.selectbox("Select Voice", options=list(voice_options.keys()), index=1 if len(voices) > 1 else 0)
            engine.setProperty('voice', voices[voice_options[selected_voice]].id)
            
            # Speech rate
            speech_rate = st.slider("Speech Rate", min_value=100, max_value=250, value=170, step=10)
            engine.setProperty('rate', speech_rate)
            
            # Speech volume
            speech_volume = st.slider("Volume", min_value=0.0, max_value=1.0, value=1.0, step=0.1)
            engine.setProperty('volume', speech_volume)
        except Exception as e:
            st.error(f"Error configuring voice settings: {e}")
    else:
        st.error("Speech engine not available. Some features will be limited.")
    
    st.markdown("---")
    
    # Gemini API setup
    st.header("Gemini API Setup")
    if not st.session_state.gemini_initialized:
        st.text_input(
            "Enter your Gemini API Key:", 
            type="password",
            key="api_key_input",
            on_change=process_api_key
        )
        st.caption("Get a key at: https://ai.google.dev/")
    else:
        st.success("✅ Gemini API initialized successfully!")
        if st.button("Reset API Key"):
            st.session_state.gemini_initialized = False
            st.session_state.api_key = ""
            st.rerun()
    
    st.markdown("---")
    
    # Stable Diffusion API setup
    st.header("Image Generation Setup")
    if not st.session_state.image_generation_enabled:
        st.text_input(
            "Enter Stable Diffusion API Key:", 
            type="password",
            key="sd_api_key_input",
            on_change=process_sd_api_key
        )
        st.caption("Get a key at: https://stability.ai/")
    else:
        st.success("✅ Image generation enabled!")
        if st.button("Reset Image API"):
            st.session_state.image_generation_enabled = False
            st.session_state.stable_diffusion_api_key = ""
            st.rerun()
    
    st.markdown("---")
    
    # MongoDB setup
    st.header("MongoDB Connection")
    if not st.session_state.mongodb_connected:
        st.text_input(
            "MongoDB Connection String:",
            placeholder="mongodb://username:password@host:port/",
            type="password",
            key="mongodb_connection_string",
            on_change=process_mongodb_connection
        )
        st.caption("Format: mongodb://username:password@host:port/")
    else:
        st.success("✅ Connected to MongoDB!")
        
        # Session management
        st.subheader("Session Management")
        
        # Create new session button
        if st.button("Start New Session"):
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.conversation = []
            st.rerun()
        
        # Load previous sessions
        previous_sessions = load_from_mongodb()
        if previous_sessions and len(previous_sessions) > 0:
            selected_session = st.selectbox(
                "Load Previous Session:",
                options=previous_sessions,
                format_func=lambda x: f"Session {x[:8]}... ({x})"
            )
            
            if st.button("Load Selected Session"):
                conversation = load_from_mongodb(selected_session)
                if conversation:
                    st.session_state.conversation = conversation
                    st.session_state.session_id = selected_session
                    st.rerun()

# Main interface
col1, col2 = st.columns([2, 1])

with col1:
    # Display conversation
    st.subheader("Conversation")
    chat_container = st.container(height=400)
    
    with chat_container:
        for i, message in enumerate(st.session_state.conversation):
            if message["role"] == "user":
                user_col, btn_col = st.columns([10, 1])
                with user_col:
                    st.markdown(f"**You:** {message['content']}")
            else:
                msg_col, btn_col = st.columns([10, 1])
                with msg_col:
                    st.markdown(f"**Assistant:** {message['content']}")
                    # Display image if exists
                    if "image_url" in message:
                        st.image(message["image_url"], caption="Generated Image")
                with btn_col:
                    # Add a read aloud button for each assistant message
                    button_key = f"read_{i}"  # Create unique key for each button
                    if st.button("🔊", key=button_key, help="Read this message aloud"):
                        read_message_aloud(i)
    
    # Audio controls
    audio_cols = st.columns(3)
    with audio_cols[0]:
        if st.session_state.speaking and not st.session_state.paused:
            if st.button("⏸️ Pause", key="pause_button"):
                pause_resume_speech()
        elif st.session_state.speaking and st.session_state.paused:
            if st.button("▶️ Resume", key="resume_button"):
                pause_resume_speech()
    
    with audio_cols[1]:
        if st.session_state.speaking:
            if st.button("⏹️ Stop", key="stop_button"):
                stop_speech()
    
    # Text input option - Using a callback to handle the input
    st.text_input(
        "Type your message:", 
        key="user_input",
        on_change=submit_text
    )

with col2:
    # Voice input option
    st.subheader("Voice Control")
    
    mic_col, status_col = st.columns(2)
    
    with mic_col:
        if st.button("🎤 Activate Microphone", disabled=st.session_state.listening):
            query = listen_for_command()
            if query:
                handle_command(query)
                st.rerun()
    
    with status_col:
        if st.session_state.listening:
            st.info("Listening...")
        elif st.session_state.speaking and st.session_state.paused:
            st.warning("Paused")
        elif st.session_state.speaking:
            st.info("Speaking...")
        else:
            st.success("Ready")
    
    # Welcome message on first load
    if len(st.session_state.conversation) == 0:
        # Wish user based on time
        hour = int(datetime.datetime.now().hour)
        if 0 <= hour < 12:
            greeting = "Good Morning!"
        elif 12 <= hour < 18:
            greeting = "Good Afternoon!"
        else:
            greeting = "Good Evening!"
        
        welcome_msg = f"{greeting} I'm your AI Assistant. Please tell me how I can help you."
        welcome_message = {"role": "assistant", "content": welcome_msg}
        st.session_state.conversation.append(welcome_message)
        
        # Save to MongoDB if connected
        if st.session_state.mongodb_connected:
            save_to_mongodb(welcome_message)
            
        speak_text(welcome_msg)
        
    # How to use instructions
    st.markdown("---")
    st.subheader("How to Use")
    st.markdown("""
    1. Enter your Gemini API key in the sidebar
    2. Add Stable Diffusion API key for image generation
    3. Connect to MongoDB (optional) to save chats
    4. Use the microphone button or type your query
    5. Try commands like:
       - "What's the time?"
       - "Open YouTube"
       - "Tell me about pandas"
       - "Generate image of a sunset over mountains"
       - "Draw a cat playing piano"
    6. Use audio controls to pause/resume/stop speech
    7. Click 🔊 next to any message to hear it again
    """)
    
    # Session info
    if st.session_state.mongodb_connected:
        st.markdown("---")
        st.subheader("Current Session")
        st.code(st.session_state.session_id)

# Clean up when app is closed
def cleanup():
    # Stop the speech thread
    st.session_state.speech_thread_running = False
    st.session_state.stop_speaking = True
    
    # Wait for queue to empty
    if 'speech_queue' in st.session_state:
        while not st.session_state.speech_queue.empty():
            try:
                st.session_state.speech_queue.get_nowait()
                st.session_state.speech_queue.task_done()
            except:
                pass

# Register cleanup
import atexit
atexit.register(cleanup)