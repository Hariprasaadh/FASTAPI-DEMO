from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_community.document_loaders import WebBaseLoader
import PyPDF2 as pdf
import os
import io
import uvicorn

app = FastAPI(
    title="Smart ATS Resume Analyzer API",
    description="API for analyzing resumes against job descriptions",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Load environment variables
load_dotenv()

GROQ_API_KEY1 = os.getenv("GROQ_API_KEY1")
if not GROQ_API_KEY1:
    raise ValueError("GROQ_API_KEY1 environment variable is not set")

GROQ_API_KEY2 = os.getenv("GROQ_API_KEY2")
if not GROQ_API_KEY2:
    raise ValueError("GROQ_API_KEY2 environment variable is not set")

GROQ_API_KEY3 = os.getenv("GROQ_API_KEY3")
if not GROQ_API_KEY3:
    raise ValueError("GROQ_API_KEY3 environment variable is not set")


def get_response(resume_content, job_content):
    """Generate ATS analysis response from resume and job content"""
    llm = ChatGroq(
        model_name="llama-3.3-70b-versatile",
        temperature=0.5,
        groq_api_key=GROQ_API_KEY1
    )
    prompt_extract = PromptTemplate.from_template(
        """
        ###Role Definition:
            Act as a highly skilled ATS (Application Tracking System) professional with expertise in evaluating resumes 
            across various tech fields, including software engineering, data science, data analysis, big data engineering, web development, and app development. 
            Compare resumes against job descriptions, ensuring high precision and actionable insights.

        ###Task Objective:
            Your task is to provide a comprehensive evaluation of a resume based on the job content, 
            web-scraped from the provided job link. The aim is to assist candidates in optimizing their resumes for a 
            competitive job market by identifying gaps and offering targeted improvement suggestions.    

        ###Response Format (Use HTML with CSS styling):
            <div style='text-align: center; padding: 20px;'>
                <h1 style='font-size: 48px; color: white; margin-bottom: 10px;'>Match Percentage: [Insert calculated percentage]%</h1>
            </div>

            <div style='background-image: linear-gradient(to top, #1e3c72 0%, #1e3c72 1%, #2a5298 100%); padding: 20px; margin: 10px 0; border-radius: 10px;'>
                <h2 style='color: white; border-bottom: 2px solid #0066cc;'>Reasons for Match Percentage</h2>
                - Strengths:
                [List specific strengths]
                - Gaps:
                [List gaps in responsibilities/skills]
                - Alignment:
                [Explain alignment with requirements]
                - Missing Elements:
                [Highlight important missing keywords]
            </div>

            <div style='background-image: linear-gradient(to top, #1e3c72 0%, #1e3c72 1%, #2a5298 100%); padding: 20px; margin: 10px 0; border-radius: 10px;'>
                <h2 style='color: white; border-bottom: 2px solid #0066cc;'>Missing Keywords</h2>
                [Detailed list of missing/weak keywords]
            </div>

            <div style='background-image: linear-gradient(to top, #1e3c72 0%, #1e3c72 1%, #2a5298 100%); padding: 20px; margin: 10px 0; border-radius: 10px;'>
                <h2 style='color: white; border-bottom: 2px solid #0066cc;'>Improvement Suggestions</h2>
                [Five actionable tips for improvement]

                <h3 style='margin-top: 15px;'>Recommended Certifications:</h3>
                [Coursera and Udemy certification recommendations with links]
            </div>

        Resume Content: {resume_content}
        Content scraped from Job Application Link: {job_content}
        """
    )
    chain = prompt_extract | llm
    res = chain.invoke(input={'resume_content': resume_content, 'job_content': job_content})
    return res.content


def extract_text(file_content):
    """Extract text from PDF content"""
    try:
        pdf_file = io.BytesIO(file_content)
        reader = pdf.PdfReader(pdf_file)
        pages = len(reader.pages)
        text = ""
        for page_num in range(pages):
            page = reader.pages[page_num]
            text += str(page.extract_text())
        return text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting text from PDF: {str(e)}")


def scrape_website(job_link):
    """Scrape job details from the provided URL"""
    if not job_link:
        raise HTTPException(status_code=400, detail="Please provide a valid job link")

    llm_scrape = ChatGroq(
        model_name="llama-3.3-70b-versatile",
        temperature=0.5,
        groq_api_key=GROQ_API_KEY2
    )

    try:
        loader = WebBaseLoader(job_link)
        page_data = loader.load().pop().page_content

        prompt_job_content = PromptTemplate.from_template(
            """
               ### SCRAPED TEXT FROM WEBSITE:
               {page_data}
               ### INSTRUCTION:
               Extract the following from the scraped text:
               - Company Details (e.g., Name)
               - Job Title and Role
               - Job Description
               - Skills and Competencies
               - Qualifications and Experience
               and any other important data
            """
        )

        chain_extract = prompt_job_content | llm_scrape
        res = chain_extract.invoke(input={'page_data': page_data})
        return res.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error scraping job content: {str(e)}")


def generate_mail(resume_content, job_content):
    """Generate a job application email based on resume and job content"""
    if not resume_content or not job_content:
        raise HTTPException(status_code=400, detail="Resume or job content is missing")

    llm_mail = ChatGroq(
        model_name="llama-3.3-70b-versatile",
        temperature=0.5,
        groq_api_key=GROQ_API_KEY3
    )

    prompt_mail = PromptTemplate.from_template(
        """
            ### JOB CONTENT:
            {job_content}

            ### USER RESUME:
            {resume_content}

            ### INSTRUCTION:
            Create a personalized job application email using the above details. 
            Include:
            1. A formal greeting
            2. A brief introduction about the candidate
            3. Explanation of why the user is interested in the job
            4. Value proposition and how the user's skills align with the job
            5. Call to action (interview invitation)
            6. Polite closing with contact details

            Ensure the email maintains a professional and concise tone.
        """
    )

    mail_extract = prompt_mail | llm_mail
    final_mail = mail_extract.invoke(input={'job_content': job_content, 'resume_content': resume_content})
    return final_mail.content


# Pydantic models for request/response validation
class AnalysisRequest(BaseModel):
    job_link: str


class MailRequest(BaseModel):
    resume_content: str
    job_content: str


class AnalysisResponse(BaseModel):
    html_content: str
    email_content: str


@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint that returns basic API information"""
    return """
    <html>
        <head>
            <title>Smart ATS Resume Analyzer API</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    line-height: 1.6;
                }
                h1 {
                    color: #2a5298;
                }
                .endpoint {
                    background: #f5f5f5;
                    padding: 15px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                }
                code {
                    background: #e0e0e0;
                    padding: 2px 5px;
                    border-radius: 3px;
                }
            </style>
        </head>
        <body>
            <h1>Smart ATS Resume Analyzer API</h1>
            <p>This API provides resume analysis against job descriptions.</p>

            <div class="endpoint">
                <h2>POST /analyze</h2>
                <p>Upload a resume PDF and provide a job link to get analysis.</p>
            </div>

            <div class="endpoint">
                <h2>POST /generate-email</h2>
                <p>Generate a job application email based on resume and job content.</p>
            </div>

            <p>Check <code>/docs</code> for detailed API documentation.</p>
        </body>
    </html>
    """


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_resume(
        resume: UploadFile = File(...),
        job_link: str = Form(...)
):
    """
    Analyze a resume against a job description

    - **resume**: PDF file containing the resume
    - **job_link**: URL of the job posting

    Returns HTML content with analysis and a generated application email
    """
    if resume.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    file_content = await resume.read()
    resume_content = extract_text(file_content)
    job_content = scrape_website(job_link)

    html_response = get_response(resume_content, job_content)
    email_content = generate_mail(resume_content, job_content)

    return AnalysisResponse(
        html_content=html_response,
        email_content=email_content
    )


@app.post("/generate-email")
async def create_email(request: MailRequest):
    """
    Generate a job application email

    - **resume_content**: Text content of the resume
    - **job_content**: Text content of the job description

    Returns a generated job application email
    """
    email = generate_mail(request.resume_content, request.job_content)
    return {"email": email}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}


if __name__ == "__main__":
    # Change this line for Render compatibility
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)