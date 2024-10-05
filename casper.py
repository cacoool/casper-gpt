import csv
import anthropic
import os
from dotenv import load_dotenv
from tqdm import tqdm
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.pdfbase.pdfmetrics import registerFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm


def create_pdf(scenarios, filename):
    doc = SimpleDocTemplate(filename, pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=18)
    Story = []
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))
    styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER))

    for i, scenario in tqdm(enumerate(scenarios, 1), total=len(scenarios)):
        Story.append(Paragraph(f"Scenario {i}", styles['Heading1']))
        Story.append(Spacer(1, 12))

        Story.append(Paragraph(scenario['Scenario'], styles['Heading1']))
        Story.append(Spacer(1, 6))

        for j in range(1, 4):
            question = scenario[f'Question {j}']
            if question:
                answer = generate_answer(scenario['Scenario'], question)
                # Add question
                Story.append(Paragraph(f"Question {j}: {question}", styles['Heading2']))
                Story.append(Spacer(1, 6))

                # Add answer
                Story.append(Paragraph(answer, styles['Justify']))
                Story.append(Spacer(1, 12))

        Story.append(Spacer(1, 12))
        Story.append(PageBreak())

    doc.build(Story, onFirstPage=add_page_number, onLaterPages=add_page_number)


def add_page_number(canvas, doc):
    page_num = canvas.getPageNumber()
    text = f"Page {page_num}"
    canvas.drawRightString(200 * mm, 20 * mm, text)

# Load environment variables
load_dotenv()

# Initialize the Anthropic client
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def read_csv(file_path):
    scenarios = []
    with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            scenarios.append(row)
    return scenarios

def generate_answer(scenario, question):
    prompt = f"""
        You are taking the Casper test (open-response situational judgment test) for medical school, which assesses personal and professional characteristics. Your goal is to provide the best possible answer to score highly. 
    
        Scenario: {scenario}
        
        Question: {question}
        
        Please provide a thoughtful, ethical, and empathetic response that demonstrates strong interpersonal skills, professionalism, and sound judgment. It is super important your answer is well-structured and around 150-200 words.
        
        Response:
    """

    response = client.messages.create(
                model="claude-3-5-sonnet-20240620",
                temperature=0.8,
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

    return response.content[0].text

def main():
    csv_file_path = "casper_scenarios.csv"  # Replace with your CSV file path
    scenarios = read_csv(csv_file_path)

    # Create PDF
    create_pdf(scenarios, "casper_responses.pdf")

    print("PDF has been created successfully.")

if __name__ == "__main__":
    main()