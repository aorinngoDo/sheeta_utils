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
