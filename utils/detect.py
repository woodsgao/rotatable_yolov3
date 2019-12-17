import numpy as np
import cv2
import torch
from pytorch_modules.utils import device
from .utils import non_max_suppression, scale_coords


@torch.no_grad()
def detect(model, img, img_size=(320, 320), conf_thres=0.3, nms_thres=0.5):
    im0 = img
    img = im0.copy()
    img = cv2.resize(img, img_size)
    img = img[:, :, ::-1]
    img = img.transpose(2, 0, 1)
    img = np.float32([img]) / 255.
    img = torch.FloatTensor(img).to(device)
    pred = model(img)[0]

    # Apply NMS
    det = non_max_suppression(pred, conf_thres, nms_thres)[0]

    # Process detections
    if det is None:
        det = []
    if len(det):

        # Rescale boxes from img_size to im0 size
        det[:, :4] = scale_coords(img.shape[2:], det[:, :4],
                                  im0.shape[:2]).round()
    return det