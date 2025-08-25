<template>
  <div class="app-container">
    <!-- Navbar -->
    <Navbar @toggle-sidebar="toggleSidebar" />

    <div class="app-content">
      <!-- Sidebar -->
      <Sidebar
        :is-collapsed="isSidebarCollapsed"
        :is-mobile="isMobile"
        :is-open="isSidebarOpen"
      />

      <!-- Overlay for mobile when sidebar is open -->
      <div v-if="isMobile && isSidebarOpen" class="overlay" @click="closeSidebar"></div>

      <!-- Main Content -->
      <main :class="['main-content', { expanded: isSidebarCollapsed && !isMobile }]">
        <Nuxt />
      </main>
    </div>
  </div>
</template>

<script>
import Navbar from '@teople1/components/Navbar.vue'
import Sidebar from '@teople1/components/Sidebar.vue'

export default {
  components: { Navbar, Sidebar },
  data() {
    return {
      isSidebarCollapsed: false,
      isSidebarOpen: false,
      isMobile: false
    }
  },
  mounted() {
    this.checkScreen()
    window.addEventListener('resize', this.checkScreen)
  },
  beforeDestroy() {
    window.removeEventListener('resize', this.checkScreen)
  },
  methods: {
    checkScreen() {
      this.isMobile = window.innerWidth < 768
      if (this.isMobile) {
        this.isSidebarCollapsed = false
      }
    },
    toggleSidebar() {
      if (this.isMobile) {
        this.isSidebarOpen = !this.isSidebarOpen
      } else {
        this.isSidebarCollapsed = !this.isSidebarCollapsed
      }
    },
    closeSidebar() {
      this.isSidebarOpen = false
    }
  }
}
</script>

<style>
.app-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.app-content {
  display: flex;
  flex: 1;
  margin-top: 60px; /* Navbar height */
}

.main-content {
  flex: 1;
  padding: 20px;
  background: #f8fafc;
  margin-left: 220px;
  min-height: calc(100vh);
  transition: margin-left 0.3s ease;
}

.main-content.expanded {
  margin-left: 60px;
}

/* On mobile, main content always full width */
@media (max-width: 768px) {
  .main-content {
    margin-left: 0 !important;
  }
}

/* Overlay for mobile drawer */
.overlay {
  position: fixed;
  top: 60px;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  z-index: 999;
}
</style>
