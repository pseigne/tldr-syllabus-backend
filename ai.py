import os
from openai import OpenAI
# from pypdf import PdfReader
from pydantic import BaseModel, Field
from typing import List, Optional
import pymupdf4llm



class GradeItem(BaseModel):
    assignment_category: str = Field(description="e.g., 'Homework', 'Midterm', 'Final Project'")
    count: int = Field(description="The number of assignments in this category. e.g., 5 for '5 Homeworks'. Default to 1 if it's a single exam.")
    weight_percentage: Optional[float] = Field(None, description="The percentage weight of this category towards the final grade, e.g., 20.0. Leave null if the class strictly uses a point system.")
    total_points: Optional[float] = Field(None, description="The total points this category is worth, if the class uses a point system. Leave null if it uses weights.")
    drop_lowest: int = Field(0, description="The number of lowest scores dropped in this category. Default is 0.")

class GradeBoundary(BaseModel):
    letter_grade: str = Field(description="The exact letter grade, e.g., 'A', 'AB', 'B', 'BC', 'C', 'D', 'F'")
    min_percent: float = Field(description="The minimum percentage required for this grade, e.g., 93.0")
    max_percent: float = Field(description="The maximum percentage for this grade. For an A, this is usually 100.0")

class ImportantDate(BaseModel):
    event: str = Field(description="e.g., 'Midterm Exam', 'Project 1 Due'")
    # Force the LLM to format the date so JavaScript's new Date() can read it instantly
    date_iso: str = Field(description="The date formatted as YYYY-MM-DD. Infer the year based on the syllabus context.")
    is_deadline: bool = Field(description="True if this is a hard deadline, exam, or deliverable")


class Staff(BaseModel):
    name: str
    role: str = Field(description="The role of the staff member, e.g., 'Professor', 'Lecturer', 'TA', 'Peer Mentor', etc.")
    email: Optional[str] = None
    phone: Optional[str] = Field(None, description="Office phone number if provided")
    office: Optional[str] = None
    officeHours: Optional[str] = Field(None, description="e.g., 'Tue/Thu 2:00PM-3:00PM'")

class ClassSession(BaseModel):
    type: str = Field(description="e.g., 'Lecture', 'Lab', 'Discussion'")
    day_of_week: str = Field(description="e.g., 'Monday', 'Tuesday'")
    # Standardize the time so your frontend doesn't have to guess AM/PM
    start_time_24h: str = Field(description="Start time in 24-hour HH:MM format, e.g., '14:30'")
    end_time_24h: str = Field(description="End time in 24-hour HH:MM format, e.g., '15:45'")

class Topic(BaseModel):
    week_or_date: str = Field(description="e.g., 'Week 1', 'Sept 4', or 'Module 1'")
    topic_name: str
    readings_or_tasks: Optional[str] = Field(None, description="Assigned readings, chapters, or tasks for this specific topic")

class Policy(BaseModel):
    policy_name: str = Field(description="e.g., 'Academic Integrity', 'Late Work', 'Accommodations'")
    summary: str = Field(description="A brief 1-2 sentence summary of the policy rules")

class Resource(BaseModel):
    name: str = Field(description="e.g., 'Piazza', 'Canvas', 'Textbook'")
    link_or_details: Optional[str] = Field(None, description="URL, ISBN, or location if available")


# --- MAIN SYLLABUS MODEL ---

class SyllabusData(BaseModel):
    course_code: str = Field(description="e.g., 'COMP SCI 571' or 'ECON 400'")
    course_title: Optional[str] = Field(None, description="e.g., 'Building User Interfaces'")
    credits: Optional[str] = Field(None, description="e.g., '3 credits' or '4'")
    course_description: Optional[str] = Field(None, description="Official catalog description found in the syllabus")
    course_summary: Optional[str] = Field(None, description="Summarize the offical description found in the syllabus to easily refrencable bullets")
    learning_outcomes: Optional[str] = Field(None, description="If there are course learning outcomes specified then add them in as a bulleted list. Summarize them as well")
    what_you_will_learn: Optional[str] = Field(None, description="Parsing the syllabus, create a list of what the student will be expected to learn throughout the semester")

    # Grouping all staff makes frontend rendering easier (you can filter by role later)
    staff: List[Staff] = Field(description="All professors, TAs, and instructional staff")
    class_sessions: List[ClassSession]

    grade_makeup: List[GradeItem]
    grade_cutoffs: List[GradeBoundary]
    
    important_dates: List[ImportantDate]
    schedule_of_topics: List[Topic]
    
    policies: List[Policy] = Field(description="Important course policies like academic integrity, AI usage, or late work")
    resources: List[Resource] = Field(description="Textbooks, software, or platforms used in the course")
    
    expected_hours_per_week: Optional[str] = Field(None, description="Expected time commitment outside of class, often mandated to be in the syllabus")
    additional_notes: Optional[str] = Field(None, description="Any other crucial information that doesn't fit elsewhere")
    


def chat(pdf_path="test.pdf"):
    # Load API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        try:
            with open("OPENAI_API_KEY.txt", "r") as f:
                api_key = f.read().strip()
        except FileNotFoundError:
            raise ValueError("OPENAI_API_KEY not found.")
    
    client = OpenAI(api_key=api_key)

    print("Converting PDF to Markdown...")
    md_text = pymupdf4llm.to_markdown(pdf_path)

    print("Analyzing Syllabus...")

    # We use client.beta.chat.completions.parse to enforce the Pydantic schema
    completion = client.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06", # Use the latest model for best structure adherence
        messages=[
            {"role": "system", "content": "You are a a professional syllabus analyzer that provides structured data from course syllabi. Extract the data exactly into the requested JSON format. If a field is missing, use null or an empty list."},
            {"role": "user", "content": f"Here is the syllabus content:\n\n{md_text}"},
        ],
        # Specify the response format 
        response_format=SyllabusData, 
    )

    # The result is already a python object validated against your class
    structured_data = completion.choices[0].message.parsed
    
    # Convert back to JSON string for your frontend
    return structured_data.model_dump_json()


# tester
def parsePDF2():
    with open("pdfToMarkdown.md", "w") as file:
        md_text = pymupdf4llm.to_markdown('test.pdf')
        file.write(md_text)


if __name__ == "__main__":
    # Tester for output 
    with open("output.json", "w") as file:
        file.write(chat('test3point5.pdf'))