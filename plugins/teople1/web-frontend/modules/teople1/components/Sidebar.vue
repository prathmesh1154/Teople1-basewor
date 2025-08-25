<template>
  <aside :class="['app-sidebar', { collapsed: isCollapsed, mobile: isMobile, open: isOpen }]">
    <nav class="sidebar-nav">
      <NuxtLink to="/demo/index" exact class="nav-link" data-tooltip="Dashboard">
        <i class="fas fa-tachometer-alt"></i>
        <span v-if="!isCollapsed || isMobile">Dashboard</span>
      </NuxtLink>

      <NuxtLink to="/demo/users" class="nav-link" data-tooltip="Users">
        <i class="fas fa-users"></i>
        <span v-if="!isCollapsed || isMobile">Users</span>
      </NuxtLink>

      <NuxtLink to="/course/courses" class="nav-link" data-tooltip="Courses">
        <i class="fas fa-book"></i>
        <span v-if="!isCollapsed || isMobile">Courses</span>
      </NuxtLink>

      <NuxtLink to="/demo/tasks" class="nav-link" data-tooltip="Tasks">
        <i class="fas fa-tasks"></i>
        <span v-if="!isCollapsed || isMobile">Tasks</span>
      </NuxtLink>

      <NuxtLink to="/auth/login" class="nav-link" @click.prevent="logout" data-tooltip="Logout">
        <i class="fas fa-sign-out-alt"></i>
        <span v-if="!isCollapsed || isMobile">Logout</span>
      </NuxtLink>
    </nav>

    <div class="sidebar-footer" v-if="!isCollapsed || isMobile">
      Logged in as <strong>Admin</strong>
    </div>
  </aside>
</template>

<script>
export default {
  props: {
    isCollapsed: { type: Boolean, default: false },
    isMobile: { type: Boolean, default: false },
    isOpen: { type: Boolean, default: false }
  },
  methods: {
    logout() {
      console.log("Logout clicked")
    }
  }
}
</script>

<style scoped>
.app-sidebar {
  position: fixed;
  top: 60px;
  left: 0;
  width: 220px;
  background: #2d3748;
  color: white;
  height: calc(100vh - 60px);
  display: flex;
  flex-direction: column;
  transition: all 0.3s ease;
  z-index: 1000;
}

.app-sidebar.collapsed {
  width: 60px;
}

.app-sidebar.mobile {
  transform: translateX(-100%);
  width: 220px;
}

.app-sidebar.mobile.open {
  transform: translateX(0);
  box-shadow: 2px 0 6px rgba(0,0,0,0.3);
}

.sidebar-nav {
  flex: 1;
  padding: 20px 0;
}

.nav-link {
  position: relative;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 20px;
  color: #cbd5e0;
  text-decoration: none;
  transition: all 0.2s;
  font-size: 15px;
}

.nav-link i {
  font-size: 18px;
  width: 20px;
  text-align: center;
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

/* ✅ Custom tooltip style */
.app-sidebar.collapsed .nav-link span {
  display: none;
}

.app-sidebar.collapsed .nav-link::after {
  content: attr(data-tooltip);
  position: absolute;
  left: 70px;
  top: 50%;
  transform: translateY(-50%);
  background: #1a202c;
  color: #fff;
  padding: 6px 10px;
  border-radius: 6px;
  white-space: nowrap;
  font-size: 13px;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.2s ease, transform 0.2s ease;
  transform: translateY(-50%) translateX(5px);
  z-index: 2000;
}

.app-sidebar.collapsed .nav-link:hover::after {
  opacity: 1;
  transform: translateY(-50%) translateX(0);
}
</style>
