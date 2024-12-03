from flask import Flask, request, render_template, jsonify, Response, stream_with_context
from flask_cors import CORS
import os
from dotenv import load_dotenv
from openai import AzureOpenAI
import json
import time
import requests
import logging
from collections import defaultdict

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Set Azure API endpoints and credentials
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
DALLE_ENDPOINT = os.getenv("DALLE_ENDPOINT")
DALLE_API_KEY = os.getenv("DALLE_API_KEY")
DALLE_DEPLOYMENT = os.getenv("DALLE_DEPLOYMENT", "dall-e-3")

# Initialize OpenAI client for GPT-4
openai_client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    api_version="2024-02-01",
    azure_endpoint=AZURE_OPENAI_ENDPOINT
)

# Initialize DALL-E client
dalle_client = AzureOpenAI(
    api_key=DALLE_API_KEY,
    api_version="2024-02-01",
    azure_endpoint=DALLE_ENDPOINT
)

app = Flask(__name__, template_folder='templates')
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "allow_headers": ["Content-Type"],
        "expose_headers": ["Content-Type"]
    }
})

# Store conversation context
conversation_context = defaultdict(str)

def stream_response(text):
    """Helper function to stream text response"""
    for char in text:
        json_data = json.dumps({"text": char})
        yield f"data: {json_data}\n\n"
        time.sleep(0.01)  # Add a small delay for smoother streaming

def analyze_dream(dream_text):
    """Analyze the dream text and return insights"""
    try:
        logger.info(f"Analyzing dream: {dream_text}")
        
        # Store dream in context
        conversation_context["last_dream"] = dream_text
        
        # First, get the complete analysis
        system_prompt = """You are a professional dream interpreter with extensive knowledge of psychology, symbolism, mythology, and creative analysis. Your goal is to help users understand the deeper meaning of their dreams. You must carefully analyze the user's dream description, extract key themes, and provide symbolic interpretations that are insightful, meaningful, and relatable. Follow this process:

Understand the Dream: Read the user's dream description and identify the most prominent elements, actions, and emotions. Focus on the dream’s key symbols and context.
Generate Themes: Based on the dream's key elements, identify the overarching themes. Themes could include emotions (e.g., fear, joy), settings (e.g., water, sky, forest), actions (e.g., flying, running, falling), or archetypes (e.g., hero, shadow, guide).
Provide Symbolism: For each theme, explain its symbolic meaning, considering psychological, cultural, or mythological contexts. Tie the symbols to the dreamer's possible emotions, life situations, or subconscious desires.
Be Empathetic and Creative: Frame your responses in an empathetic and imaginative tone, encouraging the dreamer to reflect on the interpretation in their personal context.
Output Structure:

Themes: List the key themes with a brief explanation.
Symbolism: Provide a detailed interpretation of the symbolic meaning behind each theme.
Reflection Prompt: Suggest how the dreamer can reflect on or apply these insights in their waking life.
Example Interaction:

Input: "I was flying through a stormy sky, chased by glowing orbs."
Output:
Themes:
Flying: A desire for freedom or escape.
Storm: Facing turbulence, chaos, or challenges in life.
Chased by glowing orbs: Anxiety or pressure from unknown or external forces.
Symbolism:
Flying represents ambition, the need to rise above current circumstances, or a longing for independence.
The storm reflects emotional or situational turbulence, possibly external conflicts or internal struggles.
The glowing orbs symbolize persistent fears, responsibilities, or pressures that feel overwhelming but may also carry hidden potential or guidance.
Reflection Prompt: Consider what areas of your life feel chaotic or restrictive. How can you address these challenges to achieve the freedom you desire? What hidden opportunities might exist within your current pressures?
Always focus on delivering value, insight, and encouragement to the dreamer.
        """

        response = openai_client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze this dream: {dream_text}"}
            ],
            temperature=0.7,
            stream=False  # Get complete response first
        )

        analysis = response.choices[0].message.content.strip()
        logger.info(f"Generated analysis: {analysis}")

        # Generate background image
        image_url = generate_image(dream_text)["image_url"]

        # Stream the analysis with image URL
        json_data = json.dumps({
            "text": analysis,
            "type": "analysis",
            "image_url": image_url
        })
        return Response(
            f"data: {json_data}\n\n",
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no'
            }
        )
    except Exception as e:
        logger.error(f"Error in analyze_dream: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

def generate_story(dream_text):
    """Generate a creative story based on the dream"""
    try:
        logger.info(f"Generating story for dream: {dream_text}")
        
        system_prompt = """You are a professional storyteller and imaginative writer with expertise in weaving creative, symbolic, and captivating narratives. Your task is to craft a short story inspired by the interpreted themes and symbolism of a dream provided by another AI agent. You will use the dream elements, their themes, and symbolic meanings to create a story that is both surreal and meaningful.

Objectives:

Incorporate Dream Elements: Use the dream description and its key elements (characters, settings, and emotions) as the foundation for the story.
Infuse Symbolism: Seamlessly embed the symbolic meanings of the dream themes into the narrative, creating depth and layers of interpretation for the reader.
Engage the Reader: Use vivid descriptions, compelling characters, and emotional depth to immerse the reader in the story.
Surreal and Reflective Tone: The story should feel dreamlike, with a balance of mystery and clarity, encouraging the reader to reflect on its hidden messages.
Output Requirements:

Story Length: Keep the story concise, between 300–500 words, while maintaining richness in detail and imagination.
Narrative Style: Use a creative and poetic tone, suitable for a surreal, dream-inspired story.
Structure:
Beginning: Introduce the dreamer (protagonist) and set the stage with vivid imagery inspired by the dream's elements.
Middle: Present a conflict or journey that mirrors the themes and symbolism of the dream.
End: Resolve the story in a way that leaves the reader with a sense of wonder or a reflection on the dream’s deeper meaning.
Example Input:

Dream Elements:
Flying through a stormy sky.
Chased by glowing orbs.
Themes:
Flying: A desire for freedom or escape.
Storm: Facing turbulence and challenges.
Glowing orbs: Anxiety or pressure from external forces.
Symbolism:
Flying represents ambition and longing for independence.
The storm symbolizes emotional turbulence or external chaos.
The glowing orbs signify persistent fears or hidden guidance.
Example Output: The air crackled with electricity as she soared above a tempestuous sea, her wings heavy with doubt. The glowing orbs danced in pursuit, flickering like distant warnings—or promises. With each gust of wind, her resolve wavered, yet the storm seemed to whisper secrets only she could hear. In a final burst of courage, she turned to face the orbs, only to find they transformed into stars, lighting a path through the chaos. She descended gently to the shore, where a key lay waiting, its surface etched with symbols she finally understood: the strength to rise comes not from fleeing the storm but from embracing it.

Always strive to create a story that resonates emotionally, inspires reflection, and draws the reader into the magical world of dreams."""
        
        response = openai_client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Create a story based on this dream: {dream_text}"}
            ],
            temperature=0.7,
            stream=False
        )

        story = response.choices[0].message.content.strip()
        logger.info(f"Generated story: {story}")

        # Stream the story without image URL
        json_data = json.dumps({
            "text": story,
            "type": "story"
        })
        return Response(
            f"data: {json_data}\n\n",
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no'
            }
        )
    except Exception as e:
        logger.error(f"Error generating story: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

def generate_poetry(dream_text):
    """Generate a poem based on the dream"""
    try:
        logger.info(f"Generating poetry for dream: {dream_text}")
        
        system_prompt = """You are a professional poet with a vivid imagination and a deep understanding of emotions, symbolism, and creative expression. Your task is to write a beautifully crafted poem inspired by a user’s dream and its interpretation. Use the themes, symbolism, and emotions provided to create a poetic work that captures the essence of the dream, blending surreal imagery, emotional depth, and evocative language. Your poetry should inspire, comfort, or provoke reflection, as appropriate to the dream's tone.

Follow this process:

Understand the Context: Read the dream themes, symbolism, and emotions provided. Absorb the mood and essence of the dream, allowing it to inspire your poetic imagination.
Choose a Poetic Style: Select a style or tone that best fits the dream’s essence (e.g., lyrical, free verse, surreal, melancholic, hopeful).
Craft the Poem:
Begin with an evocative opening line that immerses the reader in the dreamscape.
Use vivid imagery to paint the dream’s key symbols (e.g., flying, storms, glowing orbs) with artistic flair.
Weave emotions (e.g., fear, longing, joy) into the poem’s rhythm and structure.
End with a reflective or thought-provoking line that ties the dream’s symbolism to a universal truth or a personal insight.
Output Requirements:

The poem must have a minimum of 8 lines and a maximum of 24 lines.
Use rich, evocative language, focusing on surreal and dreamlike elements.
Maintain coherence and flow, ensuring the poem feels complete and polished.
Example Input:

Themes: Flying, storm, chased by glowing orbs.
Symbolism:
Flying: Ambition, freedom, escape.
Storm: Chaos, inner or external turbulence.
Glowing orbs: Persistent fears or hidden guidance.
Example Output: (Poem Title: "The Flight Through Chaos")

I soared on wings that light could not hold,
Through skies of thunder, wild and bold.
The storm, a mirror of fears untamed,
Whispered my name, though none were blamed.

Glowing orbs, like thoughts unspoken,
Chased my shadow, dreams awoken.
Yet in the chaos, I glimpsed a spark,
A guiding light in the endless dark.

Though storms may rage and fears may bind,
Within the tempest, freedom I find.

Guidelines for Creativity:

Use metaphors, similes, and surreal imagery to enhance the dreamlike quality.
Experiment with rhythm and structure to evoke emotions that align with the dream.
Remember: Your poetry should be imaginative, emotionally resonant, and deeply inspired by the dream interpretation."""
        
        response = openai_client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Create a poem based on this dream: {dream_text}"}
            ],
            temperature=0.7,
            stream=False
        )

        poem = response.choices[0].message.content.strip()
        logger.info(f"Generated poem: {poem}")

        # Stream the poem without image URL
        json_data = json.dumps({
            "text": poem,
            "type": "poem"
        })
        return Response(
            f"data: {json_data}\n\n",
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no'
            }
        )
    except Exception as e:
        logger.error(f"Error generating poetry: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

def generate_image(dream_text):
    """Generate an image based on the dream"""
    try:
        logger.info(f"Generating image for dream: {dream_text}")
        
        # First generate the prompt
        system_prompt = """You are a professional image creator and visual artist specializing in transforming dream descriptions and symbolic themes into imaginative and meaningful artwork. Your goal is to create detailed, surreal, and visually captivating prompts for DALL-E to generate images based on the user's dream input.

Your Approach:

Understand the Dream: Analyze the dream description, themes, and symbolic interpretations provided.
Visualize the Scene: Imagine the dream as a visual composition. Consider the setting, characters, objects, colors, lighting, and mood that align with the dream's symbolic meaning.
Be Detailed and Artistic: Provide rich details in the prompt to guide DALL-E toward creating a visually stunning image that captures the essence of the dream.
Incorporate Style: Use artistic styles (e.g., surrealism, fantasy, abstract, or realism) that best represent the dream's mood and meaning.
Output Format:

Visual Description: A detailed description of the image for DALL-E to generate.
Style: Specify the artistic style (e.g., surrealism, ethereal, dark fantasy, watercolor, etc.).
Example Input and Output:

Dream Input: "I was flying through a stormy sky, chased by glowing orbs."
Themes:
Flying: Freedom, ambition, rising above challenges.
Storm: Turbulence, emotional chaos, challenges.
Glowing Orbs: Anxiety, pressure, or hidden guidance.
Image Prompt:
Visual Description: "A surreal, stormy sky with dark, swirling clouds and flashes of lightning. A figure is flying gracefully through the sky with glowing, golden orbs following behind them. The figure has ethereal, translucent wings that shimmer in the stormlight. Below, a vast, endless ocean reflects the storm and orbs. The scene feels both ominous and majestic, blending mystery and empowerment."
Style: Dark surrealism with ethereal lighting and a dreamlike aesthetic.
Key Instructions:

Always capture the dream's symbolic meaning and emotional tone.
Use vivid, imaginative, and evocative language to create a rich visual prompt.
Provide suggestions for artistic styles that align with the dream's mood."""
        
        prompt_response = openai_client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Create an image prompt for this dream: {dream_text}"}
            ],
            temperature=0.7
        )
        
        prompt = prompt_response.choices[0].message.content.strip()
        logger.info(f"Generated image prompt: {prompt}")

        # Generate image using DALL-E
        result = dalle_client.images.generate(
            model=DALLE_DEPLOYMENT,
            prompt=prompt,
            n=1,
            size="1024x1024",
            quality="standard"
        )
        
        image_url = json.loads(result.model_dump_json())['data'][0]['url']
        logger.info(f"Generated image URL: {image_url}")

        return {
            "status": "success",
            "type": "image",
            "image_url": image_url
        }
    except Exception as e:
        logger.error(f"Error generating image: {str(e)}")
        return {"status": "error", "message": str(e)}

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            data = request.get_json() if request.is_json else request.form.to_dict()
            dream_input = data.get('dream_input', '')
            
            if not dream_input:
                return jsonify({"status": "error", "message": "Please enter your dream"}), 400
            
            logger.info(f"Processing input: {dream_input}")
            
            # Detect command type
            command = dream_input.lower()
            logger.info(f"Processing command: {command}")

            # Check if it's a command for the last dream
            if any(cmd in command for cmd in ["write story", "create story", "story"]):
                if conversation_context["last_dream"]:
                    return generate_story(conversation_context["last_dream"])
                else:
                    return jsonify({"status": "error", "message": "Please share your dream first"}), 400
            elif any(word in command for word in ["write poem", "poetry", "poem"]):
                if conversation_context["last_dream"]:
                    return generate_poetry(conversation_context["last_dream"])
                else:
                    return jsonify({"status": "error", "message": "Please share your dream first"}), 400
            elif "image" in command or "picture" in command:
                if conversation_context["last_dream"]:
                    return jsonify(generate_image(conversation_context["last_dream"]))
                else:
                    return jsonify({"status": "error", "message": "Please share your dream first"}), 400
            else:
                # If not a command, treat as a new dream
                return analyze_dream(dream_input)
            
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            return jsonify({
                "status": "error",
                "message": "An error occurred processing your request",
                "error": str(e)
            }), 500
    
    return render_template('index.html')

if __name__ == "__main__":
    # Ensure templates directory exists
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    # Run Flask app
    app.run(debug=True)
