from google.cloud import vision
import requests


async def perform_ocr(media_url):
    client = vision.ImageAnnotatorClient()

    response = requests.get(media_url)
    content = response.content

    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations

    if texts:
        return texts[0].description
    return ''
