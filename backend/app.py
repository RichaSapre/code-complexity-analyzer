from flask import Flask, request, jsonify, send_from_directory
import os
from flask_cors import CORS
import requests
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# --- Configuration ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# API Endpoints updated for latest 2026 availability
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"

@app.after_request
def after_request(response):
    """Enable CORS for cross-origin frontend requests if necessary."""
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    return response

@app.route('/')
def serve_frontend():
    """Serve the static frontend entry point."""
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))
    return send_from_directory(static_dir, 'index.html')

def clean_json_response(raw_text):
    """Robust helper to extract JSON from raw LLM responses that might contain markdown wrappers."""
    try:
        raw_text = raw_text.strip()
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].split("```")[0].strip()
        
        start_idx = raw_text.find('{')
        end_idx = raw_text.rfind('}')
        if start_idx != -1 and end_idx != -1:
            raw_text = raw_text[start_idx:end_idx+1]
            
        return json.loads(raw_text)
    except Exception as e:
        print(f"[ERROR] JSON Parse Failure. Raw input: {raw_text}")
        raise e

@app.route('/analyze', methods=['POST', 'OPTIONS'])
def analyze():
    """Main algorithmic analysis endpoint with dual-engine fallback."""
    if request.method == 'OPTIONS':
        return jsonify({"status": "preflight-ok"}), 200
    
    try:
        data = request.json
        code = data.get('code', '')
        
        print(f"\n[REQUEST] Received analysis request. Code length: {len(code)}")
        
        if not code:
            print("[WARN] Null input received")
            return jsonify({"error": "Null input: No code provided for analysis"}), 400

        prompt = f"""
        Analyze the following code for time and space complexity. 
        Return ONLY a valid JSON object with NO markdown, NO backticks, and NO extra text.
        
        The JSON structure MUST be:
        {{
          "time_complexity": "string",
          "space_complexity": "string",
          "bottleneck": "string",
          "explanation": "string",
          "optimized_code": "string",
          "optimization_explanation": "string"
        }}

        Code:
        {code}
        """

        # --- ATTEMPT 1: Google Gemini 2.0 Flash ---
        try:
            print("[SYSTEM] Attempting Gemini 2.0 Flash...")
            gemini_payload = {"contents": [{"parts": [{"text": prompt}]}]}
            response = requests.post(GEMINI_API_URL, json=gemini_payload, timeout=20)
            
            if response.status_code != 200:
                print(f"[SYSTEM] Gemini Engine failed (Status {response.status_code}): {response.text}")
                response.raise_for_status()
            
            json_resp = response.json()
            raw_text = json_resp['candidates'][0]['content']['parts'][0]['text']
            print("[SYSTEM] Gemini success. Parsing response...")
            analysis = clean_json_response(raw_text)
            return jsonify(analysis)

        except Exception as e:
            print(f"[SYSTEM] Primary engine failed: {str(e)}. Triggering Groq Llama-3.3 fallback...")
            
            # --- ATTEMPT 2: Groq Llama-3.3-70b (Fallback) ---
            try:
                groq_payload = {
                    "model": GROQ_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2
                }
                groq_headers = {
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                }
                
                print("[SYSTEM] Attempting Groq Llama-3.3...")
                response = requests.post(GROQ_API_URL, json=groq_payload, headers=groq_headers, timeout=25)
                if response.status_code != 200:
                    print(f"[SYSTEM] Groq status error {response.status_code}: {response.text}")
                    response.raise_for_status()
                
                json_resp = response.json()
                raw_text = json_resp['choices'][0]['message']['content']
                print("[SYSTEM] Groq success. Parsing response...")
                analysis = clean_json_response(raw_text)
                return jsonify(analysis)

            except Exception as groq_e:
                print(f"[FATAL] Fallback engine failed: {str(groq_e)}")
                return jsonify({
                    "error": "Optimization engine offline.",
                    "details": f"Gemini: {str(e)} | Groq: {str(groq_e)}",
                    "status": "OFFLINE"
                }), 500
    except Exception as global_e:
        print(f"[CRITICAL] Global server error: {str(global_e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": "Internal processor fault.",
            "details": str(global_e)
        }), 500

if __name__ == '__main__':
    # Default to port 5000 for local dev
    port = int(os.environ.get("PORT", 5000))
    print(f"Server starting on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False)

