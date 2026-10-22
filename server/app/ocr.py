"""服务端 OCR：rapidocr_onnxruntime（PaddleOCR 模型的 ONNX 版），中文印刷体识别。
引擎懒加载，首次调用时下载模型（约 20MB）。"""
import io
import numpy as np
from PIL import Image

_engine = None

def _get_engine():
    global _engine
    if _engine is None:
        from rapidocr_onnxruntime import RapidOCR
        _engine = RapidOCR()
    return _engine

def ocr_image(data: bytes) -> str:
    """识别图片字节中的文字，按行拼接返回。"""
    img = Image.open(io.BytesIO(data)).convert("RGB")
    arr = np.array(img)
    result, _ = _get_engine()(arr)
    if not result:
        return ""
    lines = []
    for box, text, conf in result:
        t = (text or "").strip()
        if t:
            lines.append(t)
    return "\n".join(lines)
