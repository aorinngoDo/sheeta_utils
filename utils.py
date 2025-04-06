from .classes import Sheeta, SheetaChannel, SheetaLive, SheetaVideo


def get_sheeta_class(url: str) -> SheetaChannel|SheetaVideo|None:
    sheeta_class_obj = Sheeta(url)
    sheeta_class_obj.set_site_settings()
    if sheeta_class_obj.type == "video":
        return SheetaVideo(url)
    elif sheeta_class_obj.type == "live":
        return SheetaLive(url)
    elif sheeta_class_obj.type == "channel":
        return SheetaChannel(url)
    else:
        return None

def get_sheeta_class_type(url: str) -> str|None:
    """
    Get the type of the Sheeta class based on the URL.

    Args:
        url (str): URL of the video

    Returns:
        str: Type of the Sheeta class (video, live, channel)
    """
    sheeta_class_obj = Sheeta(url)
    sheeta_class_obj.set_site_settings()
    return sheeta_class_obj.type
