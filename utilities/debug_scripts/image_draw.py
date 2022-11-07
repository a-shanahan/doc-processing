"""
Draw bounding boxes around detected text.
"""
from PIL import ImageDraw
import requests
import ast
from pdf2image import convert_from_path

pth = '../../file_storage/SMART_paper.pdf'
pdf_2_image = convert_from_path(pth)
pil_image = pdf_2_image[0]

url = 'http://localhost:5050/upload'
with open(pth, 'rb') as f:
    response = requests.post(url, files={'file': f})

resp = ast.literal_eval(response.text)

boxes = []
for i in resp['message']:
    for j in i:
        x1 = j['Co-ordinates'].get('x1')
        x2 = j['Co-ordinates'].get('x2')
        y1 = j['Co-ordinates'].get('y1')
        y2 = j['Co-ordinates'].get('y2')
        shape = [(x1, y1), (x2, y2)]
        boxes.append(shape)

img1 = ImageDraw.Draw(pil_image)
for box in boxes:
    img1.rectangle(box, outline='red')
pil_image.show()
