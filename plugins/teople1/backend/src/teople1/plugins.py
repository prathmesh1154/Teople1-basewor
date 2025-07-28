from loguru import logger
from baserow.core.registries import Plugin
from django.urls import path, include

from .api import urls as api_urls


class PluginNamePlugin(Plugin):
    type = "teople1"

    def get_api_urls(self):
        return [
            path(
                "teople1/",
                include(api_urls, namespace=self.type),
            ),
        ]
