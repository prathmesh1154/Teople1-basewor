<template>
  <div class="dashboard-page">
    <div class="table-header">
      <div>
        <h1 class="table-title">Task Management</h1>
        <p class="table-subtitle">Manage your tasks efficiently</p>
      </div>
      <div class="table-actions">
        <button @click="refreshTasks" class="refresh-btn" :disabled="loading">
          <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24">
            <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"/>
          </svg>
          <span v-if="!loading">Refresh</span>
          <span v-else>Loading...</span>
        </button>
        <button @click="openCreateModal" class="action-btn btn-primary">
          <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24">
            <line x1="12" y1="5" x2="12" y2="19"/>
            <line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
          New Task
        </button>
      </div>
    </div>

    <div v-if="error" class="error-message">
      <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24">
        <circle cx="12" cy="12" r="10"></circle>
        <line x1="12" y1="8" x2="12" y2="12"></line>
        <line x1="12" y1="16" x2="12.01" y2="16"></line>
      </svg>
      {{ error }}
    </div>

    <div class="table-container">
      <div class="table-responsive">
        <table class="tasks-table">
          <thead>
            <tr>
              <th>Title</th>
              <th>Description</th>
              <th>Status</th>
              <th>Due Date</th>
              <th>Priority</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading">
              <td colspan="6" class="loading-state">
                <svg class="animate-spin h-5 w-5 text-gray-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span>Loading tasks...</span>
              </td>
            </tr>
            <tr v-else-if="tasks.length === 0">
              <td colspan="6" class="empty-state">
                <svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                </svg>
                <div>
                  <h3>No tasks found</h3>
                  <p>Create your first task to get started</p>
                </div>
                <button @click="openCreateModal" class="action-btn btn-primary">
                  Create Task
                </button>
              </td>
            </tr>
            <tr v-for="task in tasks" :key="task.id">
              <td>
                <div class="task-title">
                  <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24">
                    <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path>
                  </svg>
                  {{ task.task_name || 'Untitled' }}
                </div>
              </td>
              <td>
                <div class="task-description">
                  {{ task.description || 'No description' }}
                </div>
              </td>
              <td><span :class="['status-badge', getStatusClass(task.status)]">{{ task.status || 'Not Set' }}</span></td>
              <td>
                <div class="due-date">
                  <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24">
                    <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                    <line x1="16" y1="2" x2="16" y2="6"></line>
                    <line x1="8" y1="2" x2="8" y2="6"></line>
                    <line x1="3" y1="10" x2="21" y2="10"></line>
                  </svg>
                  {{ formatDate(task.due_date) }}
                </div>
              </td>
              <td><span class="priority-badge" :class="`priority-${task.priority}`">{{ getPriorityLabel(task.priority) }}</span></td>
              <td>
                <div class="flex space-x-2">
                  <button @click="editTask(task)" class="action-btn btn-edit" title="Edit">
                    <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24">
                      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                    </svg>
                  </button>
                  <button @click="confirmDelete(task)" class="action-btn btn-delete" title="Delete">
                    <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24">
                      <polyline points="3 6 5 6 21 6"></polyline>
                      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                    </svg>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Edit Task Modal -->
    <div v-if="editingTask" class="modal-overlay">
      <div class="modal-container">
        <div class="modal-header">
          <h3 class="modal-title">Edit Task</h3>
          <button @click="cancelEdit" class="modal-close-btn">
            <svg class="h-6 w-6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24">
              <path d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>

        <div class="modal-content">
          <div class="form-group">
            <label class="form-label">Task Name <span class="required">*</span></label>
            <input type="text" v-model="editingTask.task_name"
              :class="{'input-error': editFormErrors.task_name}"
              class="form-input" placeholder="Enter task name" />
            <p v-if="editFormErrors.task_name" class="error-text">{{ editFormErrors.task_name }}</p>
          </div>

          <div class="form-group">
            <label class="form-label">Description</label>
            <textarea rows="3" v-model="editingTask.description"
              class="form-input" placeholder="Enter task description"></textarea>
          </div>

          <div class="form-group">
            <label class="form-label">Due Date <span class="required">*</span></label>
            <input type="date" v-model="editingTask.due_date"
              :class="{'input-error': editFormErrors.due_date}"
              class="form-input" />
            <p v-if="editFormErrors.due_date" class="error-text">{{ editFormErrors.due_date }}</p>
          </div>

          <div class="form-group">
            <label class="form-label">Status <span class="required">*</span></label>
            <select v-model="editingTask.status"
              :class="{'input-error': editFormErrors.status}"
              class="form-input">
              <option>Not Started</option>
              <option>In Progress</option>
              <option>Completed</option>
            </select>
            <p v-if="editFormErrors.status" class="error-text">{{ editFormErrors.status }}</p>
          </div>

          <div class="form-group">
            <label class="form-label">Priority</label>
            <div class="priority-selector">
              <button @click="editingTask.priority = '1'" :class="{'priority-active': editingTask.priority === '1'}" class="priority-option priority-low">
                Low
              </button>
              <button @click="editingTask.priority = '2'" :class="{'priority-active': editingTask.priority === '2'}" class="priority-option priority-medium">
                Medium
              </button>
              <button @click="editingTask.priority = '3'" :class="{'priority-active': editingTask.priority === '3'}" class="priority-option priority-high">
                High
              </button>
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <button @click="cancelEdit" class="btn-secondary" :disabled="isUpdating">
            Cancel
          </button>
          <button @click="updateTask" class="btn-primary" :disabled="isUpdating">
            <svg v-if="isUpdating" class="w-4 h-4 mr-2 animate-spin" fill="none" stroke="currentColor" stroke-width="4" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            {{ isUpdating ? 'Updating...' : 'Update Task' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Create Task Modal -->
    <div v-if="showCreateModal" class="modal-overlay">
      <div class="modal-container">
        <div class="modal-header">
          <h3 class="modal-title">Create New Task</h3>
          <button @click="closeCreateModal" class="modal-close-btn">
            <svg class="h-6 w-6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24">
              <path d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>

        <div class="modal-content">
          <div class="form-group">
            <label class="form-label">Task Name <span class="required">*</span></label>
            <input type="text" v-model="newTask.task_name"
              :class="{'input-error': formErrors.task_name}"
              class="form-input" placeholder="Enter task name" />
            <p v-if="formErrors.task_name" class="error-text">{{ formErrors.task_name }}</p>
          </div>

          <div class="form-group">
            <label class="form-label">Description</label>
            <textarea rows="3" v-model="newTask.description"
              class="form-input" placeholder="Enter task description"></textarea>
          </div>

          <div class="form-group">
            <label class="form-label">Due Date <span class="required">*</span></label>
            <input type="date" v-model="newTask.due_date"
              :class="{'input-error': formErrors.due_date}"
              class="form-input" />
            <p v-if="formErrors.due_date" class="error-text">{{ formErrors.due_date }}</p>
          </div>

          <div class="form-group">
            <label class="form-label">Status <span class="required">*</span></label>
            <select v-model="newTask.status"
              :class="{'input-error': formErrors.status}"
              class="form-input">
              <option>Not Started</option>
              <option>In Progress</option>
              <option>Completed</option>
            </select>
            <p v-if="formErrors.status" class="error-text">{{ formErrors.status }}</p>
          </div>

          <div class="form-group">
            <label class="form-label">Priority</label>
            <div class="priority-selector">
              <button @click="newTask.priority = '1'" :class="{'priority-active': newTask.priority === '1'}" class="priority-option priority-low">
                Low
              </button>
              <button @click="newTask.priority = '2'" :class="{'priority-active': newTask.priority === '2'}" class="priority-option priority-medium">
                Medium
              </button>
              <button @click="newTask.priority = '3'" :class="{'priority-active': newTask.priority === '3'}" class="priority-option priority-high">
                High
              </button>
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <button @click="closeCreateModal" class="btn-secondary" :disabled="isCreating">
            Cancel
          </button>
          <button @click="createTask" class="btn-primary" :disabled="isCreating">
            <svg v-if="isCreating" class="w-4 h-4 mr-2 animate-spin" fill="none" stroke="currentColor" stroke-width="4" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            {{ isCreating ? 'Creating...' : 'Create Task' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <div v-if="taskToDelete" class="modal-overlay">
      <div class="modal-container">
        <div class="modal-header">
          <h3 class="modal-title">Confirm Deletion</h3>
          <button @click="cancelDelete" class="modal-close-btn">
            <svg class="h-6 w-6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24">
              <path d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>

        <div class="modal-content">
          <div class="delete-warning">
            <svg width="48" height="48" fill="none" stroke="#ef4444" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="12" y1="8" x2="12" y2="12"></line>
              <line x1="12" y1="16" x2="12.01" y2="16"></line>
            </svg>
            <p>Are you sure you want to delete the task <strong>"{{ taskToDelete.task_name }}"</strong>? This action cannot be undone.</p>
          </div>
        </div>

        <div class="modal-footer">
          <button @click="cancelDelete" class="btn-secondary" :disabled="isDeleting">
            Cancel
          </button>
          <button @click="deleteTask" class="btn-danger" :disabled="isDeleting">
            <svg v-if="isDeleting" class="w-4 h-4 mr-2 animate-spin" fill="none" stroke="currentColor" stroke-width="4" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            {{ isDeleting ? 'Deleting...' : 'Delete' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  layout: 'dashboard',
  data() {
    return {
      tasks: [],
      loading: false,
      error: null,

      editingTask: null,
      isUpdating: false,
      editFormErrors: {},

      showCreateModal: false,
      isCreating: false,
      newTask: {
        task_name: '',
        description: '',
        due_date: '',
        status: 'Not Started',
        priority: '2'
      },
      formErrors: {},

      taskToDelete: null,
      isDeleting: false,
    }
  },

  async asyncData({ app }) {
    try {
      const response = await app.$client.get('teople1/tasks/')
      return { tasks: response.data.tasks || [], loading: false, error: null }
    } catch (e) {
      return { tasks: [], loading: false, error: 'Failed to load tasks. Please try again.' }
    }
  },

  methods: {
    async fetchTasks() {
      this.loading = true
      this.error = null
      try {
        const response = await this.$client.get('teople1/tasks/')
        this.tasks = response.data.tasks || []
      } catch (e) {
        this.error = 'Failed to load tasks. Please try again.'
      } finally {
        this.loading = false
      }
    },

    async refreshTasks() {
      await this.fetchTasks()
    },

    formatDate(dateString) {
      if (!dateString) return 'N/A'
      const options = { year: 'numeric', month: 'short', day: 'numeric' }
      return new Date(dateString).toLocaleDateString(undefined, options)
    },

    getStatusClass(status) {
      switch (status) {
        case 'Completed': return 'status-completed'
        case 'In Progress': return 'status-in-progress'
        default: return 'status-not-started'
      }
    },

    getPriorityLabel(priority) {
      switch (priority) {
        case 1:
        case '1': return 'Low'
        case 2:
        case '2': return 'Medium'
        case 3:
        case '3': return 'High'
        default: return 'N/A'
      }
    },

    // Create Task
    openCreateModal() {
      this.showCreateModal = true
    },

    closeCreateModal() {
      this.showCreateModal = false
      this.resetNewTask()
      this.formErrors = {}
    },

    resetNewTask() {
      this.newTask = {
        task_name: '',
        description: '',
        due_date: '',
        status: 'Not Started',
        priority: '2'
      }
    },

    validateTaskForm() {
      this.formErrors = {}
      let valid = true
      if (!this.newTask.task_name.trim()) {
        this.formErrors.task_name = 'Task name is required'
        valid = false
      }
      if (!this.newTask.due_date) {
        this.formErrors.due_date = 'Due date is required'
        valid = false
      }
      if (!this.newTask.status) {
        this.formErrors.status = 'Status is required'
        valid = false
      }
      return valid
    },

    async createTask() {
      if (!this.validateTaskForm()) return
      this.isCreating = true
      this.error = null
      try {
        const taskData = {
          task_name: this.newTask.task_name,
          description: this.newTask.description,
          due_date: this.newTask.due_date,
          status: this.newTask.status,
          priority: parseInt(this.newTask.priority)
        }
        const response = await this.$client.post('teople1/tasks/', taskData)
        if (response.data && response.data.task) this.tasks.unshift(response.data.task)
        this.closeCreateModal()
      } catch (e) {
        this.error = e.response?.data?.error || e.response?.data?.message || 'Failed to create task'
        if (e.response?.data?.errors) this.formErrors = { ...this.formErrors, ...e.response.data.errors }
      } finally {
        this.isCreating = false
      }
    },

    // Edit Task
    editTask(task) {
      this.editingTask = JSON.parse(JSON.stringify(task))
      this.editFormErrors = {}
    },

    cancelEdit() {
      this.editingTask = null
      this.editFormErrors = {}
    },

    validateEditForm() {
      this.editFormErrors = {}
      let valid = true
      if (!this.editingTask.task_name?.trim()) {
        this.editFormErrors.task_name = 'Task name is required'
        valid = false
      }
      if (!this.editingTask.due_date) {
        this.editFormErrors.due_date = 'Due date is required'
        valid = false
      }
      if (!this.editingTask.status) {
        this.editFormErrors.status = 'Status is required'
        valid = false
      }
      return valid
    },

    async updateTask() {
      if (!this.validateEditForm()) return
      this.isUpdating = true
      this.error = null
      try {
        const taskData = {
          task_name: this.editingTask.task_name,
          description: this.editingTask.description,
          due_date: this.editingTask.due_date,
          status: this.editingTask.status,
          priority: parseInt(this.editingTask.priority)
        }
        const response = await this.$client.put(`teople1/tasks/${this.editingTask.id}/`, taskData)
        if (response.data && response.data.task) {
          const idx = this.tasks.findIndex(t => t.id === this.editingTask.id)
          if (idx !== -1) this.tasks.splice(idx, 1, response.data.task)
        }
        this.editingTask = null
      } catch (e) {
        this.error = e.response?.data?.error || e.response?.data?.message || 'Failed to update task'
        if (e.response?.data?.errors) this.editFormErrors = { ...this.editFormErrors, ...e.response.data.errors }
      } finally {
        this.isUpdating = false
      }
    },

    // Delete Task
    confirmDelete(task) {
      this.taskToDelete = task
    },

    cancelDelete() {
      this.taskToDelete = null
      this.isDeleting = false
    },

    async deleteTask() {
      if (!this.taskToDelete) return
      this.isDeleting = true
      this.error = null
      try {
        await this.$client.delete(`teople1/tasks/${this.taskToDelete.id}/`)
        const idx = this.tasks.findIndex(t => t.id === this.taskToDelete.id)
        if (idx !== -1) this.tasks.splice(idx, 1)
        this.taskToDelete = null
      } catch (e) {
        this.error = e.response?.data?.error || e.response?.data?.message || 'Failed to delete task'
      } finally {
        this.isDeleting = false
      }
    }
  }
}
</script>

<style scoped>
/* Base Styles */
.dashboard-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
  color: #1f2937;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Header Styles */
.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.table-title {
  font-size: 1.75rem;
  font-weight: 700;
  color: #111827;
  margin-bottom: 0.25rem;
}

.table-subtitle {
  font-size: 0.875rem;
  color: #6b7280;
}

.table-actions {
  display: flex;
  gap: 1rem;
  align-items: center;
}

/* Button Styles */
.action-btn {
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  font-weight: 500;
  font-size: 0.875rem;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  border: none;
  cursor: pointer;
}

.action-btn:hover {
  transform: translateY(-1px);
}

.action-btn:active {
  transform: translateY(0);
}

.btn-primary {
  background-color: #3b82f6;
  color: white;
}

.btn-primary:hover {
  background-color: #2563eb;
}

.btn-secondary {
  background-color: white;
  color: #374151;
  border: 1px solid #d1d5db;
}

.btn-secondary:hover {
  background-color: #f9fafb;
}

.btn-danger {
  background-color: #ef4444;
  color: white;
}

.btn-danger:hover {
  background-color: #dc2626;
}

.btn-edit {
  background-color: #e0f2fe;
  color: #0369a1;
  padding: 0.5rem;
  border-radius: 0.375rem;
}

.btn-edit:hover {
  background-color: #bae6fd;
}

.btn-delete {
  background-color: #fee2e2;
  color: #b91c1c;
  padding: 0.5rem;
  border-radius: 0.375rem;
}

.btn-delete:hover {
  background-color: #fecaca;
}

.refresh-btn {
  padding: 0.5rem 1rem;
  background-color: #f3f4f6;
  border-radius: 0.5rem;
  font-weight: 500;
  color: #374151;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: background-color 0.2s ease;
  border: none;
  cursor: pointer;
}

.refresh-btn:hover {
  background-color: #e5e7eb;
}

.refresh-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

/* Table Styles */
.table-container {
  background: white;
  border-radius: 0.75rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.table-responsive {
  overflow-x: auto;
}

.tasks-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  min-width: 800px;
}

.tasks-table thead th {
  background-color: #f9fafb;
  color: #6b7280;
  font-weight: 600;
  text-transform: uppercase;
  font-size: 0.75rem;
  letter-spacing: 0.05em;
  text-align: left;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #e5e7eb;
}

.tasks-table tbody tr {
  transition: background-color 0.15s ease;
}

.tasks-table tbody tr:hover {
  background-color: #f9fafb;
}

.tasks-table tbody td {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #e5e7eb;
  font-size: 0.875rem;
  color: #374151;
}

.tasks-table tbody tr:last-child td {
  border-bottom: none;
}

/* Status Badges */
.status-badge {
  display: inline-flex;
  align-items: center;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
  line-height: 1.25rem;
}

.status-not-started {
  background-color: #f3f4f6;
  color: #374151;
}

.status-in-progress {
  background-color: #dbeafe;
  color: #1e40af;
}

.status-completed {
  background-color: #dcfce7;
  color: #166534;
}

/* Priority Badges */
.priority-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
}

.priority-1 {
  background-color: #ecfdf5;
  color: #059669;
}

.priority-2 {
  background-color: #fef3c7;
  color: #b45309;
}

.priority-3 {
  background-color: #fee2e2;
  color: #b91c1c;
}

/* Task Content Styles */
.task-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 500;
  color: #111827;
}

.task-description {
  color: #6b7280;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

.due-date {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

/* Loading & Empty States */
.loading-state {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 0.75rem;
  padding: 2rem;
  color: #6b7280;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  padding: 3rem 1rem;
  color: #6b7280;
  text-align: center;
}

.empty-state h3 {
  font-weight: 600;
  color: #111827;
  margin-bottom: 0.25rem;
}

.empty-state p {
  color: #6b7280;
  margin-bottom: 1rem;
}

/* Error Message */
.error-message {
  background-color: #fef2f2;
  color: #b91c1c;
  padding: 1rem;
  border-radius: 0.5rem;
  margin-bottom: 1.5rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-weight: 500;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  background-color: rgba(0, 0, 0, 0.5);
}

.modal-container {
  position: relative;
  width: 100%;
  max-width: 28rem;
  background-color: white;
  border-radius: 0.75rem;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.modal-header {
  padding: 1.5rem;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #111827;
}

.modal-close-btn {
  color: #9ca3af;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 0.25rem;
}

.modal-close-btn:hover {
  color: #6b7280;
  background-color: #f3f4f6;
}

.modal-content {
  padding: 1.5rem;
}

.modal-footer {
  padding: 1.25rem 1.5rem;
  border-top: 1px solid #e5e7eb;
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  background-color: #f9fafb;
}

/* Form Styles */
.form-group {
  margin-bottom: 1.25rem;
}

.form-label {
  display: block;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
}

.required {
  color: #ef4444;
}

.form-input {
  display: block;
  width: 100%;
  padding: 0.625rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  color: #374151;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.form-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.input-error {
  border-color: #fca5a5;
}

.input-error:focus {
  border-color: #fca5a5;
  box-shadow: 0 0 0 3px rgba(248, 113, 113, 0.1);
}

.error-text {
  margin-top: 0.25rem;
  font-size: 0.75rem;
  color: #ef4444;
}

/* Priority Selector */
.priority-selector {
  display: flex;
  gap: 0.5rem;
}

.priority-option {
  flex: 1;
  padding: 0.5rem;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  border: 1px solid #e5e7eb;
  background-color: white;
  transition: all 0.2s ease;
}

.priority-option:hover {
  transform: translateY(-1px);
}

.priority-active {
  color: white;
  border-color: transparent;
}

.priority-low.priority-active {
  background-color: #10b981;
}

.priority-medium.priority-active {
  background-color: #f59e0b;
}

.priority-high.priority-active {
  background-color: #ef4444;
}

/* Delete Warning */
.delete-warning {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 1rem;
  padding: 1rem 0;
}

.delete-warning p {
  color: #6b7280;
  line-height: 1.5;
}

.delete-warning strong {
  color: #111827;
  font-weight: 600;
}

/* Animations */
@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.animate-spin {
  animation: spin 1s linear infinite;
}

/* Responsive Adjustments */
@media (max-width: 768px) {
  .dashboard-page {
    padding: 1rem;
  }

  .table-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }

  .modal-container {
    max-width: 95%;
  }
}
</style>