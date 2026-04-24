import mss
import numpy as np
import cv2

def capture_board(region):
    """
    Captures a specific region of the screen using mss.
    
    Args:
        region (tuple): (left, top, width, height)
    
    Returns:
        np.array: Captured image in BGR format.
    """
    with mss.mss() as sct:
        # mss expects: {'top': y, 'left': x, 'width': w, 'height': h}
        monitor = {
            "top": region[1],
            "left": region[0],
            "width": region[2],
            "height": region[3]
        }
        
        # Capture the screen
        screenshot = sct.grab(monitor)
        
        # Convert to numpy array and drop alpha channel
        img = np.array(screenshot)
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        
        return img
