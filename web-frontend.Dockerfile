FROM baserow/web-frontend:1.34.5

USER root

COPY ./plugins/teople1/ /baserow/plugins/teople1/
RUN /baserow/plugins/install_plugin.sh --folder /baserow/plugins/teople1

USER $UID:$GID
