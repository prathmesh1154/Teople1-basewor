<template>
  <div> example!
  Your plugin is working
  </div>
</template>

<script>
export default {
  async asyncData({ app }) {
    const response = await app.$client.get(
      'teople1/example/'
    )
    return response.data
  },
  head() {
    return {
      title: this.title,
    }
  },
}
</script>
