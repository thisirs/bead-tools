#!/usr/bin/python2

"""This script unpacks sprites from an image file and store them in a
subdirectory.

"""

import os
import argparse
import numpy as np
import cv2

# For .gif files
from PIL import Image

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('file', help="name of the image file to extract from")
parser.add_argument("-d",
                    "--directory",
                    type=str,
                    help="directory where sprites are stored")
parser.add_argument("-f",
                    "--format",
                    type=str,
                    help="format of stored sprites",
                    default='{filename}-{num:0>{length}}.png')
parser.add_argument("-m",
                    "--min-area",
                    type=int,
                    help="minimum area of extracted sprites",
                    default=15)
parser.add_argument("-M",
                    "--max-area",
                    type=int,
                    help="maximum area of extracted sprites",
                    default=np.Inf)
parser.add_argument("-r",
                    "--resize-factor",
                    type=int,
                    help="resize factor",
                    default=1)
args = parser.parse_args()

# Initializing parameters
filepath = args.file
sm_dir, sm_name = os.path.split(filepath)
sm_name, sm_ext = os.path.splitext(sm_name)

if args.directory:
    directory = args.directory
else:
    directory = os.path.join(sm_dir, sm_name + "_sprites")

if os.path.exists(directory):
    if not os.path.isdir(directory):
        raise "File already existing, aborting"
else:
    print("Creating directory {0}".format(directory))
    os.makedirs(directory)

cntsMinArea = args.min_area
cntsMaxArea = args.max_area
s_name_format = os.path.join(directory, args.format)

# Load image
if filepath.endswith('.gif'):
    # OpenCV does not load .gif files
    pic = Image.open(filepath)
    rgb = pic.convert('RGB')
    imgInput = np.array(rgb)

    # BGR instead of RGB
    imgInput = imgInput[:, :, ::-1]
else:
    imgInput = cv2.imread(filepath, cv2.IMREAD_UNCHANGED)

if imgInput is None:
    raise "Unable to load image file {0}".format(filepath)

if len(imgInput.shape) == 2 or imgInput.shape[2] == 1:
    imgInput = cv2.cvtColor(imgInput, cv2.COLOR_GRAY2RGB)

# Add alpha channel
if imgInput.shape[2] == 3:
    b, g, r = cv2.split(imgInput)
    a = 255 * np.ones(imgInput.shape[:2], dtype=np.uint8)
    imgInput = cv2.merge((b, g, r, a))

# Identifying background color
merge = imgInput[:, :, 0] + \
        np.left_shift(imgInput[:, :, 1].astype(np.uint32), 8) + \
        np.left_shift(imgInput[:, :, 2].astype(np.uint32), 16)

counts = np.bincount(merge.flatten())
c = np.argmax(counts)

b = c & 0xFF
g = (c >> 8) & 0xFF
r = (c >> 16) & 0xFF

background_color0 = np.array([b, g, r, 0])
background_color255 = np.array([b, g, r, 255])

print("Background color is: ({0}, {1}, {2})".format(b, g, r))

# Add background border
imgInput = cv2.copyMakeBorder(imgInput, 1, 1, 1, 1, cv2.BORDER_CONSTANT, value=background_color255)
# cv2.imwrite('imgInput.png', imgInput)

# Mask out of image
m = cv2.inRange(imgInput, background_color0, background_color255)
# cv2.imwrite('tmask.png', m)

mask = 255 - cv2.inRange(imgInput, background_color0, background_color255)
# cv2.imwrite('mmask.png', mask)

imgInput[mask == 0] = [0, 0, 0, 0]
# cv2.imwrite('blah.png', imgInput)

imgMask = cv2.cvtColor(mask, cv2.COLOR_GRAY2RGB)
# cv2.imwrite('mask.png', imgMask)

imgGray = cv2.cvtColor(imgMask, cv2.COLOR_RGB2GRAY)
# cv2.imwrite('mask_gray.png', imgGray)

# Find Contours
cnts, hierarchy = cv2.findContours(imgGray.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

print("{0} potential sprites found".format(len(cnts)))


# Remove the small ones
def by_size(x):
    return cntsMinArea < cv2.contourArea(x) < cntsMaxArea


def valid_sprite(i, cnts, hierarchy):
    """A valid sprite complies with fixed size and its parent is not a
    sprite."""
    return by_size(cnts[i]) and \
        not (hierarchy[0, i, 3] != -1 and
             by_size(cnts[hierarchy[0, i, 3]]))

cnts = [c for i, c in enumerate(cnts) if valid_sprite(i, cnts, hierarchy)]

print("{0} sprites identified".format(len(cnts)))

height = int(np.round(np.mean([cv2.boundingRect(x)[3] for x in cnts])))


def sort_by_row(x):
    (x, y) = cv2.boundingRect(x)[:2]
    return (y//height*height, x)

# Trying to sort line by line
cnts = sorted(cnts, key=sort_by_row)

# Draw Contours
imgCnts = imgInput.copy()
cv2.drawContours(imgCnts, cnts, -1, (255, 128, 255), -1)
# cv2.imwrite('gui Contours.png', imgCnts)

# Extract contours images
imgBlank = np.zeros_like(imgInput)
# imgBlank = np.zeros(shape=(imgInput.shape[0], imgInput.shape[1], 4))
cntsLen = len(cnts)

for i, cnt in enumerate(cnts):
    print('Extracting sprite {0}/{1}'.format(i+1, cntsLen))

    # Create contour mask
    mask = cv2.cvtColor(imgBlank.copy(), cv2.COLOR_BGRA2GRAY)
    cv2.drawContours(mask, cnts, i, 255, thickness=cv2.cv.CV_FILLED)

    # Apply mask to Input Img
    imgCnt = imgBlank.copy()
    imgCnt[mask == 255] = imgInput[mask == 255]

    # Extract bounding rect of the crop
    bRect = cv2.boundingRect(cnt)

    # Crops contours
    x, y, w, h = bRect
    imgCntCropped = imgCnt[y:y+h, x:x+w]

    # Sava image to file
    length = int(np.floor(np.log10(cntsLen)))+1
    fname = s_name_format.format(filename=sm_name, num=i+1, length=length)

    size = tuple([args.resize_factor*x for x in imgCntCropped.shape[::-1][1:]])
    imgResized = cv2.resize(imgCntCropped, size, interpolation=cv2.INTER_NEAREST)
    cv2.imwrite(fname, imgResized)
