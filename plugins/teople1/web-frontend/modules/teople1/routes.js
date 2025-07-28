import path from 'path'

export const routes = [
  {
    name: 'starting',
    path: '/starting',
    component: path.resolve(__dirname, 'pages/starting.vue'),
  },
   {
    name: 'example',
    path: '/example',
    component: path.resolve(__dirname, 'pages/example.vue'),
  },
  {
    name: 'login',
    path: '/demo/login',
    component: path.resolve(__dirname, 'pages/login.vue'),
  },
  {
    name: 'dashboard',
    path: '/demo/dashboard',
    component: path.resolve(__dirname, 'layouts/dashboard.vue'),
  },
  {
    name: 'index',
    path: '/demo/index',
    component: path.resolve(__dirname, 'pages/demo/index.vue'),
  },
]
