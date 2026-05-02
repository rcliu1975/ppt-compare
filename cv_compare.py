import cv2
import numpy as np


def compare_images(img1_path: str, img2_path: str, diff_out_path: str) -> bool:
    """
    Compare two images using OpenCV.
    Draw red bounding boxes around differences.
    Save a side-by-side comparison image to diff_out_path.
    Returns True if images are identical (no significant difference), False otherwise.
    """
    img1 = cv2.imread(img1_path)
    img2 = cv2.imread(img2_path)

    if img1 is None or img2 is None:
        raise ValueError(f"Could not read one of the images: {img1_path}, {img2_path}")

    # Resize img2 to match img1 if they have different sizes
    if img1.shape != img2.shape:
        img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))

    # Convert to grayscale for diffing
    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

    # Compute absolute difference
    diff = cv2.absdiff(gray1, gray2)

    # Threshold the difference to get a binary mask
    _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)

    # Find contours of differences
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    has_diff = False

    # Draw red rectangles around differences on a copy of img2
    img2_marked = img2.copy()
    for contour in contours:
        if cv2.contourArea(contour) > 50:  # filter out very small noise
            x, y, w, h = cv2.boundingRect(contour)
            # Draw red bounding box
            cv2.rectangle(img2_marked, (x, y), (x + w, y + h), (0, 0, 255), 2)
            has_diff = True

    # Create a 3-channel version of the diff mask so we can stack it horizontally
    diff_color = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)

    # Side-by-side: old | new (with boxes) | diff mask
    side_by_side = np.hstack((img1, img2_marked, diff_color))

    cv2.imwrite(diff_out_path, side_by_side)

    return not has_diff
