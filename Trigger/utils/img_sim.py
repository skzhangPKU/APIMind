from PIL import Image
from io import BytesIO
import numpy as np
from scipy.stats import wasserstein_distance

def fromimage(im, flatten):
    if flatten:
        im = im.convert('F')
    a = np.array(im)
    return a

def get_histogram(img):
  h, w = img.shape
  hist = [0.0] * 256
  for i in range(h):
    for j in range(w):
      hist[img[i, j]] += 1
  return np.array(hist) / (h * w)

def normalize_exposure(img):
  img = img.astype(int)
  hist = get_histogram(img)
  cdf = np.array([sum(hist[:i+1]) for i in range(len(hist))])
  sk = np.uint8(255 * cdf)
  height, width = img.shape
  normalized = np.zeros_like(img)
  for i in range(0, height):
    for j in range(0, width):
      normalized[i, j] = sk[img[i, j]]
  return normalized.astype(int)


def get_img(img, norm_exposure=False):
    pil_img = Image.open(BytesIO(img))
    img = fromimage(pil_img, flatten=True)
    if norm_exposure:
        img = normalize_exposure(img)
    return img

def earth_movers_distance(img_b, img_a):
    pil_imga = get_img(img_a, norm_exposure=True)
    pil_imgb = get_img(img_b, norm_exposure=True)
    hist_a = get_histogram(pil_imga)
    hist_b = get_histogram(pil_imgb)
    return wasserstein_distance(hist_a, hist_b)