def prompt_generate_prompts(x: str):
    return f"""
generate 10 prompts to generate this {x} (that i intend to use to  fine tune a model to be able to generate this {x} when prompted by those prompts):

"""


def prompt_summarize_pdf(text: str) -> str:
    return f"Summarize and clean the following text extracted from a PDF document: \n{text}"


def prompt_summarize_csv_table(text: str) -> str:
    return f"Construct tables from the following CSV data: \n{text}"


def prompt_summarize_csv(text: str) -> str:
    return f"Summarize and clean the following text extracted from a CSV file: \n{text}"


def prompt_summarize_excel_table(text: str) -> str:
    return f"Construct tables from the following Excel data: \n{text}"


def prompt_summarize_excel(text: str) -> str:
    return f"Summarize and clean the following text extracted from an Excel file: \n{text}"


def prompt_summarize_word(text: str) -> str:
    return f"Summarize and clean the following text extracted from a Word document: \n{text}"


def prompt_summarize_json(text: str) -> str:
    return f"Summarize and clean the following text extracted from a JSON file: \n{text}"


def prompt_summarize_xml(text: str) -> str:
    return f"Summarize and clean the following text extracted from an XML file: \n{text}"


def prompt_summarize_ppt(text: str) -> str:
    return f"Summarize and clean the following text extracted from a presentation: \n{text}"


def prompt_summarize_txt(text: str) -> str:
    return f"Summarize and clean the following text extracted from a text file: \n{text}"


def prompt_summarize_html(text: str) -> str:
    return f"Summarize and clean the following text extracted from a HTML file: \n{text}"


def prompt_summarize_md(text: str) -> str:
    return f"Summarize and clean the following text extracted from a Markdown file: \n{text}"
