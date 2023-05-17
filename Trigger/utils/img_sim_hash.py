from PIL import Image
import imagehash
from io import BytesIO

def img_hash_distance(img_b,img_a):
    pil_img_a = Image.open(BytesIO(img_a))
    pil_img_b = Image.open(BytesIO(img_b))
    image_a_hash = imagehash.phash(pil_img_a)
    image_b_hash = imagehash.phash(pil_img_b)
    similarity = image_a_hash - image_b_hash
    print('similarity is ',similarity)
    return similarity
