export default {
 router: {
    extendRoutes(nuxtRoutes, resolve) {
      routes.forEach(route => {
        nuxtRoutes.push({
          name: route.name,
          path: route.path,
          component: resolve(__dirname, route.component),
        })
      })
    }
  }
}