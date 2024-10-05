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


def create_toc(scenarios):
    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle(fontName='Helvetica-Bold', fontSize=14, name='TOCHeading1', leftIndent=20, firstLineIndent=-20,
                       spaceBefore=5, leading=16),
    ]
    return toc


def create_summary_table(scenarios):
    data = [["Scenario", "Summary"]]
    for i, scenario in enumerate(scenarios, 1):
        summary = scenario['Scenario'][:100] + "..." if len(scenario['Scenario']) > 100 else scenario['Scenario']
        data.append([f"Scenario {i}", Paragraph(summary, ParagraphStyle('Summary', fontName='Helvetica', fontSize=10))])

    table = Table(data, colWidths=[100, 400])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    return table


def create_pdf(scenarios, filename):
    doc = SimpleDocTemplate(filename, pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=18)
    Story = []
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))
    styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER))

    # Add title
    Story.append(Paragraph("Casper Test Responses", styles['Title']))
    Story.append(Spacer(1, 12))

    # Add table of contents
    toc = create_toc(scenarios)
    Story.append(toc)
    Story.append(PageBreak())

    # Add summary table
    Story.append(Paragraph("Scenario Summaries", styles['Heading1']))
    Story.append(Spacer(1, 12))
    Story.append(create_summary_table(scenarios))
    Story.append(PageBreak())

    for i, scenario in tqdm(enumerate(scenarios, 1), total=len(scenarios)):
        # Add bookmark for TOC
        scenario_title = f"Scenario {i}: {scenario['Scenario'][:50]}..."
        Story.append(Paragraph(scenario_title, styles['Heading1']))
        Story.append(Spacer(1, 12))

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