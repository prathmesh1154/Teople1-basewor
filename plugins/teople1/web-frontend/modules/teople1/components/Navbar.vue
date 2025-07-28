<template>
  <header class="navbar">
    <div class="navbar-left">
      <h1 class="logo">Admin Panel</h1>
    </div>
    <div class="welcome-message">
      Welcome, <strong>Admin</strong>
    </div>
  </header>
</template>

<style scoped>
.navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  background: #ffffff;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  z-index: 1000;
}

.logo {
  font-size: 1.2rem;
}

.welcome-message {
  font-size: 0.9rem;
}
</style>