import streamlit as st
from colorama import Fore
from dotenv import load_dotenv
import time
import os
import requests
import json

from utils.completions import build_prompt_structure
from utils.completions import FixedFirstChatHistory
from utils.completions import update_chat_history
from utils.logging import fancy_step_tracker
from prompts import BASE_GENERATION_SYSTEM_PROMPT, BASE_REFLECTION_SYSTEM_PROMPT

# Load environment variables
load_dotenv()

# Set page configuration
st.set_page_config(
    page_title="Reflection Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark theme with animations
st.markdown("""
<style>
    /* More user-friendly color palette */
    :root {
        --bg-primary: #1E2130;
        --bg-secondary: #262B3D;
        --bg-tertiary: #323A5E;
        --text-primary: #E6F1FF;
        --text-secondary: #A6B5D9;
        --accent-primary: #5EAEFD;
        --accent-secondary: #9069ED;
        --success: #7AE7A5;
        --warning: #FFD166;
        --error: #FF686B;
        --shadow: rgba(0, 0, 0, 0.2);
    }
    
    /* Dark theme with better text contrast */
    .stApp {
        background-color: var(--bg-primary);
    }
    
    /* Global text color with improved readability */
    body, p, div, span, h1, h2, h3, h4, h5, h6, li, label, td, th {
        color: var(--text-primary) !important;
    }
    
    /* Animation for headers */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes glowing {
        0% { text-shadow: 0 0 5px var(--accent-primary); }
        50% { text-shadow: 0 0 15px var(--accent-primary), 0 0 20px var(--accent-secondary); }
        100% { text-shadow: 0 0 5px var(--accent-primary); }
    }
    
    @keyframes borderGlow {
        0% { border-color: var(--accent-primary); box-shadow: 0 0 5px var(--accent-primary); }
        50% { border-color: var(--accent-secondary); box-shadow: 0 0 10px var(--accent-secondary); }
        100% { border-color: var(--accent-primary); box-shadow: 0 0 5px var(--accent-primary); }
    }
    
    .main-title {
        color: var(--text-primary) !important;
        font-size: 3rem !important;
        font-weight: 700 !important;
        margin-bottom: 1rem !important;
        text-align: center !important;
        animation: fadeIn 1.5s ease-out, glowing 3s infinite !important;
    }
    
    /* Button styles */
    .stButton button {
        background-color: var(--bg-tertiary) !important;
        color: var(--text-primary) !important;
        border-radius: 30px !important;
        padding: 0.5rem 2rem !important;
        font-weight: bold !important;
        border: none !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 2px 5px var(--shadow) !important;
    }
    
    .stButton button:hover {
        background-color: var(--accent-secondary) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 5px 15px var(--shadow) !important;
    }
    
    /* Text input background */
    .stTextInput>div>div {
        background-color: var(--bg-secondary) !important;
        border-radius: 10px !important;
        border: 1px solid var(--bg-tertiary) !important;
    }
    
    /* Text area styles */
    .stTextArea textarea {
        background-color: var(--bg-secondary) !important;
        color: var(--text-primary) !important;
        border-radius: 10px !important;
        border: 1px solid var(--bg-tertiary) !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextArea textarea:focus {
        border: 1px solid var(--accent-primary) !important;
        box-shadow: 0 0 5px var(--accent-primary) !important;
    }
    
    /* Container styles */
    .generation-container {
        animation: fadeIn 0.8s ease-out;
        background-color: var(--bg-secondary);
        border-left: 4px solid var(--accent-primary);
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 15px;
        color: var(--text-primary) !important;
        box-shadow: 0 2px 5px var(--shadow);
    }
    
    .reflection-container {
        animation: fadeIn 0.8s ease-out;
        background-color: var(--bg-secondary);
        border-left: 4px solid var(--success);
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 15px;
        color: var(--text-primary) !important;
        box-shadow: 0 2px 5px var(--shadow);
    }

    /* Expander styles */
    .streamlit-expanderContent {
        background-color: var(--bg-primary) !important;
        color: var(--text-primary) !important;
        border-radius: 10px !important;
        padding: 10px !important;
        animation: fadeIn 0.5s ease-out;
    }
    
    /* Success/info message styling */
    .stSuccess, .stInfo {
        background-color: rgba(94, 174, 253, 0.1) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--accent-primary) !important;
        border-radius: 10px !important;
        animation: borderGlow 3s infinite;
    }
    
    /* Header styling */
    .step-header {
        font-weight: bold;
        padding: 10px;
        color: var(--text-primary) !important;
        background-color: var(--bg-tertiary);
        border-radius: 10px 10px 0 0;
    }
    
    /* Sidebar styling */
    .sidebar .sidebar-content {
        background-color: var(--bg-primary) !important;
    }
    
    /* Progress bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, var(--accent-primary), var(--accent-secondary)) !important;
        background-size: 400% 400% !important;
        animation: gradientShift 3s ease infinite !important;
    }
    
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* Custom content boxes */
    .content-box {
        background-color: var(--bg-secondary);
        border-left: 4px solid var(--accent-primary);
        padding: 15px;
        border-radius: 10px;
        color: var(--text-primary) !important;
        animation: fadeIn 1s ease-out;
        box-shadow: 0 2px 5px var(--shadow);
    }
    
    /* Custom tooltip styling */
    .tooltip {
        position: relative;
        display: inline-block;
        cursor: help;
    }
    
    .tooltip .tooltiptext {
        visibility: hidden;
        width: 200px;
        background-color: var(--bg-secondary);
        color: var(--text-primary);
        text-align: center;
        border-radius: 6px;
        padding: 5px;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        margin-left: -100px;
        opacity: 0;
        transition: opacity 0.3s;
        border: 1px solid var(--accent-primary);
        box-shadow: 0 2px 8px var(--shadow);
    }
    
    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }
    
    /* Custom slider styling */
    .stSlider > div > div {
        background-color: var(--bg-secondary) !important;
    }
    
    /* Divider styling */
    hr {
        border: 1px solid var(--bg-tertiary) !important;
        margin: 2rem 0 !important;
    }
    
    /* Checkboxes */
    .stCheckbox > div > div > label {
        color: var(--text-primary) !important;
    }

    /* Warning styling */
    .stWarning {
        background-color: rgba(255, 209, 102, 0.1) !important;
        color: var(--warning) !important;
        border: 1px solid var(--warning) !important;
    }
    
    /* Error styling */
    .stError {
        background-color: rgba(255, 104, 107, 0.1) !important;
        color: var(--error) !important;
        border: 1px solid var(--error) !important;
    }
    
    /* Code styling */
    .stCodeBlock {
        background-color: var(--bg-primary) !important;
        border: 1px solid var(--bg-tertiary) !important;
        border-radius: 10px !important;
    }
    
    /* Select box styling */
    .stSelectbox > div > div {
        background-color: var(--bg-secondary) !important;
        border-radius: 10px !important;
        border: 1px solid var(--bg-tertiary) !important;
    }
    
    /* Link styling */
    a {
        color: var(--accent-primary) !important;
        text-decoration: none !important;
        transition: all 0.3s ease !important;
    }
    
    a:hover {
        color: var(--accent-secondary) !important;
        text-decoration: underline !important;
    }
    
    /* Fixing dark scrollbars */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--bg-primary);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--bg-tertiary);
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--accent-primary);
    }
</style>
""", unsafe_allow_html=True)

# Custom HTML components for better UI/UX
def animated_title(text):
    st.markdown(f"<h1 class='main-title'>{text}</h1>", unsafe_allow_html=True)

def info_box(text, icon="ℹ️"):
    st.markdown(f"""
    <div style='background-color:#141f33; padding:15px; border-radius:10px; border-left:5px solid #4da6ff; animation: fadeIn 0.8s ease-out;'>
        <span style='font-size:1.5rem'>{icon}</span> <span style='color:#4da6ff'>{text}</span>
    </div>
    """, unsafe_allow_html=True)

def animated_text(text, delay=0):
    st.markdown(f"""
    <div style='animation: fadeIn 1s ease-out {delay}s;'>
        {text}
    </div>
    """, unsafe_allow_html=True)

class ReflectionAgent:
    """
    A class that implements a Reflection Agent, which generates responses and reflects
    on them using the LLM to iteratively improve the interaction.
    """

    def __init__(self, model: str = "llama-3.3-70b-versatile"):
        # Initialize with API key
        self.api_key = "Replace with oyur api"
        if not self.api_key:
            raise ValueError("API key is not set.")
        
        self.model = model
        # Corrected API URL for Groq API based on error message
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        
    def _request_completion(self, history, verbose: int = 0, log_title: str = "COMPLETION", log_color: str = ""):
        try:
            # Convert FixedFirstChatHistory to a simple list of dictionaries
            if isinstance(history, FixedFirstChatHistory):
                # Extract messages from FixedFirstChatHistory object
                messages = history.get_messages()
            else:
                messages = history
                
            # Create a clean list of simple dictionaries
            simple_messages = []
            for msg in messages:
                if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                    simple_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
            
            # Debug
            if verbose > 0:
                print(f"API URL: {self.api_url}")
                print(f"Number of messages: {len(simple_messages)}")
                print(f"First message role: {simple_messages[0]['role'] if simple_messages else 'No messages'}")
            
            # API call with direct dictionaries
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Create payload with proper simple message format
            payload = {
                "model": self.model,
                "messages": simple_messages,
                "temperature": 0.7,
                "max_tokens": 1000
            }
            
            # Debug the payload
            if verbose > 0:
                print("Payload:", json.dumps(payload, indent=2))
            
            # Make the API call
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,  # Use json parameter instead of data for proper serialization
                timeout=60
            )
            
            # Check response
            if response.status_code != 200:
                error_message = f"API call failed with status code {response.status_code}: {response.text}"
                print(error_message)
                raise Exception(error_message)
            
            # Parse response
            result = response.json()
            output = result["choices"][0]["message"]["content"]
            
            if verbose > 0:
                print(log_color, f"\n\n{log_title}\n\n", output)
                
            return output
        except Exception as e:
            print(f"Error in request completion: {str(e)}")
            raise

    def generate(self, generation_history: list, verbose: int = 0) -> str:
        return self._request_completion(
            generation_history, verbose, log_title="GENERATION", log_color=Fore.BLUE
        )

    def reflect(self, reflection_history: list, verbose: int = 0) -> str:
        return self._request_completion(
            reflection_history, verbose, log_title="REFLECTION", log_color=Fore.GREEN
        )
        
    def optimize_prompt(self, user_prompt: str, verbose: int = 0) -> str:
        """
        Send a user prompt to Groq for optimization before using it in the main application.
        
        Args:
            user_prompt (str): The original user prompt
            verbose (int): Verbosity level
            
        Returns:
            str: The optimized prompt
        """
        try:
            # Create an optimization prompt
            optimization_messages = [
                {
                    "role": "system",
                    "content": """You are a prompt optimization expert. Your task is to enhance the user's prompt to make it more detailed, 
                    specific, and optimized for generating high-quality content.
                    
                    Follow these guidelines:
                    1. Maintain the original intent of the prompt
                    2. Add relevant details and specifications
                    3. Improve clarity and structure
                    4. Consider adding formatting suggestions
                    5. Remove any vague or ambiguous language
                    
                    Respond ONLY with the optimized prompt, without explanations or additional text."""
                },
                {
                    "role": "user",
                    "content": f"Please optimize this prompt for better results: {user_prompt}"
                }
            ]
            
            # Send to API for optimization
            if verbose > 0:
                print(f"Optimizing prompt: {user_prompt}")
                
            # Make the API call
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": optimization_messages,
                "temperature": 0.7,
                "max_tokens": 1000
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            
            # Check response
            if response.status_code != 200:
                print(f"Prompt optimization failed: {response.status_code} - {response.text}")
                return user_prompt  # Return original prompt if optimization fails
            
            # Parse response
            result = response.json()
            optimized_prompt = result["choices"][0]["message"]["content"]
            
            if verbose > 0:
                print(f"Original prompt: {user_prompt}")
                print(f"Optimized prompt: {optimized_prompt}")
                
            return optimized_prompt
            
        except Exception as e:
            print(f"Error optimizing prompt: {str(e)}")
            return user_prompt  # Return original prompt if optimization fails

    def run(self, user_msg: str, generation_system_prompt: str = "", reflection_system_prompt: str = "", n_steps: int = 10, verbose: int = 0, optimize_prompt: bool = False) -> tuple:
        if optimize_prompt:
            user_msg = self.optimize_prompt(user_msg, verbose)
            
        generation_system_prompt += BASE_GENERATION_SYSTEM_PROMPT
        reflection_system_prompt += BASE_REFLECTION_SYSTEM_PROMPT

        generation_history = FixedFirstChatHistory(
            [
                build_prompt_structure(prompt=generation_system_prompt, role="system"),
                build_prompt_structure(prompt=user_msg, role="user"),
            ],
            total_length=3,
        )

        reflection_history = FixedFirstChatHistory(
            [build_prompt_structure(prompt=reflection_system_prompt, role="system")],
            total_length=3,
        )

        steps_data = []
        for step in range(n_steps):
            if verbose > 0:
                fancy_step_tracker(step, n_steps)

            # Update Streamlit progress
            progress_value = (step / n_steps)
            st.session_state.progress_bar.progress(progress_value)
            st.session_state.status_text.text(f"Step {step+1}/{n_steps}: Generating content...")

            # Generate the response
            generation = self.generate(generation_history, verbose=verbose)
            update_chat_history(generation_history, generation, "assistant")
            update_chat_history(reflection_history, generation, "user")

            # Update Streamlit progress
            st.session_state.status_text.text(f"Step {step+1}/{n_steps}: Reflecting on content...")

            # Reflect and critique the generation
            critique = self.reflect(reflection_history, verbose=verbose)
            
            steps_data.append({
                "step": step + 1,
                "generation": generation,
                "critique": critique
            })

            if "<OK>" in critique:
                break

            update_chat_history(generation_history, critique, "user")
            update_chat_history(reflection_history, critique, "assistant")

        # Final progress update
        st.session_state.progress_bar.progress(1.0)
        st.session_state.status_text.text("Completed!")
        
        return generation, steps_data

# Template prompts
TEMPLATE_PROMPTS = {
    "Algorithm Design": "Design a simple algorithm to find the longest palindrome in a string.",
    "Essay Outline": "Create an outline for an essay about the impact of artificial intelligence on modern education.",
    "Marketing Copy": "Write marketing copy for a new fitness app that helps users track their workouts and nutrition.",
    "Story Idea": "Develop a short story idea about a time traveler who accidentally changes history.",
    "Product Description": "Write a product description for a smart home device that controls all appliances via voice commands."
}

# Streamlit UI
def main():
    try:
        # Title and description with animation
        animated_title("🧠 Reflection Agent")
        
        info_box("This app generates content and uses AI reflection to improve it iteratively until it meets quality standards.", "🔍")

        # Interactive sidebar
        with st.sidebar:
            st.markdown("<h2 style='text-align:center; color:var(--text-primary);'>⚙️ Settings</h2>", unsafe_allow_html=True)
            
            # Model selection with animation
            model = st.selectbox(
                "Select Model",
                ["llama-3.3-70b-versatile", "mixtral-8x7b-32768", "gemma-7b-it"],
                index=0
            )
            
            # Steps slider with tooltip
            st.markdown("""
            <div class="tooltip">Steps
              <span class="tooltiptext">More steps allow for more iterations of improvement</span>
            </div>
            """, unsafe_allow_html=True)
            n_steps = st.slider("", 1, 10, 3, key="steps_slider")
            
            # Prompt optimization option
            st.markdown("<h3 style='margin-top:20px; color:var(--text-primary);'>🚀 Advanced Options</h3>", unsafe_allow_html=True)
            optimize_prompt = st.checkbox("Optimize prompt", value=True, help="Let AI enhance your prompt before processing")
            
            # Template section
            st.markdown("<h3 style='margin-top:30px; color:var(--text-primary);'>📝 Templates</h3>", unsafe_allow_html=True)
            template_selected = st.selectbox("Choose a starting point", list(TEMPLATE_PROMPTS.keys()))
            
            if st.button("Use Template"):
                st.session_state.template_content = TEMPLATE_PROMPTS[template_selected]
            
            # Help section
            st.markdown("<h3 style='margin-top:30px; color:var(--text-primary);'>💡 Tips</h3>", unsafe_allow_html=True)
            with st.expander("How it works", expanded=False):
                st.markdown("""
                1. **Input a prompt**: What content do you want to generate?
                2. **AI optimizes your prompt** (if enabled): Makes your prompt more specific and detailed
                3. **AI generates content**: Based on your optimized prompt
                4. **AI reflects & improves**: Reviews and refines the content
                5. **Process continues**: Until quality standards are met
                """)

        # Main content area with animation effects
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Initialize template content if it doesn't exist
            if 'template_content' not in st.session_state:
                st.session_state.template_content = ""
                
            user_input = st.text_area(
                "What would you like the AI to generate?", 
                height=150,
                key="input_area",
                value=st.session_state.template_content,
                placeholder="Enter your prompt here... e.g., 'Write a blog post about artificial intelligence'"
            )
        
        with col2:
            st.markdown("<h4 style='color:var(--text-primary);'>Example prompts:</h4>", unsafe_allow_html=True)
            st.markdown("• Write a blog post about sustainable living")
            st.markdown("• Create a tutorial for learning Python")
            st.markdown("• Design a workout routine for beginners")
        
        # Generate button with animation
        generate_col1, generate_col2, generate_col3 = st.columns([1, 2, 1])
        with generate_col2:
            generate_button = st.button("✨ Generate Content", key="generate_button", use_container_width=True)
        
        if generate_button:
            if not user_input:
                st.warning("⚠️ Please enter a prompt first!")
                return

            # Initialize session state for progress tracking
            st.session_state.progress_bar = st.progress(0)
            st.session_state.status_text = st.empty()
            
            # Create container for steps with animation
            steps_container = st.container()
            
            try:
                # Create a placeholder for optimized prompt
                optimized_prompt_container = st.empty()
                
                # Show a loading animation
                with st.spinner("🧠 Thinking..."):
                    # Initialize and run the agent
                    agent = ReflectionAgent(model=model)
                    
                    # If prompt optimization is enabled, show it to the user
                    if optimize_prompt:
                        with st.spinner("✨ Optimizing your prompt..."):
                            optimized_prompt = agent.optimize_prompt(user_input, verbose=1)
                            # Display the optimized prompt if it's different from the original
                            if optimized_prompt != user_input:
                                optimized_prompt_container.markdown(f"""
                                <div style='background-color:var(--bg-secondary); border-left:4px solid var(--accent-secondary); 
                                     padding:15px; border-radius:10px; margin:15px 0; animation: fadeIn 0.8s ease-out;'>
                                    <strong>✨ Optimized Prompt:</strong><br>
                                    {optimized_prompt.replace("<", "&lt;").replace(">", "&gt;")}
                                </div>
                                """, unsafe_allow_html=True)
                    else:
                        optimized_prompt = user_input
                    
                    # Run the agent with the original or optimized prompt
                    final_response, steps_data = agent.run(
                        user_msg=optimized_prompt if optimize_prompt else user_input,
                        n_steps=n_steps,
                        verbose=1,
                        optimize_prompt=False  # Don't optimize again
                    )
                
                # Display each step with animations
                with steps_container:
                    # First, add a visual timeline to show the progression
                    st.markdown("""
                    <div style='display:flex; justify-content:space-between; margin:20px 0 30px 0;'>
                    """, unsafe_allow_html=True)
                    
                    for i, step_data in enumerate(steps_data):
                        progress_percent = (i+1) / len(steps_data) * 100
                        active_class = "active" if i == len(steps_data)-1 else ""
                        st.markdown(f"""
                        <div style='flex:1; text-align:center;'>
                            <div style='display:inline-block; width:30px; height:30px; border-radius:50%; 
                                background-color:var(--accent-primary); color:var(--text-primary); 
                                text-align:center; line-height:30px; margin-bottom:5px; 
                                box-shadow: 0 0 {10 if active_class else 0}px var(--accent-primary);
                                animation: fadeIn 0.8s ease-out;'>
                                {step_data['step']}
                            </div>
                            <div style='width:100%; height:4px; margin-top:10px; background-color:var(--bg-tertiary);'>
                                <div style='width:{progress_percent}%; height:100%; background-color:var(--accent-primary);'></div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Display the detailed steps in cards
                    for i, step_data in enumerate(steps_data):
                        step_number = step_data['step']
                        is_last_step = i == len(steps_data)-1
                        
                        # Create a card for each step with better visual hierarchy
                        st.markdown(f"""
                        <div style='background-color:var(--bg-secondary); border-radius:15px; margin:30px 0; 
                             box-shadow:0 4px 10px var(--shadow); overflow:hidden; animation:fadeIn 0.8s ease-out;'>
                            <div style='background-color:var(--bg-tertiary); padding:15px; display:flex; justify-content:space-between; align-items:center;'>
                                <h3 style='margin:0; color:var(--text-primary);'>Step {step_number} of {len(steps_data)}</h3>
                                <div style='color:var(--accent-primary); font-weight:bold;'>
                                    {f"✓ Final" if is_last_step else ""}
                                </div>
                            </div>
                            <div style='padding:20px;'>
                        """, unsafe_allow_html=True)
                        
                        # Generation section
                        st.markdown(f"""
                        <div style='margin-bottom:25px;'>
                            <div style='display:flex; align-items:center; margin-bottom:15px;'>
                                <div style='background-color:var(--accent-primary); width:35px; height:35px; border-radius:50%; 
                                     display:flex; justify-content:center; align-items:center; margin-right:10px;'>
                                    <span style='color:var(--text-primary); font-size:18px;'>🎯</span>
                                </div>
                                <h4 style='margin:0; color:var(--text-primary);'>Generation</h4>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # Safely escape any HTML tags
                        safe_generation = step_data['generation'].replace("<", "&lt;").replace(">", "&gt;")
                        
                        # Format the generation content with line breaks
                        formatted_generation = safe_generation.replace("\n", "<br>")
                        
                        st.markdown(f"""
                            <div style='background-color:rgba(94, 174, 253, 0.1); padding:20px; border-radius:10px; 
                                 border-left:4px solid var(--accent-primary); color:var(--text-primary);'>
                                {formatted_generation}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Reflection section
                        st.markdown(f"""
                        <div>
                            <div style='display:flex; align-items:center; margin-bottom:15px;'>
                                <div style='background-color:var(--success); width:35px; height:35px; border-radius:50%; 
                                     display:flex; justify-content:center; align-items:center; margin-right:10px;'>
                                    <span style='color:var(--text-primary); font-size:18px;'>💭</span>
                                </div>
                                <h4 style='margin:0; color:var(--text-primary);'>Reflection & Changes</h4>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        if "<OK>" in step_data['critique']:
                            st.markdown("""
                            <div style='background-color:rgba(122, 231, 165, 0.1); padding:20px; border-radius:10px; 
                                 border-left:4px solid var(--success); color:var(--text-primary);'>
                                ✅ Content is satisfactory! No further improvements needed.
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            # Analyze the critique to highlight changes
                            # Safely escape any HTML tags in the critique
                            safe_critique = step_data['critique'].replace("<", "&lt;").replace(">", "&gt;")
                            
                            # Extract specific recommendations and format them nicely
                            import re
                            recommendations = []
                            numbered_pattern = re.compile(r'(?:\d+\.\s*|\*\s*)([^\n\d\*][^\n]+)')
                            matches = numbered_pattern.findall(safe_critique)
                            
                            # Format the critique content with line breaks
                            formatted_critique = safe_critique.replace("\n", "<br>")
                            
                            # Display the full reflection
                            st.markdown(f"""
                            <div style='background-color:rgba(122, 231, 165, 0.1); padding:20px; border-radius:10px; 
                                 border-left:4px solid var(--success); color:var(--text-primary);'>
                                {formatted_critique}
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # If we have recommendations, show them in a more structured format
                            if matches:
                                st.markdown("""
                                <div style='margin-top:20px;'>
                                    <h5 style='color:var(--text-primary); margin-bottom:10px;'>Key Improvements Made:</h5>
                                    <ul style='color:var(--text-primary); padding-left:20px;'>
                                """, unsafe_allow_html=True)
                                
                                for rec in matches:
                                    st.markdown(f"<li>{rec}</li>", unsafe_allow_html=True)
                                
                                st.markdown("</ul></div>", unsafe_allow_html=True)
                            
                        st.markdown("</div></div></div>", unsafe_allow_html=True)
                
                # Clear progress indicators with an animation
                st.session_state.progress_bar.empty()
                st.session_state.status_text.empty()
                
                # Show final response with animation
                st.markdown("<hr>", unsafe_allow_html=True)
                st.markdown("""
                <h2 style='text-align:center; color:var(--text-primary); animation: fadeIn 1s ease-out;'>
                    ✨ Final Result ✨
                </h2>
                """, unsafe_allow_html=True)
                
                # Safely escape any HTML tags in the final response
                safe_response = final_response.replace("<", "&lt;").replace(">", "&gt;")
                st.markdown(f"""
                <div style='background-color:var(--bg-secondary); padding:20px; border-radius:10px; border:2px solid var(--accent-primary); 
                     animation: fadeIn 1.5s ease-out; box-shadow: 0 0 15px rgba(77, 166, 255, 0.3);'>
                    {safe_response}
                </div>
                """, unsafe_allow_html=True)
                
                # Copy button for final output
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("📋 Copy to Clipboard", key="copy_button"):
                    st.code(final_response)
                    st.success("Content copied! You can now paste it wherever you need.")
                
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                import traceback
                st.error(traceback.format_exc())
    
    except Exception as e:
        st.error(f"Application error: {str(e)}")

if __name__ == "__main__":
    main() 
