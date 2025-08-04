<template>
  <div class="login-container">
    <div class="login-box">
      <h2 class="text-2xl font-semibold mb-4">Login</h2>
      <form @submit.prevent="login">
        <input v-model="email" type="email" placeholder="Email" required />
        <input v-model="password" type="password" placeholder="Password" required />
        <button type="submit">Login</button>
      </form>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      email: '',
      password: '',
    }
  },
  methods: {
    login() {
      // Static/fake login
      if (this.email === 'admin@example.com' && this.password === 'admin') {
        localStorage.setItem('isLoggedIn', true)
        this.$router.push('/demo/index') // Redirect to dashboard
      } else {
        alert('Invalid credentials')
      }
    }
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: #edf2f7;
}

.login-box {
  background: white;
  padding: 30px;
  border-radius: 8px;
  width: 300px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  text-align: center;
}

input {
  width: 100%;
  padding: 10px;
  margin-bottom: 15px;
  border-radius: 4px;
  border: 1px solid #ccc;
}

button {
  width: 100%;
  padding: 10px;
  background-color: #2d3748;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
</style>
