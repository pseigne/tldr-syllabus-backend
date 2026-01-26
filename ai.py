import os
from openai import OpenAI
from pypdf import PdfReader

def chat(pdf_path="test3point5.pdf"):
    # Load API key from file if not in environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        try:
            with open("OPENAI_API_KEY.txt", "r") as f:
                api_key = f.read().strip()
        except FileNotFoundError:
            raise ValueError("OPENAI_API_KEY not found in environment or OPENAI_API_KEY.txt file")
    
    client = OpenAI(api_key=api_key)

    # Set the parameters 
    messages = [
        {"role": "system", "content": "You are a syllabus analyzer. Extract this information. course: coursename, professors: [[name:Name, email:Email, office:(Location of office. Would be like Van Vleck 102. None given if no location.), officeHours:(office hour times, none given if not found)]], TAs:[[Name:Name, Email:Email]], classTime: [[lecture:[time/day1, time/day2]], [lab/discussion/other (ifapplicable)]], gradeMakeup: [exam1:10%,homework:20%...], gradeCutoffs: [A:90-100,B:80-90...], importantDates:[Midterm:date,final:date,projectDue:date...(ALL DATES YOU SEE)], expectedWeeklySchedule: [mon:[homework (Due at 11:59),lecture (at 11 AM), etc.]]  Output JSON only"}
    ]

    print("Analyzing..............")


    messages.append({"role": "user", "content": parsePDF(pdf_path)})

    response = client.chat.completions.create(
        model="gpt-4o",
        response_format={ "type": "json_object" }, 
        messages=messages,
        temperature=0
)

    assistant_message = response.choices[0].message.content

    messages.append({"role": "assistant", "content": assistant_message})
    
    # Method for when not running on a server 
    
    # with open("output.json", "w") as file:
    #     file.write(assistant_message)
    
    return assistant_message


def parsePDF(pdf_path):
    reader = PdfReader(pdf_path)
    syllabus_text = ''
    
    for page in reader.pages:
        syllabus_text += page.extract_text(extraction_mode="layout")
    
    return syllabus_text



if __name__ == "__main__":
    chat()