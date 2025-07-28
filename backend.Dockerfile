FROM baserow/backend:1.34.5

USER root

COPY ./plugins/teople1/ $BASEROW_PLUGIN_DIR/teople1/
RUN /baserow/plugins/install_plugin.sh --folder $BASEROW_PLUGIN_DIR/teople1

USER $UID:$GID
