import { PluginNamePlugin } from '@teople1/plugins'

export default (context) => {
  const { app } = context
  app.$registry.register('plugin', new PluginNamePlugin(context))
}
