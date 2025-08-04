import path from 'path'

export const routes = [
//  {
//    name: 'starting',
//    path: '/starting',
//    component: path.resolve(__dirname, 'pages/starting.vue'),
//  },
//   {
//    name: 'example',
//    path: '/example',
//    component: path.resolve(__dirname, 'pages/example.vue'),
//  },
{
  name: 'login',
  path: '/auth/login',
  component: path.resolve(__dirname, 'pages/authentication/login.vue'),
},

  {
    name: 'index',
    path: '/demo/index',
    component: path.resolve(__dirname, 'pages/demo/index.vue'),
  },
   {
    name: 'user',
    path: '/demo/users',
    component: path.resolve(__dirname, 'pages/demo/users.vue'),
  },
  {
    name: 'tasks',
    path: '/demo/tasks',
    component: path.resolve(__dirname, 'pages/demo/tasks.vue'),
  },
   {
    name: 'courses',
    path: '/course/courses',
    component: path.resolve(__dirname, 'pages/course/courses.vue'),
  },
  {
    name: 'course-detail',
    path: '/course/courses/:id',
    component: path.resolve(__dirname, 'pages/course/CourseDetailPage.vue'),
    props: true,
  },
]
