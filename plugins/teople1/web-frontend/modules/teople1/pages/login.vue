<template>
  <div class="form-container">
    <h1>Login</h1>
    <form @submit.prevent="submitForm">
      <div>
        <label for="username">Username:</label>
        <input id="username" v-model="form.username" type="text" required />
      </div>
      <div>
        <label for="password">Password:</label>
        <input id="password" v-model="form.password" type="text" required />
      </div>
      <button type="submit">Submit</button>
    </form>

    <div v-if="response">
      <h2>Server Response:</h2>
      <pre>{{ response }}</pre>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      form: {
        username: '',
        password: ''
      },
      response: null
    }
  },
  methods: {
    async submitForm() {
      try {
        const res = await this.$client.post('teople1/custom-login/', this.form)
        this.response = res.data
      } catch (err) {
        console.error('POST error:', err)
        this.response = { error: 'Submission failed' }
      }
    }
  }
}
</script>

<style scoped>
.form-container {
  max-width: 500px;
  margin: 0 auto;
  padding: 1rem;
}
form div {
  margin-bottom: 1rem;
}
label {
  display: block;
  margin-bottom: 0.5rem;
}
input {
  width: 100%;
  padding: 0.5rem;
}
button {
  padding: 0.5rem 1rem;
}
</style>