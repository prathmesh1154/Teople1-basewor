<template>
  <div class="dashboard">
    <!-- Page Header -->
    <h2 class="text-2xl font-bold mb-6">Welcome, Admin 👋</h2>

    <!-- Summary Cards -->
    <div class="cards-row">
      <div class="card-box blue">
        <h3>Total Users</h3>
        <p>120</p>
      </div>
      <div class="card-box green">
        <h3>Tasks Completed</h3>
        <p>42</p>
      </div>
      <div class="card-box yellow">
        <h3>Revenue</h3>
        <p>$14,300</p>
      </div>
    </div>

    <!-- To-Do Form -->
    <div class="todo-form">
      <input
        v-model="newTask"
        type="text"
        placeholder="Enter a new task..."
        class="input"
      />
      <button @click="addTask" class="add-btn">Add Task</button>
    </div>

    <!-- To-Do Table -->
    <div class="todo-table">
      <h3 class="table-title">Task List</h3>
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Task</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="tasks.length === 0">
            <td colspan="4" class="empty">No tasks found.</td>
          </tr>
          <tr v-for="(task, index) in tasks" :key="index">
            <td>{{ index + 1 }}</td>
            <td :class="{ done: task.done }">{{ task.text }}</td>
            <td>
              <span :class="task.done ? 'badge-done' : 'badge-pending'">
                {{ task.done ? 'Completed' : 'Pending' }}
              </span>
            </td>
            <td>
              <button @click="toggleDone(index)" class="btn small success">
                ✅
              </button>
              <button @click="removeTask(index)" class="btn small danger">
                ❌
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
export default {
  layout: 'dashboard',
  data() {
    return {
      newTask: '',
      tasks: [
        { text: 'Prepare meeting notes', done: false },
        { text: 'Email to John', done: true },
      ],
    }
  },
  methods: {
    addTask() {
      if (this.newTask.trim()) {
        this.tasks.push({ text: this.newTask, done: false })
        this.newTask = ''
      }
    },
    toggleDone(index) {
      this.tasks[index].done = !this.tasks[index].done
    },
    removeTask(index) {
      this.tasks.splice(index, 1)
    },
  },
}
</script>

<style scoped>
.dashboard {
  max-width: 1200px;
  margin: auto;
  padding-bottom: 40px;
}

/* Cards */
.cards-row {
  display: flex;
  gap: 20px;
  margin-bottom: 40px;
}

.card-box {
  flex: 1;
  border-radius: 10px;
  padding: 20px;
  color: white;
  font-size: 1.2rem;
  text-align: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.card-box h3 {
  font-size: 1rem;
  margin-bottom: 10px;
  font-weight: 500;
}

.card-box p {
  font-size: 2rem;
  font-weight: bold;
}

.card-box.blue {
  background: #4299e1;
}
.card-box.green {
  background: #48bb78;
}
.card-box.yellow {
  background: #ecc94b;
}

/* To-Do Form */
.todo-form {
  display: flex;
  margin-bottom: 30px;
}

.input {
  flex: 1;
  padding: 12px 16px;
  font-size: 1rem;
  border: 1px solid #ccc;
  border-radius: 8px 0 0 8px;
}

.add-btn {
  background-color: #2d3748;
  color: white;
  padding: 12px 24px;
  border: none;
  font-weight: bold;
  border-radius: 0 8px 8px 0;
  cursor: pointer;
}

/* Table */
.todo-table {
  background: white;
  padding: 20px;
  border-radius: 10px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  overflow-x: auto;
}

.table-title {
  font-size: 1.2rem;
  font-weight: 600;
  margin-bottom: 20px;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th {
  background: #f5f5f5;
  padding: 12px;
  text-align: left;
}

td {
  padding: 12px;
  border-bottom: 1px solid #e2e8f0;
}

.done {
  text-decoration: line-through;
  color: gray;
}

.badge-done {
  background-color: #48bb78;
  color: white;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 0.85rem;
}

.badge-pending {
  background-color: #ed8936;
  color: white;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 0.85rem;
}

.btn.small {
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 0.85rem;
  border: none;
  cursor: pointer;
  margin-right: 5px;
}

.btn.success {
    background-color: #fff;
  border:1px solid green;
  color: white;
}
.btn.danger {
  background-color: #fff;
  border:1px solid red;
  color: white;
}

.empty {
  text-align: center;
  padding: 20px;
  font-style: italic;
  color: gray;
}
</style>
