import os
import google.generativeai as genai
import json
from functions.pdf_to_text import extract_text_from_pdf
from functions.get_yt_videos import replace_youtube_videos_with_links

def generate_interview_cheatsheet(pdf_path, job_description):
    """
    Generate an interview cheatsheet from a PDF resume and job description
    """
    default_response = {
        "company": "Company",
        "role": "Position",
        "swot_analysis": {
            "strengths": ["Unable to analyze strengths"],
            "weaknesses": ["Unable to analyze weaknesses"],
            "opportunities": ["Unable to analyze opportunities"],
            "threats": ["Unable to analyze threats"]
        },
        "requiredskills": ["Unable to analyze required skills"],
        "concepts_revision": ["Unable to analyze concepts"],
        "QA": ["Unable to generate Q&A"],
        "company_insights": ["Unable to analyze company insights"]
    }
    
    try:
        # Configure Gemini API
        api_key = os.getenv("GEMINI_API_KEY")
        print(f"API Key present: {bool(api_key)}")
        genai.configure(api_key=api_key)
        
        # Extract text from PDF
        print("Extracting text from PDF...")
        resume_text = extract_text_from_pdf(pdf_path)
        
        if not resume_text:
            raise ValueError("Failed to extract text from PDF")
        
        prompt = f"""
        Analyze this resume and job description to create a detailed interview preparation guide.
        
        RESUME:
        {resume_text}

        JOB DESCRIPTION:
        {job_description}

        Provide a direct JSON response with this exact structure (fill in with actual content):
        {{
            "company": "Actual Company Name",
            "role": "Actual Job Title",
            "swot_analysis": {{
                "strengths": ["Specific strength 1", "Specific strength 2"],
                "weaknesses": ["Specific weakness 1", "Specific weakness 2"],
                "opportunities": ["Specific opportunity 1", "Specific opportunity 2"],
                "threats": ["Specific threat 1", "Specific threat 2"]
            }},
            "requiredskills": ["Required skill 1", "Required skill 2"],
            "concepts_revision": ["Technical concept 1", "Technical concept 2"],
            "QA": ["Q: Likely interview question 1\\nA: Suggested answer 1", "Q: Question 2\\nA: Answer 2"],
            "company_insights": ["Company insight 1", "Company insight 2"]
        }}

        IMPORTANT: 
        1. Return ONLY the JSON object
        2. No markdown, no explanations, no additional text
        3. Ensure all fields are present and filled with relevant content
        4. Make all analysis specific to the provided resume and job description
        """
        
        print("Sending request to Gemini...")
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=8192,
                top_p=0.8,
                top_k=40
            )
        )
        
        # Clean and parse response
        cheatsheet_text = response.text.strip()
        if cheatsheet_text.startswith("```"):
            start = cheatsheet_text.find("\n") + 1
            end = cheatsheet_text.rfind("```")
            cheatsheet_text = cheatsheet_text[start:end].strip()
        
        try:
            formatted_response = json.loads(cheatsheet_text)
            
            # Validate all required fields are present
            required_fields = ["company", "role", "swot_analysis", "requiredskills", 
                             "concepts_revision", "QA", "company_insights"]
            
            if all(field in formatted_response for field in required_fields):
                if all(field in formatted_response["swot_analysis"] 
                      for field in ["strengths", "weaknesses", "opportunities", "threats"]):
                    return formatted_response
            
            print("Missing required fields in response")
            return default_response
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {str(e)}")
            print(f"Raw response: {cheatsheet_text}")
            return default_response
            
    except Exception as e:
        print(f"Error generating cheatsheet: {str(e)}")
        return default_response