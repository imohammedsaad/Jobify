schema = {
    "type": "object",
    "properties": {
        "company": {
            "type": "string",
            "description": "The company that the job description belongs to"
        },
        "role": {
            "type": "string",
            "description": "The role that the job description belongs to"
        },
        "swot_analysis": {
            "type": "object",
            "description": "A SWOT analysis of the candidate for this particular job role in terms of experience, skillsets, and culture match",
            "properties": {
                "strengths": {
                    "type": "array",
                    "description": "Key strengths of the candidate in this job interview",
                    "items": {"type": "string"}
                },
                "weaknesses": {
                    "type": "array",
                    "description": "Key weaknesses of the candidate in this job interview",
                    "items": {"type": "string"}
                },
                "opportunities": {
                    "type": "array",
                    "description": "Key opportunities that may come up for the candidate in this job role",
                    "items": {"type": "string"}
                },
                "threats": {
                    "type": "array",
                    "description": "Key threats that may come up for the candidate in this job role",
                    "items": {"type": "string"}
                }
            },
            "required": ["strengths", "weaknesses", "opportunities", "threats"]
        },
        "requiredskills": {
            "type": "array",
            "description": "A list of skills required for the role",
            "items": {
                "type": "object",
                "properties": {
                    "skill": {"type": "string"},
                    "candidate_skill": {
                        "type": "boolean",
                        "description": "Based on the resume, does the candidate have the skill or not?"
                    }
                },
                "required": ["skill", "candidate_skill"]
            }
        },
        "concepts_revision": {
            "type": "array",
            "description": "Topics that could be covered in the interview, based on the job description. Be exhaustive and cover all topics mentioned in the job description",
            "items": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string"},
                    "brief": {
                        "type": "string",
                        "description": "An introduction about what the topic is, why it's relevant to the role, and how the candidate can prepare for it"
                    },
                    "yt_search_query": {
                        "type": "string",
                        "description": "Youtube search query to get videos to learn about this topic"
                    },
                    "interview_questions": {
                        "type": "array",
                        "description": "Questions that can come up during the interview on this topic. Include at least 4.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "question": {
                                    "type": "string",
                                    "description": "A question on this topic relevant to the role"
                                },
                                "answer": {
                                    "type": "string",
                                    "description": "Answer for the question"
                                }
                            },
                            "required": ["question", "answer"]
                        }
                    }
                },
                "required": ["topic", "brief", "yt_search_query", "interview_questions"]
            }
        },
        "QA": {
            "type": "array",
            "description": "Questions that can come up during the interview based on the projects done and/or relevant to the job role. Include at least 10.",
            "items": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "A question deep-diving into project specifics"
                    },
                    "answer": {
                        "type": "string",
                        "description": "Suggested or example answer for the question"
                    }
                },
                "required": ["question", "answer"]
            }
        },
        "company_insights": {
            "type": "array",
            "description": "Insights about the company that might be useful during the interview, such as industry, business model, founding year, employee count, user base, annual revenue, headquarters, company values, and competitors. Add as much information about the company as possible. Be exhaustive.",
            "items": {
                "type": "object",
                "properties": {
                    "information_type": {
                        "type": "string",
                        "description": "The type of information, formatted neatly (e.g., 'Industry', 'Business Model')"
                    },
                    "info": {
                        "type": "string",
                        "description": "The information specific to the company. Make it concise (e.g., 'Technology', 'Subscription-based SaaS')."
                    }
                },
                "required": ["information_type", "info"]
            }
        }
    },
    "required": [
        "company",
        "role",
        "swot_analysis",
        "requiredskills",
        "concepts_revision",
        "QA",
        "company_insights"
    ]
}

response_format = {
    "name": "interview_cheatsheet",
    "description": "Generates a cheatsheet for a job role",
    "strict": True,
    "schema":schema
}

def format_response(text):
    """
    Format the raw response text into structured sections
    """
    sections = {
        'key_skills': [],
        'interview_questions': [],
        'technical_concepts': [],
        'achievements': [],
        'expertise_areas': [],
        'project_highlights': [],
        'swot_analysis': {
            'strengths': [],
            'weaknesses': [],
            'opportunities': [],
            'threats': []
        }
    }
    
    current_section = None
    current_swot = None
    
    # Split the text into lines and process each line
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check for section headers
        lower_line = line.lower()
        
        # SWOT Analysis section handling
        if 'swot analysis' in lower_line:
            current_section = 'swot_analysis'
            current_swot = None
            continue
        elif current_section == 'swot_analysis':
            if 'strengths' in lower_line:
                current_swot = 'strengths'
                continue
            elif 'weaknesses' in lower_line:
                current_swot = 'weaknesses'
                continue
            elif 'opportunities' in lower_line:
                current_swot = 'opportunities'
                continue
            elif 'threats' in lower_line:
                current_swot = 'threats'
                continue
            elif current_swot and line.startswith('-'):
                sections['swot_analysis'][current_swot].append(line[1:].strip())
                continue
        
        # Regular section handling
        if 'key skills' in lower_line:
            current_section = 'key_skills'
            continue
        elif 'interview questions' in lower_line:
            current_section = 'interview_questions'
            continue
        elif 'technical concepts' in lower_line:
            current_section = 'technical_concepts'
            continue
        elif 'achievements' in lower_line:
            current_section = 'achievements'
            continue
        elif 'areas of expertise' in lower_line:
            current_section = 'expertise_areas'
            continue
        elif 'project highlights' in lower_line:
            current_section = 'project_highlights'
            continue
            
        # Add content to current section
        if current_section and current_section != 'swot_analysis' and line.startswith('-'):
            sections[current_section].append(line[1:].strip())
    
    return sections