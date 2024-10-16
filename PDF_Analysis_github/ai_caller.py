import os
import vertexai
from vertexai.preview.generative_models import GenerativeModel

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "key.json"

PROJECT_ID = "winter-cogency-436501-g9"
REGION = "us-central1"

vertexai.init(project=PROJECT_ID, location=REGION)

def call_ai_model(content, question):
    generative_model = GenerativeModel("gemini-1.5-flash")
    
    prompt = f"""Based on the following content, answer this question: {question}

When providing your answer, please reference the source of information using the MLX## format found at the beginning of each section of the content.

Content:
{content}"""

    contents = [
        {
            "role": "user",
            "parts": [{"text": prompt}]
        }
    ]
    
    generation_config = {
        "temperature": 0.7,
        "max_output_tokens": 1500,
        "top_p": 0.95,
        "top_k": 40
    }
    
    response = generative_model.generate_content(
        contents=contents,
        generation_config=generation_config
    )
    
    return response.text.strip()