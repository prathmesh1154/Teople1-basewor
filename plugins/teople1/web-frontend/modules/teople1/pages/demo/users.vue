<template>
  <div class="users-page">
    <h1 class="title">Users Table</h1>

    <!-- Search Filter -->
    <div class="search-bar">
      <input
        v-model="searchQuery"
        type="text"
        placeholder="Search by name or email"
        class="search-input"
      />
      <span class="search-icon">🔍</span>
    </div>

    <!-- Table -->
    <div class="table-container">
      <table class="users-table">
        <thead>
          <tr>
            <th>#</th>
            <th @click="sortBy('name')" :class="{ active: sortKey === 'name' }">
              Name
              <span class="sort-icon" v-if="sortKey === 'name'">
                {{ sortDirection === 'asc' ? '↑' : '↓' }}
              </span>
            </th>
            <th @click="sortBy('email')" :class="{ active: sortKey === 'email' }">
              Email
              <span class="sort-icon" v-if="sortKey === 'email'">
                {{ sortDirection === 'asc' ? '↑' : '↓' }}
              </span>
            </th>
            <th>Role</th>
            <th @click="sortBy('credit')" :class="{ active: sortKey === 'credit' }">
              Credit
              <span class="sort-icon" v-if="sortKey === 'credit'">
                {{ sortDirection === 'asc' ? '↑' : '↓' }}
              </span>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(user, index) in paginatedUsers" :key="user.id">
            <td>{{ index + 1 + (currentPage - 1) * itemsPerPage }}</td>
            <td>{{ user.name }}</td>
            <td>{{ user.email }}</td>
            <td>
              <span :class="['role-badge', user.role.toLowerCase()]">
                {{ user.role }}
              </span>
            </td>
            <td>${{ user.credit.toFixed(2) }}</td>
          </tr>
          <tr v-if="paginatedUsers.length === 0">
            <td colspan="5" class="no-results">No users found</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Enhanced Pagination -->
    <div class="pagination">
      <button
        @click="changePage(1)"
        :disabled="currentPage === 1"
        class="pagination-button"
      >
        <<
      </button>
      <button
        @click="changePage(currentPage - 1)"
        :disabled="currentPage === 1"
        class="pagination-button"
      >
        Previous
      </button>

      <div class="page-numbers">
        <span
          v-for="page in visiblePages"
          :key="page"
          @click="changePage(page)"
          :class="{ active: currentPage === page }"
          class="page-number"
        >
          {{ page }}
        </span>
        <span v-if="showEllipsis">...</span>
      </div>

      <button
        @click="changePage(currentPage + 1)"
        :disabled="currentPage === totalPages"
        class="pagination-button"
      >
        Next
      </button>
      <button
        @click="changePage(totalPages)"
        :disabled="currentPage === totalPages"
        class="pagination-button"
      >
        >>
      </button>
    </div>

    <div class="pagination-info">
      Showing {{ startItem }}-{{ endItem }} of {{ sortedUsers.length }} users
    </div>
  </div>
</template>

<script>
export default {
  layout: 'dashboard',
  data() {
    return {
      users: [
        { id: 1, name: 'Alice Johnson', email: 'alice@example.com', role: 'Admin', credit: 1250.50 },
        { id: 2, name: 'Bob Smith', email: 'bob@example.com', role: 'User', credit: 750.25 },
        { id: 3, name: 'Charlie Brown', email: 'charlie@example.com', role: 'Editor', credit: 3200.75 },
        // Add more dummy data for pagination
        ...Array.from({ length: 40 }, (_, i) => ({
          id: i + 4,
          name: `User ${i + 4}`,
          email: `user${i + 4}@example.com`,
          role: i % 3 === 0 ? 'User' : i % 3 === 1 ? 'Editor' : 'Admin',
          credit: Math.floor(Math.random() * 5000) + Math.random(),
        })),
      ],
      searchQuery: '',
      sortKey: 'name',
      sortDirection: 'asc',
      currentPage: 1,
      itemsPerPage: 10,
      maxVisiblePages: 5,
    };
  },
  computed: {
    filteredUsers() {
      return this.users.filter(
        (user) =>
          user.name.toLowerCase().includes(this.searchQuery.toLowerCase()) ||
          user.email.toLowerCase().includes(this.searchQuery.toLowerCase())
      );
    },
    sortedUsers() {
      if (!this.sortKey) return this.filteredUsers;

      return [...this.filteredUsers].sort((a, b) => {
        const aValue = a[this.sortKey];
        const bValue = b[this.sortKey];

        if (typeof aValue === 'number' && typeof bValue === 'number') {
          return this.sortDirection === 'asc' ? aValue - bValue : bValue - aValue;
        }

        const comparison = String(aValue).localeCompare(String(bValue));
        return this.sortDirection === 'asc' ? comparison : -comparison;
      });
    },
    paginatedUsers() {
      const start = (this.currentPage - 1) * this.itemsPerPage;
      return this.sortedUsers.slice(start, start + this.itemsPerPage);
    },
    totalPages() {
      return Math.ceil(this.sortedUsers.length / this.itemsPerPage);
    },
    startItem() {
      return (this.currentPage - 1) * this.itemsPerPage + 1;
    },
    endItem() {
      const end = this.currentPage * this.itemsPerPage;
      return end > this.sortedUsers.length ? this.sortedUsers.length : end;
    },
    visiblePages() {
      const pages = [];
      let startPage = Math.max(1, this.currentPage - Math.floor(this.maxVisiblePages / 2));
      const endPage = Math.min(this.totalPages, startPage + this.maxVisiblePages - 1);

      if (endPage - startPage + 1 < this.maxVisiblePages) {
        startPage = Math.max(1, endPage - this.maxVisiblePages + 1);
      }

      for (let i = startPage; i <= endPage; i++) {
        pages.push(i);
      }

      return pages;
    },
    showEllipsis() {
      return this.visiblePages[this.visiblePages.length - 1] < this.totalPages;
    }
  },
  methods: {
    changePage(page) {
      if (page >= 1 && page <= this.totalPages) {
        this.currentPage = page;
      }
    },
    sortBy(key) {
      if (this.sortKey === key) {
        this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
      } else {
        this.sortKey = key;
        this.sortDirection = 'asc';
      }
    },
  },
};
</script>

<style scoped>
.users-page {
  padding: 24px;
  background-color: #f8f9fa;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.title {
  font-size: 28px;
  margin-bottom: 20px;
  color: #2c3e50;
  font-weight: 600;
}

.search-bar {
  position: relative;
  margin-bottom: 20px;
  max-width: 400px;
  border:1px solid black;
  border-radius:6px;
}

.search-input {
  width: 100%;
  padding: 10px 15px 10px 35px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  transition: border-color 0.3s;
}

.search-input:focus {
  outline: none;
  border-color: #3498db;
  box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.2);
}

.search-icon {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: #7f8c8d;
}

.table-container {
  overflow-x: auto;
  margin-bottom: 20px;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
}

.users-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 8px;
  overflow: hidden;
}

.users-table th,
.users-table td {
  padding: 14px 16px;
  text-align: left;
  border-bottom: 1px solid #eee;
}

.users-table th {
  background-color: #3498db;
  color: white;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
  position: relative;
}

.users-table th:hover {
  background-color: #2980b9;
}



.sort-icon {
  margin-left: 5px;
  font-size: 12px;
}

.users-table tbody tr:hover {
  background-color: #f5f5f5;
}

.no-results {
  text-align: center;
  color: #7f8c8d;
  padding: 20px;
}

.role-badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.role-badge.admin {
  background-color: #e3f2fd;
  color: #1976d2;
}

.role-badge.user {
  background-color: #e8f5e9;
  color: #388e3c;
}

.role-badge.editor {
  background-color: #fff3e0;
  color: #f57c00;
}

.pagination {
  display: flex;
  justify-content: right;
  align-items: right;
  gap: 8px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.pagination-button {
  padding: 8px 12px;
  background-color: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
  font-size: 14px;
}

.pagination-button:hover:not(:disabled) {
  background-color: #2980b9;
}

.pagination-button:disabled {
  background-color: #bdc3c7;
  cursor: not-allowed;
  opacity: 0.7;
}

.page-numbers {
  display: flex;
  gap: 4px;

}

.page-number {
  padding: 8px 12px;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
  font-size: 14px;
}

.page-number:hover {
  background-color: #e0e0e0;
}

.page-number.active {
  background-color: #3498db;
  color: white;
}

.pagination-info {
  text-align: right;
  color: #7f8c8d;
  font-size: 14px;
}
</style>