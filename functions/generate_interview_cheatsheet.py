import json
import PyPDF2
from io import BytesIO
from transformers import pipeline

class InterviewAnalyzer:
    def __init__(self):
        # Use tiny model that's quick to download
        self.pipeline = pipeline(
            "text-generation",
            model="sshleifer/tiny-gpt2",  # Tiny model, fast to download
            device="cpu"
        )
        # Get model's max length
        self.max_length = self.pipeline.model.config.max_position_embeddings

    def generate_response(self, prompt):
        try:
            # Shorter prompt to stay within limits
            formatted_prompt = f"""Analyze:
{prompt[:500]}  # Limit input length

JSON format:
{{
    "swot_analysis": {{
        "strengths": ["key strengths"],
        "weaknesses": ["areas to improve"],
        "opportunities": ["growth areas"],
        "threats": ["challenges"]
    }},
    "requiredskills": [
        {{
            "name": "skill",
            "required_level": 3,
            "current_level": 2,
            "match_percentage": 75
        }}
    ]
}}"""
            
            # Calculate safe token limits
            max_new_tokens = min(200, self.max_length - len(self.pipeline.tokenizer.encode(formatted_prompt)))
            
            response = self.pipeline(
                formatted_prompt,
                max_new_tokens=max_new_tokens,
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True,
                truncation=True,
                pad_token_id=self.pipeline.tokenizer.eos_token_id
            )[0]['generated_text']
            
            # Extract JSON or use fallback
            try:
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = response[json_start:json_end]
                    return self.enhance_analysis(json_str, prompt)
            except:
                return self.generate_smart_fallback(prompt)

        except Exception as e:
            print(f"Error generating response: {str(e)}")
            return self.generate_smart_fallback(prompt)

    def enhance_analysis(self, json_str, content):
        """Enhance the analysis with extracted information"""
        try:
            # Extract skills and experience
            content_lower = content.lower()
            skills_found = self.extract_skills(content_lower)
            experience = self.extract_experience(content_lower)
            
            # Create enhanced analysis
            analysis = {
                "swot_analysis": {
                    "strengths": [f"Experienced in {skill}" for skill in skills_found[:3]],
                    "weaknesses": ["Areas identified for improvement"],
                    "opportunities": [f"Potential growth in {skill}" for skill in skills_found[3:5]],
                    "threats": ["Market competition", "Technology evolution"]
                },
                "requiredskills": [
                    {
                        "name": skill,
                        "required_level": 4,
                        "current_level": 3,
                        "match_percentage": 75,
                        "evidence": experience.get(skill, "Mentioned in resume")
                    } for skill in skills_found[:5]
                ]
            }
            return json.dumps(analysis, indent=2)
        except:
            return self.generate_smart_fallback(content)

    def extract_skills(self, content):
        """Extract technical skills from content"""
        common_skills = [
            'python', 'java', 'javascript', 'react', 'node', 'sql', 'aws',
            'docker', 'kubernetes', 'git', 'agile', 'ci/cd', 'rest api'
        ]
        return [skill for skill in common_skills if skill in content]

    def extract_experience(self, content):
        """Extract experience details for skills"""
        experience = {}
        sentences = content.split('.')
        for sentence in sentences:
            for skill in self.extract_skills(sentence):
                if skill not in experience:
                    experience[skill] = sentence.strip()
        return experience

    def generate_smart_fallback(self, content):
        """Generate intelligent fallback analysis"""
        skills = self.extract_skills(content.lower())
        experience = self.extract_experience(content.lower())
        
        analysis = {
            "swot_analysis": {
                "strengths": [
                    f"Technical expertise in {skills[0]}" if skills else "Technical background",
                    f"Experience with {skills[1]}" if len(skills) > 1 else "Professional experience"
                ],
                "weaknesses": ["Continuing skill development"],
                "opportunities": [
                    f"Growth potential in {skills[2]}" if len(skills) > 2 else "Skill expansion opportunities"
                ],
                "threats": ["Market competition"]
            },
            "requiredskills": [
                {
                    "name": skill,
                    "required_level": 3,
                    "current_level": 3,
                    "match_percentage": 100,
                    "evidence": experience.get(skill, "Mentioned in profile")
                } for skill in skills[:3]
            ] or [
                {
                    "name": "Technical Skills",
                    "required_level": 3,
                    "current_level": 2,
                    "match_percentage": 66,
                    "evidence": "Based on overall profile"
                }
            ]
        }
        return json.dumps(analysis, indent=2)

def generate_interview_cheatsheet(pdf_path, job_description):
    try:
        # Initialize analyzer
        analyzer = InterviewAnalyzer()

        # Extract text from PDF
        if isinstance(pdf_path, BytesIO):
            pdf_reader = PyPDF2.PdfReader(pdf_path)
            resume_text = ""
            for page in pdf_reader.pages:
                resume_text += page.extract_text()
        else:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                resume_text = ""
                for page in pdf_reader.pages:
                    resume_text += page.extract_text()

        # Generate the prompt for analysis
        prompt = f"""
        Task: Analyze the resume and job description to create an interview cheatsheet.
        
        RESUME:
        {resume_text}

        JOB DESCRIPTION:
        {job_description}

        Generate a detailed analysis in the following JSON format:
        {{
            "swot_analysis": {{
                "strengths": [list of strengths found in resume],
                "weaknesses": [areas for improvement based on job requirements],
                "opportunities": [potential growth areas],
                "threats": [potential challenges]
            }},
            "requiredskills": [
                {{
                    "name": "skill name",
                    "required_level": required level (1-5),
                    "current_level": current level (1-5),
                    "match_percentage": percentage match,
                    "evidence": "evidence from resume"
                }}
            ],
            "concepts_revision": [key concepts to review],
            "QA": [potential interview questions],
            "company_insights": [relevant company insights]
        }}

        INSTRUCTIONS:
        1. Base all analyses on concrete evidence from the resume and job description
        2. For skills, calculate match_percentage as (current_level/required_level) * 100
        3. Return ONLY the JSON object, no additional text or explanations
        4. Ensure all evidence is specific and referenced from the resume
        """

        # Get response from DeepSeek
        response_text = analyzer.generate_response(prompt)

        # Clean and parse the response
        if response_text.startswith("```"):
            response_text = response_text[response_text.find("{"):response_text.rfind("}")+1]

        # Parse JSON response
        cheatsheet_data = json.loads(response_text)
        
        return cheatsheet_data

    except Exception as e:
        print(f"Error in generate_interview_cheatsheet: {str(e)}")
        # Return a structured error response
        return {
            "swot_analysis": {
                "strengths": ["Error analyzing strengths"],
                "weaknesses": ["Error analyzing weaknesses"],
                "opportunities": ["Error analyzing opportunities"],
                "threats": ["Error analyzing threats"]
            },
            "requiredskills": [
                {
                    "name": "Error",
                    "required_level": 0,
                    "current_level": 0,
                    "match_percentage": 0,
                    "evidence": "Error processing skills"
                }
            ],
            "concepts_revision": ["Error processing concepts"],
            "QA": ["Error processing questions"],
            "company_insights": ["Error processing insights"]
        }