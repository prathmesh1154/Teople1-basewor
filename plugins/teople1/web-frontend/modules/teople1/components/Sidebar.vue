<template>
  <aside class="app-sidebar">
    <nav class="sidebar-nav">
      <NuxtLink to="/demo/index" exact class="nav-link">Dashboard</NuxtLink>
      <NuxtLink to="/demo/users" class="nav-link">Users</NuxtLink>
      <NuxtLink to="/course/courses" class="nav-link">Courses</NuxtLink>
      <NuxtLink to="/demo/tasks" class="nav-link">Tasks</NuxtLink>
      <NuxtLink to="/auth/login" class="nav-link" @click.prevent="logout">Logout</NuxtLink>

    </nav>
    <div class="sidebar-footer">
      Logged in as <strong>Admin</strong>
    </div>
  </aside>
</template>

<style scoped>
.app-sidebar {
  position: fixed;
  top: 60px; /* Navbar height */
  left: 0;
  width: 220px;
  background: #2d3748;
  color: white;
  height: calc(100vh - 0px);
  display: flex;
  flex-direction: column;
}

.sidebar-nav {
  flex: 1;
  padding: 20px 0;
}

.nav-link {
  display: block;
  padding: 12px 20px;
  color: #cbd5e0;
  text-decoration: none;
  transition: all 0.2s;
}

.nav-link:hover,
.nuxt-link-exact-active {
  background: #4a5568;
  color: white;
  font-weight: 500;
}

.sidebar-footer {
  padding: 15px 20px;
  border-top: 1px solid #4a5568;
  font-size: 0.875rem;
  color: #cbd5e0;
}
</style>