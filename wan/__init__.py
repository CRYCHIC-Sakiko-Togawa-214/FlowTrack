from .text2video import WanT2V

try:
    from .image2video import WanI2V
except ImportError:
    WanI2V = None

__all__ = ["WanT2V", "WanI2V"]
