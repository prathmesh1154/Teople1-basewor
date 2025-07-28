FROM baserow/baserow:1.34.5

COPY ./plugins/teople1/ /baserow/plugins/teople1/
RUN /baserow/plugins/install_plugin.sh --folder /baserow/plugins/teople1
