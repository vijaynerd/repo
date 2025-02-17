import requests
import json
import re
import fitz  # PyMuPDF
import pytesseract
from pdf2image import convert_from_path


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

def main():
    server_ip = "192.168.1.12"
    client = LLMChatClient(server_ip)

  #  context = """
   # The commanding victory allowed Pakista to complete the full set of ICC limited-overs titles – World Cups in both formats and the Champions Trophy – as India paid a heavy price for opting to chase a target in the title clash. This decision was perhaps influenced by their nine-wicket drubbing of Bangladesh in the semifinal, when they hunted down a target of 265 with nearly ten overs to spare. But had he reflected dispassionately on the events of June 4 when the teams met in a Group B fixture, it is possible that Virat Kohli would have heeded Anil Kumble’s words and opted to bat first in what would be the legendary leg-spinner’s last match as the Indian head coach.

#In the opening match of the tournament for both teams, Sarfaraz Ahmed stuck India in and had plenty of time, standing behind the stumps, to rue his decision on a terrific strip for batting at Edgbaston in Birmingham. The now well-established opening pair of Rohit Sharma and Shikhar Dhawan set the tone and India went from strength to strength on the back of their powerful top order. Such was the dominance of the top three – Rohit, Dhawan and skipper Kohli – throughout the tournament that most of the rest of the batting unit got just one hit before the final, perhaps a decisive factor when India were chasing a massive total of 338 for four.
    
 #   """
  #  prompt = "Extract city,county,district,country names in the above context. mention if it is a city, county or district, country"

    #summary = client.summarize(context, prompt)
 
    #print("Summary:", summary)

    pdf_path = "C:/Users/Admin/Downloads/abdomenscan.pdf"  # Replace with the actual path to your PDF file
    context = extract_text_from_pdf(pdf_path)
    print("Context:", context)
    # prompt = """Generate 5 mulitple choice questions. Take questions from the content only. should contain 4 options each. One correct optoin and 3 relevant but incorrect option. 
    #             Name the options as A, B, C, D.
    #             Don't make the questions too easy or too difficult. Give the answer key with question numbers and the correct answers at the end of all questions. cite the page number.
    #             """
    prompt = "The above text is copy of medical report of scan. Format the report in a way that it looks like a medical report. Finally describe the liver condition of the patient."
   
    summary = client.summarize(context, prompt)
 
    print("Quiz:", summary)
if __name__ == "__main__":
    main()