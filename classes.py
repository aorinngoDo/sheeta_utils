import re
from urllib.parse import parse_qs, urlparse

import requests


class Sheeta:
    """
    Sheeta class for getting site settings and checking URL type

    Args:
        url (str): URL of the site

    Attributes:
        url (str): URL of the site
        type (str): Type of the site (channel or video)
        base_domain (str): Base domain of the site
        site_settings (dict): Site settings
        base_headers (dict): Base headers for requests
        fcid (int): Fanclub site ID
    """

    def __init__(self, url: str):
        self.url = str(url)
        self.type = None
        self.base_domain = None
        self.site_settings = {}
        self.base_headers = {}
        self.fcid = None

    def __str__(self):
        return f"{self.__class__.__name__}: ({self.__dict__})"

    def check_url_type(self, useragent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0"):
        try:
            parsed_url = urlparse(self.url)
        except Exception as e:
            raise ValueError(f"Invalid URL: {e}")
        if parsed_url.scheme != "https":
            raise ValueError("Invalid URL: URL must be HTTPS")
        parsed_url_text = f"{parsed_url.netloc}{parsed_url.path}" if parsed_url.path != "" else f"{parsed_url.netloc}/"

        self.base_domain = parsed_url.netloc

        try:
            import fake_useragent
            useragent = fake_useragent.UserAgent(os='Windows', browsers=['Edge', 'Chrome']).random
        except ImportError:
            pass

        self.base_headers = {
                'fc_use_device': 'null',
                'origin': f'https://{self.base_domain}',
                'referer': f'https://{self.base_domain}/',
                'user-agent': useragent,
                'accept': 'application/json, text/plain, */*',
                'accept-language': 'ja,en-US;q=0.9,en;q=0.8',
            }

        if re.match(r"^[^/]+/[^/]+/(video|audio)/[A-Za-z0-9]+$", parsed_url_text):
            # multi channel site (with channel name) / single video
            self.type = "video"
            self.channel_id = parsed_url.path.split("/")[-3]
            self.video_id = parsed_url.path.split("/")[-1]

        elif re.match(r"^[^/]+/(video|audio)/[A-Za-z0-9]+$", parsed_url_text):
            # single channel site / single video
            self.type = "video"
            self.video_id = parsed_url.path.split("/")[-1]

        elif re.match(r"^[^/]+/[^/]+/(live)/[A-Za-z0-9]+$", parsed_url_text):
            # multi channel site (with channel name) / single live
            self.type = "live"
            self.channel_id = parsed_url.path.split("/")[-3]
            self.video_id = parsed_url.path.split("/")[-1]

        elif re.match(r"^[^/]+/(live)/[A-Za-z0-9]+$", parsed_url_text):
            # single channel site / single live
            self.type = "live"
            self.video_id = parsed_url.path.split("/")[-1]

        elif re.match(r"^[^/]+/[^/]+(/videos/?|/)?$", parsed_url_text):
            # multi channel site (with channel name) / videos
            self.type = "channel"
            self.channel_id = parsed_url.path.split("/")[1]
            self.tag = parse_qs(parsed_url.query).get("tag", [None])[0]

        elif re.match(r"^[^/]+(/videos/?|/)?$", parsed_url_text):
            # single channel site / videos
            self.type = "channel"
            self.tag = parse_qs(parsed_url.query).get("tag", [None])[0]

        else:
            raise ValueError("Invalid URL: could not determine URL type")

    def set_site_settings(self):
        if not self.base_domain:
            self.check_url_type()
        try:
            site_settings_request = requests.get(f"https://{self.base_domain}/site/settings.json", headers=self.base_headers, timeout=20)
            site_settings_request.raise_for_status()
            self.site_settings = site_settings_request.json()
            if not (isinstance(self.site_settings, dict) and isinstance(self.site_settings.get("api_base_url"), str)):
                raise ValueError("Failed to get site settings")
        except Exception as e:
            raise ValueError(f"Failed to get site settings: {e}")

    def set_fcid(self):
        if not self.site_settings:
            self.set_site_settings()

        if self.site_settings.get("channel") is True or self.site_settings.get("channel") is None:
            try:
                ch_fcid_request = requests.get(f'{self.site_settings.get("api_base_url")}/content_providers/channels', headers=self.base_headers, timeout=20)
                ch_fcid_request.raise_for_status()
                fcid = [data for data in ch_fcid_request.json().get("data", {}).get("content_providers", []) if data["domain"] == f"https://{self.base_domain}/{self.channel_id}"][0].get("id")
                if fcid is None or not isinstance(fcid, int):
                    raise ValueError("Failed to get fcid")
                self.fcid = fcid
            except Exception as e:
                raise ValueError(f"Failed to get fcid: {e}")
        else:
            self.fcid = self.site_settings.get("fanclub_site_id")

class SheetaVideo(Sheeta):

    """
    SheetaVideo class for getting video info

    Args:
        url (str): URL of the video

    Attributes:
        url (str): URL of the video
        type (str): Type of the video (video)
        channel_id (str): Channel ID of the video
        video_id (str): Video ID
        video_info_dump (dict): Video info dump
    """

    def __init__(self, url: str):
        super().__init__(url)
        self.type = "video"
        self.channel_id = None
        self.video_id = None
        self.video_info_dump = {}

    def get_video_info(self):
        if not self.fcid:
            self.set_fcid()

        try:
            video_info_request = requests.get(f'{self.site_settings.get("api_base_url")}/video_pages/{self.video_id}', headers=self.base_headers|{'fc_site_id': str(self.fcid)}, timeout=20)
            video_info_request.raise_for_status()
            self.video_info_dump = video_info_request.json()
        except Exception as e:
            raise ValueError(f"Failed to get video info: {e}")

class SheetaLive(SheetaVideo):

    """
    SheetaLive class for getting live info

    Args:
        url (str): URL of the live

    Attributes:
        url (str): URL of the video
        type (str): Type of the video (live)
        channel_id (str): Channel ID of the video
        video_id (str): Video ID
        video_info_dump (dict): Video info dump
    """

    def __init__(self, url: str):
        super().__init__(url)
        self.type = "live"

class SheetaChannel(Sheeta):

    """
    SheetaChannel class for getting video list

    Args:
        url (str): URL of the channel

    Attributes:
        url (str): URL of the channel
        type (str): Type of the channel (channel)
        channel_id (str): Channel ID of the channel
        tag (str): Tag of the channel
        video_dumps (list): Video info dumps
        videos (list): Video objects
        live_dumps (list): Live info dumps
        lives (list): Live objects
    """

    def __init__(self, url: str):
        super().__init__(url)
        self.type = "channel"
        self.channel_id = None
        self.tag = None
        self.video_dumps = []
        self.videos = []
        self.live_dumps = []
        self.lives = []

    def _get_pages_list(self, page_type: str, params: tuple = ()):
        if not self.fcid:
            self.set_fcid()

        if not page_type == "video" and not page_type == "live":
            raise ValueError("Invalid page type")

        _page_num = 1
        params_original = params

        while True:
            params = params_original + (('page', _page_num), ('per_page', '100'), ('sort', 'display_date'))
            if self.tag:
                params = params + (('tag', self.tag),)

            try:
                video_list_request = requests.get(f'{self.site_settings.get("api_base_url")}/fanclub_sites/{self.fcid}/{page_type}_pages', headers=self.base_headers, params=params, timeout=20)
                video_list_request.raise_for_status()
                video_list_json = video_list_request.json()

                video_info_list = video_list_json.get("data", {}).get("video_pages", {}).get("list", [])
                video_url_list = [f'https://{self.base_domain}/{self.channel_id + "/" if self.channel_id else "" }{page_type}/{video.get("content_code")}' for video in video_info_list]

                if page_type == "video":
                    self.video_dumps.extend(video_info_list)
                    self.videos.extend([SheetaVideo(video_url) for video_url in video_url_list])
                elif page_type == "live":
                    self.live_dumps.extend(video_info_list)
                    self.lives.extend([SheetaLive(video_url) for video_url in video_url_list])

                if len(video_info_list) < 100:
                    break
                else:
                    _page_num += 1
            except requests.exceptions.RequestException as e:
                break
            except Exception as e:
                raise ValueError(f"Failed to get video list: {e}")

    def get_videos_list(self):
        self._get_pages_list(
            page_type = "video",
            params = (
                ('sort', '-display_date'),
            )
        )

    def get_lives_now_list(self):
        self._get_pages_list(
            page_type = "live",
            params = (
                ('live_type', '1'),
            )
        )

    def get_lives_schedule_list(self):
        self._get_pages_list(
            page_type = "live",
            params = (
                ('live_type', '2'),
            )
        )
