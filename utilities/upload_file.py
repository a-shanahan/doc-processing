"""
This script provides example code for a user to upload an example file.
"""
from pdf2image import convert_from_path
import requests
import ast

pth = '../file_storage/SMART_paper.pdf'
pdf_2_image = convert_from_path(pth)
pil_image = pdf_2_image[0]

url = 'http://localhost:5050/upload'
with open(pth, 'rb') as f:
    response = requests.post(url, files={'file': f})

resp = ast.literal_eval(response.text)
print(resp)
