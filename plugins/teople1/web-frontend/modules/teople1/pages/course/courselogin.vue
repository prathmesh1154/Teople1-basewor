<template>
  <div v-if="showModal" class="login-modal">
    <div class="modal-overlay" @click="closeModal"></div>
    <div class="modal-content">
      <button class="close-button" @click="closeModal">
        <i class="fas fa-times"></i>
      </button>

      <!-- Login Form -->
      <div v-if="!showRegister">
        <h2>Login to Continue</h2>
        <form @submit.prevent="handleLogin">
          <div class="form-group">
            <label for="login-username">Username</label>
            <input
              type="text"
              id="login-username"
              v-model="loginData.username"
              placeholder="Enter your username"
              required
              :class="{'input-error': formErrors.username}"
            />
            <p v-if="formErrors.username" class="error-text">{{ formErrors.username }}</p>
          </div>
          <div class="form-group">
            <label for="login-password">Password</label>
            <input
              type="password"
              id="login-password"
              v-model="loginData.password"
              placeholder="Enter your password"
              required
              :class="{'input-error': formErrors.password}"
            />
            <p v-if="formErrors.password" class="error-text">{{ formErrors.password }}</p>
          </div>
          <button type="submit" class="login-button" :disabled="loading">
            {{ loading ? 'Logging in...' : 'Login' }}
          </button>
        </form>
        <div class="login-footer">
          <p>Don't have an account? <a href="#" @click.prevent="toggleRegister">Sign up</a></p>
        </div>
      </div>

      <!-- Registration Form -->
      <div v-else>
        <h2>Create an Account</h2>
        <form @submit.prevent="handleRegister">
          <div class="form-group">
            <label for="reg-username">Username</label>
            <input
              type="text"
              id="reg-username"
              v-model="registerData.username"
              placeholder="Choose a username"
              required
              :class="{'input-error': formErrors.username}"
            />
            <p v-if="formErrors.username" class="error-text">{{ formErrors.username }}</p>
          </div>
          <div class="form-group">
            <label for="reg-email">Email</label>
            <input
              type="email"
              id="reg-email"
              v-model="registerData.email"
              placeholder="Enter your email"
              required
              :class="{'input-error': formErrors.email}"
            />
            <p v-if="formErrors.email" class="error-text">{{ formErrors.email }}</p>
          </div>
          <div class="form-group">
            <label for="reg-password">Password</label>
            <input
              type="password"
              id="reg-password"
              v-model="registerData.password"
              placeholder="Create a password"
              required
              :class="{'input-error': formErrors.password}"
            />
            <p v-if="formErrors.password" class="error-text">{{ formErrors.password }}</p>
          </div>
          <div class="form-group">
            <label for="reg-firstname">First Name (Optional)</label>
            <input
              type="text"
              id="reg-firstname"
              v-model="registerData.first_name"
              placeholder="Enter your first name"
            />
          </div>
          <div class="form-group">
            <label for="reg-lastname">Last Name (Optional)</label>
            <input
              type="text"
              id="reg-lastname"
              v-model="registerData.last_name"
              placeholder="Enter your last name"
            />
          </div>
          <button type="submit" class="login-button" :disabled="loading">
            {{ loading ? 'Registering...' : 'Register' }}
          </button>
        </form>
        <div class="login-footer">
          <p>Already have an account? <a href="#" @click.prevent="toggleRegister">Login</a></p>
        </div>
      </div>

      <!-- Success Message -->
      <div v-if="successMessage" class="success-message">
        <svg width="20" height="20" fill="none" stroke="#10B981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24">
          <path d="M22 11.08V12a10 10 0 11-5.93-9.14"></path>
          <path d="M22 4L12 14.01l-3-3"></path>
        </svg>
        {{ successMessage }}
      </div>

      <!-- Error Message -->
      <div v-if="errorMessage" class="error-message">
        <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="12" y1="8" x2="12" y2="12"></line>
          <line x1="12" y1="16" x2="12.01" y2="16"></line>
        </svg>
        {{ errorMessage }}
      </div>
    </div>
  </div>
</template>

<script>
export default {
  layout: 'dashboard',
  data() {
    return {
      showModal: false,
      showRegister: false,
      loading: false,
      successMessage: '',
      errorMessage: '',
      formErrors: {},
      loginData: {
        username: '',
        password: ''
      },
      registerData: {
        username: '',
        email: '',
        password: '',
        first_name: '',
        last_name: ''
      }
    }
  },
  methods: {
    openModal() {
      this.showModal = true
    },
    closeModal() {
      this.showModal = false
      this.resetForms()
    },
    toggleRegister() {
      this.showRegister = !this.showRegister
      this.errorMessage = ''
      this.successMessage = ''
      this.formErrors = {}
    },
    resetForms() {
      this.loginData = {
        username: '',
        password: ''
      }
      this.registerData = {
        username: '',
        email: '',
        password: '',
        first_name: '',
        last_name: ''
      }
      this.errorMessage = ''
      this.successMessage = ''
      this.formErrors = {}
      this.showRegister = false
    },
    validateLoginForm() {
      this.formErrors = {}
      let valid = true

      if (!this.loginData.username.trim()) {
        this.formErrors.username = 'Username is required'
        valid = false
      }

      if (!this.loginData.password) {
        this.formErrors.password = 'Password is required'
        valid = false
      }

      return valid
    },
    validateRegisterForm() {
      this.formErrors = {}
      let valid = true

      if (!this.registerData.username.trim()) {
        this.formErrors.username = 'Username is required'
        valid = false
      }

      if (!this.registerData.email.trim()) {
        this.formErrors.email = 'Email is required'
        valid = false
      } else if (!/^\S+@\S+\.\S+$/.test(this.registerData.email)) {
        this.formErrors.email = 'Please enter a valid email'
        valid = false
      }

      if (!this.registerData.password) {
        this.formErrors.password = 'Password is required'
        valid = false
      } else if (this.registerData.password.length < 6) {
        this.formErrors.password = 'Password must be at least 6 characters'
        valid = false
      }

      return valid
    },
    async handleLogin() {
      if (!this.validateLoginForm()) return

      this.loading = true
      this.errorMessage = ''
      this.successMessage = ''

      try {
        const response = await this.$client.post('teople1/users/login/', {
          username: this.loginData.username,
          password: this.loginData.password
        })

        if (response.data && response.data.status === 'success') {
          // Handle successful login
          this.isLoggedIn = true
          this.closeModal()
          this.$emit('login-success', response.data.user)
        } else {
          this.errorMessage = response.data?.message || 'Login failed'
        }
      } catch (error) {
        console.error('Login error:', error)

        if (error.response) {
          if (error.response.data?.errors) {
            this.formErrors = { ...this.formErrors, ...error.response.data.errors }
          }
          this.errorMessage = error.response.data?.message || 'Login failed'
        } else {
          this.errorMessage = 'Network error. Please try again.'
        }
      } finally {
        this.loading = false
      }
    },
    async handleRegister() {
      if (!this.validateRegisterForm()) return

      this.loading = true
      this.errorMessage = ''
      this.successMessage = ''

      try {
        const response = await this.$client.post('teople1/users/register/', {
          username: this.registerData.username,
          email: this.registerData.email,
          password: this.registerData.password,
          first_name: this.registerData.first_name,
          last_name: this.registerData.last_name
        })

        if (response.data && response.data.status === 'success') {
          // Show success message and switch to login form
          this.successMessage = 'Registration successful! Please login.'
          this.resetRegisterForm()
          this.showRegister = false

          // Auto-fill login form with registered credentials
          this.loginData.username = this.registerData.username
        } else {
          this.errorMessage = response.data?.message || 'Registration failed'
        }
      } catch (error) {
        console.error('Registration error:', error)

        if (error.response) {
          if (error.response.data?.errors) {
            this.formErrors = { ...this.formErrors, ...error.response.data.errors }
          }
          this.errorMessage = error.response.data?.message || 'Registration failed'
        } else {
          this.errorMessage = 'Network error. Please try again.'
        }
      } finally {
        this.loading = false
      }
    },
    resetRegisterForm() {
      this.registerData = {
        username: '',
        email: '',
        password: '',
        first_name: '',
        last_name: ''
      }
      this.formErrors = {}
    }
  }
}
</script>

<style scoped>
/* Reusing styles from your task management component */
.login-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
}

.modal-content {
  position: relative;
  background: white;
  padding: 30px;
  border-radius: 10px;
  width: 100%;
  max-width: 400px;
  z-index: 1001;
  box-shadow: 0 5px 20px rgba(0, 0, 0, 0.2);
}

.close-button {
  position: absolute;
  top: 15px;
  right: 15px;
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: #7f8c8d;
}

h2 {
  margin-top: 0;
  margin-bottom: 20px;
  color: #2c3e50;
  font-size: 1.5rem;
  font-weight: 600;
}

.form-group {
  margin-bottom: 20px;
}

label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #2c3e50;
  font-size: 0.875rem;
}

input {
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 5px;
  font-size: 16px;
}

.input-error {
  border-color: #fca5a5;
}

.error-text {
  margin-top: 0.25rem;
  font-size: 0.75rem;
  color: #ef4444;
}

.login-button {
  width: 100%;
  padding: 12px;
  background: linear-gradient(135deg, #3498db, #2980b9);
  color: white;
  border: none;
  border-radius: 5px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.login-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(52, 152, 219, 0.3);
}

.login-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.login-footer {
  margin-top: 20px;
  text-align: center;
  font-size: 14px;
  color: #6b7280;
}

.login-footer a {
  color: #3498db;
  text-decoration: none;
  cursor: pointer;
  font-weight: 500;
}

.success-message {
  margin-top: 20px;
  padding: 12px;
  background-color: #ECFDF5;
  color: #065F46;
  border-radius: 5px;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
}

.error-message {
  margin-top: 20px;
  padding: 12px;
  background-color: #FEF2F2;
  color: #B91C1C;
  border-radius: 5px;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
}
</style>