from starlite import Starlite, get, post, Request, Response
import aiofiles

import requests
import json
import re
import fitz  # PyMuPDF
import pytesseract
from pdf2image import convert_from_path
import markdown

class LLMChatClient:
    def __init__(self, server_ip, port=11434):
        self.server_url = f"http://{server_ip}:{port}/api/generate"

    def summarize(self, context, prompt):
        payload = {
            "model": "deepseek-r1",  # Replace with your model name if different
            "prompt": f"{context}\n\n{prompt}",
            "system_message": "You are a helpful assistant that gives concise answers.",
            "temperature": 0.1
        }
        try:
            response = requests.post(self.server_url, headers={"Content-Type": "application/json"}, data=json.dumps(payload))
            response_text = response.text

            if response.status_code != 200:
                error_data = json.loads(response_text)
                raise ValueError(f"HTTP error! status: {response.status}, message: {error_data.get('message', response.statusText)}")

            response_lines = response_text.strip().split('\n')
            final_response = ''.join(json.loads(line)['response'] for line in response_lines)
            # final_response = final_response.replace('</?think>', '')
            # final_response = final_response.replace('</think>', '').replace('<think>', '')
            final_response = re.sub(r'<think>.*?</think>', '', final_response, flags=re.DOTALL)

            return final_response
        except Exception as e:
            print(f"Error generating text: {e}")
            return str(e)

def extract_text_from_pdf(pdf_path, start_page=None, end_page=None):
        # Convert PDF pages to images
    pages = convert_from_path(pdf_path, 300)  # 300 is the DPI (dots per inch)

    # Extract text from each page
    text = ""
    pageno = 1
    for page in pages:
        text += "Pageno:" + str(pageno) + "\n" + pytesseract.image_to_string(page)
        pageno += 1

    # doc = fitz.open(pdf_path)
    # text = ""
    # start_page = start_page or 0
    # end_page = end_page or doc.page_count - 1

    # for page_num in range(start_page, end_page + 1):
    #     page = doc.load_page(page_num)
    #     text += page.get_text()
    return text


# HTML form to be served
html_form = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Upload PDF</title>
</head>
<body>
    <h1>Upload PDF File</h1>
    <form action="/upload" method="post" enctype="multipart/form-data">
        <label for="file">Choose a PDF file:</label>
        <input type="file" id="file" name="file" accept="application/pdf">
        <button type="submit">Upload</button>
    </form>
</body>
</html>
"""

@get("/process")
async def serve_form(request: Request) -> Response:
    return Response(html_form, media_type="text/html")

@post("/upload")
async def upload_pdf(request: Request) -> Response:
    form = await request.form()
    pdf_file = form.get("file")

    # Save the uploaded PDF file
    async with aiofiles.open(pdf_file.filename, 'wb') as out_file:
        content = await pdf_file.read()
        await out_file.write(content)

    # Pass the saved PDF file to another module (to be written later)
    output = process_pdf(pdf_file.filename)
    # Convert Markdown to HTML
    html_output = markdown.markdown(output)

    return Response(html_output, media_type="text/html")

#    return Response({"message": "File uploaded successfully", "output": output})

def process_pdf(file_path: str) -> str:
    # Placeholder function for processing the PDF

    server_ip = "ollama"
    client = LLMChatClient(server_ip)
    pdf_path = file_path  # Replace with the actual path to your PDF file
    context = extract_text_from_pdf(pdf_path)
    print("Context:", context)
    prompt = "The above text is copy of medical report of scan. Extract Patient name and age followed by doctor name and hospital name and location. Each information should be in a separate line."
   
    summary = client.summarize(context, prompt)
 
    print("Quiz:", summary)

    return summary

# Create the Starlite application
app = Starlite(route_handlers=[serve_form, upload_pdf])

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="myservice", port=8000)




