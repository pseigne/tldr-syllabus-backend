import os
from openai import OpenAI
# from pypdf import PdfReader
from pydantic import BaseModel, Field
from typing import List, Optional
import pymupdf4llm


class GradeItem(BaseModel):
    assignment_type: str = Field(description="e.g. 'Homework' or 'Midterm'")
    percentage: str = Field(description="e.g. '20%' or '200 points'")

class GradeCutoff(BaseModel):
    grade: str = Field(description="e.g. 'A', 'A-'")
    cutoff: str = Field(description="e.g. '>= 93%'")

class ImportantDate(BaseModel):
    event: str = Field(description="e.g. 'Midterm Exam'")
    date: str = Field(description="e.g. 'Oct 14th'")


class Staff(BaseModel):
    name: str
    email: Optional[str] = None
    office: Optional[str] = None
    officeHours: Optional[str] = None
    
class ClassSession(BaseModel):
    type: str = Field(description="e.g., Lecture, Lab, Discussion")
    times: List[str] = Field(description="e.g., ['Mon 10:00-11:00', 'Wed 10:00-11:00']")
    
class WeeklySchedule(BaseModel):
    mon: List[str] = []
    tue: List[str] = []
    wed: List[str] = []
    thu: List[str] = []
    fri: List[str] = []
    
class SyllabusData(BaseModel):
    course: str
    professors: List[Staff]
    TAs: List[Staff]
    classTime: List[ClassSession]
    gradeMakeup: List[GradeItem]
    gradeCutoffs: List[GradeCutoff]
    importantDates: List[ImportantDate]
    
    expectedWeeklySchedule: WeeklySchedule
    


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


def parsePDF2():
    with open("pdfToMarkdown.md", "w") as file:
        md_text = pymupdf4llm.to_markdown('test.pdf')
        file.write(md_text)


if __name__ == "__main__":
    # Tester for output 
    with open("output.json", "w") as file:
        file.write(chat('test3point5.pdf'))