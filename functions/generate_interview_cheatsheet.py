import os
import google.generativeai as genai
import json
from functions.pdf_to_text import extract_text_from_pdf
from functions.get_yt_videos import replace_youtube_videos_with_links

def generate_interview_cheatsheet(pdf_path, job_description):
    """
    Generate an interview cheatsheet from a PDF resume and job description
    """
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

        # First, get SWOT analysis separately for better reliability
        swot_prompt = f"""
        Perform a detailed SWOT analysis based on the resume and job description.
        Focus on specific, actionable insights.

        RESUME:
        {resume_text}

        JOB DESCRIPTION:
        {job_description}

        Analyze and provide a JSON response with this structure:
        {{
            "swot_analysis": {{
                "strengths": [
                    {{
                        "strength": "Specific strength point",
                        "evidence": "Evidence from resume",
                        "relevance": "How this strength matches job requirements"
                    }}
                ],
                "weaknesses": [
                    {{
                        "weakness": "Specific gap or area for improvement",
                        "impact": "How this might affect job performance",
                        "mitigation": "How to address or explain this in interview"
                    }}
                ],
                "opportunities": [
                    {{
                        "opportunity": "Specific growth or learning opportunity",
                        "benefit": "How this benefits both candidate and company",
                        "action_plan": "How to leverage this opportunity"
                    }}
                ],
                "threats": [
                    {{
                        "threat": "Specific challenge or risk",
                        "potential_impact": "How this could affect success in role",
                        "mitigation_strategy": "How to address this threat"
                    }}
                ]
            }}
        }}

        IMPORTANT:
        1. Be specific and detailed
        2. Base analysis on actual resume content and job requirements
        3. Provide actionable insights
        4. Include at least 3 points for each category
        5. Focus on technical and professional aspects
        """

        print("Generating SWOT analysis...")
        model = genai.GenerativeModel('gemini-pro')
        swot_response = model.generate_content(
            swot_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,
                max_output_tokens=8192,
                top_p=0.8,
                top_k=40
            )
        )

        swot_text = swot_response.text.strip()
        if swot_text.startswith("```"):
            start = swot_text.find("\n") + 1
            end = swot_text.rfind("```")
            swot_text = swot_text[start:end].strip()

        try:
            swot_data = json.loads(swot_text)
            if not validate_swot_analysis(swot_data.get("swot_analysis", {})):
                raise ValueError("Invalid SWOT analysis structure")
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error parsing SWOT analysis: {str(e)}")
            swot_data = generate_fallback_swot(resume_text, job_description)

        # Now proceed with the main analysis
        prompt = f"""
        Analyze this resume and job description to create a detailed interview preparation guide.
        
        RESUME:
        {resume_text}

        JOB DESCRIPTION:
        {job_description}

        Provide a direct JSON response with this exact structure. Analyze deeply and provide specific, detailed content:
        {{
            "company": "Extract the actual company name from the job description",
            "role": "Extract the actual job title from the job description",
            "requiredskills": [
                {{
                    "name": "Extract each required skill from job description",
                    "importance": "Rate importance 1-5 based on frequency and emphasis in job description",
                    "context": "Provide specific context of how this skill is used in the role"
                }}
            ],
            "concepts_revision": [
                {{
                    "concept": "Technical concept from job description",
                    "importance": "High/Medium/Low based on role requirements",
                    "details": "Specific details about what to review"
                }}
            ],
            "QA": [
                {{
                    "question": "Generate specific technical or behavioral question based on job requirements",
                    "answer": "Provide detailed answer incorporating resume experience",
                    "type": "Technical/Behavioral/Company-specific",
                    "importance": "High/Medium/Low"
                }}
            ],
            "company_insights": [
                {{
                    "category": "Business Model/Culture/Technology/Market Position",
                    "insight": "Specific insight about the company from job description or public information",
                    "relevance": "How this insight is relevant to the interview"
                }}
            ]
        }}
        """
        
        print("Generating main analysis...")
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
            required_fields = ["company", "role", "requiredskills", 
                             "concepts_revision", "QA", "company_insights"]
            
            if all(field in formatted_response for field in required_fields):
                # Process and structure the skills data
                skills_data = process_skills(resume_text, job_description, formatted_response["requiredskills"])
                
                # Structure the complete response
                cheatsheet_data = {
                    "company": formatted_response["company"],
                    "role": formatted_response["role"],
                    "swot_analysis": swot_data["swot_analysis"],
                    "requiredskills": skills_data,
                    "concepts_revision": formatted_response["concepts_revision"],
                    "QA": formatted_response["QA"],
                    "company_insights": formatted_response["company_insights"]
                }
                return cheatsheet_data
            
            print("Missing required fields in response")
            return generate_fallback_response(resume_text, job_description, swot_data["swot_analysis"])
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {str(e)}")
            print(f"Raw response: {cheatsheet_text}")
            return generate_fallback_response(resume_text, job_description, swot_data["swot_analysis"])
            
    except Exception as e:
        print(f"Error generating cheatsheet: {str(e)}")
        return generate_fallback_response(resume_text, job_description)

def validate_swot_analysis(swot_data):
    """
    Validate the SWOT analysis data structure and content
    """
    required_categories = ["strengths", "weaknesses", "opportunities", "threats"]
    
    # Check if all categories exist
    if not all(category in swot_data for category in required_categories):
        return False
    
    # Check if each category has at least one item
    for category in required_categories:
        if not isinstance(swot_data[category], list) or len(swot_data[category]) == 0:
            return False
    
    return True

def generate_fallback_swot(resume_text, job_description):
    """
    Generate a basic SWOT analysis when the main analysis fails
    """
    try:
        model = genai.GenerativeModel('gemini-pro')
        fallback_prompt = f"""
        Create a simple SWOT analysis based on the resume and job description.
        Focus on the most important points only.

        RESUME:
        {resume_text}

        JOB DESCRIPTION:
        {job_description}

        Return a JSON object with arrays of strings for strengths, weaknesses, opportunities, and threats.
        Keep it simple but specific to the actual resume and job.
        """

        response = model.generate_content(
            fallback_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,
                max_output_tokens=2048
            )
        )

        fallback_text = response.text.strip()
        if fallback_text.startswith("```"):
            start = fallback_text.find("\n") + 1
            end = fallback_text.rfind("```")
            fallback_text = fallback_text[start:end].strip()

        fallback_data = json.loads(fallback_text)
        return {"swot_analysis": fallback_data}

    except Exception as e:
        print(f"Error generating fallback SWOT: {str(e)}")
        return {
            "swot_analysis": {
                "strengths": ["Technical skills from resume", "Relevant experience", "Educational background"],
                "weaknesses": ["Areas for skill development", "Experience gaps", "Areas to improve"],
                "opportunities": ["Growth potential in role", "Learning opportunities", "Career development"],
                "threats": ["Market competition", "Technical challenges", "Industry changes"]
            }
        }

def generate_fallback_response(resume_text, job_description, swot_analysis=None):
    """
    Generate a basic response when the main analysis fails
    """
    if swot_analysis is None:
        swot_analysis = generate_fallback_swot(resume_text, job_description)["swot_analysis"]

    return {
        "company": extract_company_name(job_description),
        "role": extract_role(job_description),
        "swot_analysis": swot_analysis,
        "requiredskills": extract_basic_skills(job_description),
        "concepts_revision": ["Key technical concepts from job description"],
        "QA": ["Basic interview questions based on role"],
        "company_insights": ["Company information from job description"]
    }

def extract_company_name(job_description):
    """Extract company name from job description using basic text analysis"""
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(
            f"Extract only the company name from this job description: {job_description}",
            generation_config=genai.types.GenerationConfig(temperature=0.1)
        )
        return response.text.strip()
    except:
        return "Company"

def extract_role(job_description):
    """Extract role from job description using basic text analysis"""
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(
            f"Extract only the job title/role from this job description: {job_description}",
            generation_config=genai.types.GenerationConfig(temperature=0.1)
        )
        return response.text.strip()
    except:
        return "Position"

def extract_basic_skills(job_description):
    """Extract basic required skills from job description"""
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(
            """
            List exactly 5 key required skills from this job description.
            Return ONLY the skill names, one per line, nothing else.
            
            JOB DESCRIPTION:
            """ + job_description,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,
                max_output_tokens=1024,
                top_p=0.1,
                top_k=1
            )
        )
        
        # Get the text content from the response
        skills_text = response.text.strip()
        
        # Clean up the response if it contains markdown code blocks
        if skills_text.startswith("```"):
            start = skills_text.find("\n") + 1
            end = skills_text.rfind("```")
            skills_text = skills_text[start:end].strip()
        
        # Split into lines and clean each skill
        skills = [line.strip() for line in skills_text.split("\n") if line.strip()]
        
        # Take only the first 5 skills
        skills = skills[:5]
        
        # Format each skill with default levels
        return [
            {
                "name": skill,
                "required_level": 3,
                "current_level": 0,
                "match_percentage": 0
            } 
            for skill in skills
        ] if skills else [
            {
                "name": "Required technical skill",
                "required_level": 3,
                "current_level": 0,
                "match_percentage": 0
            }
        ]
    except Exception as e:
        print(f"Error extracting skills: {str(e)}")
        return [
            {
                "name": "Required technical skill",
                "required_level": 3,
                "current_level": 0,
                "match_percentage": 0
            }
        ]

def calculate_skill_match(required_level, current_level):
    max_level = max(required_level, current_level)
    match_percentage = (current_level / required_level) * 100 if required_level > 0 else 100
    return min(round(match_percentage), 100)

def process_skills(resume_text, job_description, required_skills):
    """
    Analyze the resume text against required skills to determine skill levels and matches
    """
    try:
        # Configure Gemini API
        model = genai.GenerativeModel('gemini-pro')
        
        skills_prompt = f"""
        Analyze the resume and job description to rate the candidate's current level in each required skill.
        
        RESUME:
        {resume_text}

        JOB DESCRIPTION:
        {job_description}

        REQUIRED SKILLS:
        {json.dumps(required_skills, indent=2)}

        For each skill, provide a JSON object with:
        1. name: The skill name
        2. required_level: Required proficiency level (1-5) based on job description
        3. current_level: Current proficiency level (1-5) based on resume
        4. match_percentage: Calculated match percentage
        5. evidence: Specific evidence from resume supporting the rating

        Return only a JSON array of skill objects.
        """

        response = model.generate_content(
            skills_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,
                max_output_tokens=8192,
                top_p=0.8,
                top_k=40
            )
        )

        skills_text = response.text.strip()
        if skills_text.startswith("```"):
            start = skills_text.find("\n") + 1
            end = skills_text.rfind("```")
            skills_text = skills_text[start:end].strip()

        skills_data = json.loads(skills_text)
        return skills_data

    except Exception as e:
        print(f"Error processing skills: {str(e)}")
        return []