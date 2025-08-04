from baserow.core.registries import plugin_registry
from django.apps import AppConfig


class PluginNameConfig(AppConfig):
    name = "teople1"

    def ready(self):
        from .plugins import PluginNamePlugin

        plugin_registry.register(PluginNamePlugin())


# from django.apps import AppConfig
# from baserow.core.registries import (
#     plugin_registry,
#     application_type_registry,
#     object_scope_type_registry,
#     operation_type_registry
# )
# from baserow.core.action.registries import action_type_registry
# from baserow.core.trash.registries import trash_item_type_registry
#
# class Teople1Config(AppConfig):
#     name = "teople1"
#
#     def ready(self):
#         # Import all components
#         from .plugins import Teople1Plugin
#         from .application_types import Teople1ApplicationType
#         from .actions import CreateTeople1ItemActionType, UpdateTeople1ItemActionType
#         from .trash import Teople1ItemTrashableItemType
#         from .object_scopes import Teople1ObjectScopeType, Teople1ItemObjectScopeType
#         from .operations import RestoreTeople1ItemOperationType
#
#         # Register components
#         plugin_registry.register(Teople1Plugin())
#         application_type_registry.register(Teople1ApplicationType())
#         action_type_registry.register(CreateTeople1ItemActionType())
#         action_type_registry.register(UpdateTeople1ItemActionType())
#         trash_item_type_registry.register(Teople1ItemTrashableItemType())
#         object_scope_type_registry.register(Teople1ObjectScopeType())
#         object_scope_type_registry.register(Teople1ItemObjectScopeType())
#         operation_type_registry.register(RestoreTeople1ItemOperationType())