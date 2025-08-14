<template>
  <div class="courses-page">
    <div class="header-section">
      <h1 class="page-title">Available Courses</h1>
      <div class="search-filter">
        <input type="text" placeholder="Search courses..." class="search-input" v-model="searchQuery" @input="filterCourses" />
        <select class="filter-select" v-model="filterStatus" @change="filterCourses">
          <option value="all">All Courses</option>
          <option value="in-progress">In Progress</option>
          <option value="completed">Completed</option>
          <option value="not-started">Not Started</option>
        </select>
      </div>
    </div>

    <div class="courses-grid">
      <div
        v-for="course in filteredCourses"
        :key="course.id"
        class="course-card"
      >
        <div class="course-image-container" @click="openCourseDetails(course.id)">
          <img :src="course.image" :alt="course.title" class="course-image" />
          <span class="course-status" :class="statusClass(course.status)">
            {{ course.status }}
          </span>
          <div class="course-category">{{ course.category }}</div>
        </div>

        <div class="course-content">
          <div class="course-meta">
            <span class="course-instructor">
              <i class="fas fa-user"></i> {{ course.instructor }}
            </span>
            <span class="course-lessons">
              <i class="fas fa-book"></i> {{ course.lessons }} Lessons
            </span>
          </div>

          <h2 class="course-title" @click="openCourseDetails(course.id)">{{ course.title }}</h2>

          <div class="course-progress" v-if="course.lessons > 0">
            <div class="progress-info">
              <span class="progress-text">{{ course.progress }}% Complete</span>
            </div>
            <div class="progress-bar-bg">
              <div
                class="progress-bar-fill"
                :style="{ width: course.progress + '%' }"
              ></div>
            </div>
          </div>

          <button
            class="course-action-btn"
            @click.stop="handleCourseAction(course)"
          >
            {{ getButtonText(course) }}
          </button>
        </div>
      </div>
    </div>

    <login-modal
      ref="loginModal"
      @login-success="startCourse(selectedCourseId)"
    />
  </div>
</template>

<script>
import axios from 'axios'
import LoginModal from './courselogin.vue'

export default {
  layout: 'dashboard',
  name: "CoursesPage",
  components: {
    LoginModal
  },
  data() {
    return {
      courses: [],
      filteredCourses: [],
      selectedCourseId: null,
      isLoggedIn: false,
      searchQuery: '',
      filterStatus: 'all',
    };
  },
  created() {
    this.fetchCourses()
  },
  methods: {
    async fetchProgress() {
      try {
        const res = await axios.get('http://localhost/api/teople1/progress/')
        if (res.data.status === 'success') {
          return res.data.progress || []
        }
        return []
      } catch (err) {
        console.error('Error fetching progress:', err)
        return []
      }
    },
    async fetchCourses() {
      try {
        const courseRes = await axios.get('http://localhost/api/teople1/courses/')
        const progressList = await this.fetchProgress()

        if (courseRes.data.status === 'success') {
          const mappedCourses = courseRes.data.courses.map(c => {
            // Find matching progress item by course ID
            let progressItem = progressList.find(p =>
              p.course && p.course.some(co => co.id === c.id)
            )

            // Calculate progress percent based on lessons completed
            let totalLessons = c.Lessons.length || 0
            let completedLessons = progressItem && progressItem.lesson ? progressItem.lesson.length : 0
            let progress = totalLessons ? Math.floor((completedLessons / totalLessons) * 100) : 0

            // Determine status based on progress
            let status = 'Not Started'
            if (progress === 100) {
              status = 'Completed'
            } else if (progress > 0) {
              status = 'In Progress'
            }

            return {
              id: c.id,
              title: c.Title || 'Untitled Course',
              lessons: totalLessons,
              instructor: 'N/A', // API does not provide instructor info
              progress,
              status,
              image: c.image_url || 'https://via.placeholder.com/340x180?text=No+Image',
              category: c.category || '',
            }
          })

          this.courses = mappedCourses
          this.filteredCourses = [...mappedCourses]
        }
      } catch (err) {
        console.error('Error fetching courses:', err)
      }
    },
    openCourseDetails(courseId) {
      this.$router.push({ name: 'course-detail', params: { id: courseId } })
    },
    getButtonText(course) {
      if (course.progress === 0) return 'Start Now'
      if (course.progress === 100) return 'View Certificate'
      return 'Continue'
    },
    handleCourseAction(course) {
      this.selectedCourseId = course.id
      if (course.progress === 100) {
        alert(`View certificate for ${course.title}`)
      } else {
        this.$router.push({
          name: 'course-detail',
          params: { id: course.id }
        })
      }
    },
    startCourse(courseId) {
      this.$router.push({
        name: 'course-learn',
        params: { id: courseId }
      })
    },
    statusClass(status) {
      switch (status.toLowerCase()) {
        case 'completed':
          return 'complete'
        case 'in progress':
          return 'in-progress'
        case 'not started':
        default:
          return 'not-started'
      }
    },
    filterCourses() {
      let filtered = this.courses

      if (this.searchQuery.trim() !== '') {
        const q = this.searchQuery.toLowerCase()
        filtered = filtered.filter(c =>
          c.title.toLowerCase().includes(q) ||
          c.category.toLowerCase().includes(q) ||
          c.instructor.toLowerCase().includes(q)
        )
      }

      if (this.filterStatus !== 'all') {
        // Map filter value to status string
        const statusMap = {
          'in-progress': 'In Progress',
          'completed': 'Completed',
          'not-started': 'Not Started'
        }
        filtered = filtered.filter(c => c.status === statusMap[this.filterStatus])
      }

      this.filteredCourses = filtered
    }
  }
};
</script>

<style scoped>
@import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css');
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

.courses-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 30px 20px;
  font-family: 'Poppins', sans-serif;
  background: #f9fafb;
}

.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 40px;
  flex-wrap: wrap;
  gap: 20px;
}

.page-title {
  font-size: 32px;
  font-weight: 700;
  margin: 0;
  color: #2c3e50;
  position: relative;
  padding-bottom: 10px;
}

.page-title::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 60px;
  height: 4px;
  background: linear-gradient(90deg, #3498db, #2ecc71);
  border-radius: 2px;
}

.search-filter {
  display: flex;
  gap: 15px;
}

.search-input {
  padding: 12px 20px;
  border: 1px solid #e0e0e0;
  border-radius: 30px;
  font-size: 14px;
  width: 250px;
  transition: all 0.3s;
  box-shadow: 0 2px 10px rgba(0,0,0,0.05);
}

.search-input:focus {
  outline: none;
  border-color: #3498db;
  box-shadow: 0 2px 15px rgba(52, 152, 219, 0.2);
}

.filter-select {
  padding: 12px 20px;
  border: 1px solid #e0e0e0;
  border-radius: 30px;
  font-size: 14px;
  background: white;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 2px 10px rgba(0,0,0,0.05);
}

.filter-select:focus {
  outline: none;
  border-color: #3498db;
}

.courses-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 30px;
}

.course-card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.08);
  cursor: pointer;
  transition: all 0.3s ease;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.course-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 15px 35px rgba(0,0,0,0.12);
}

.course-image-container {
  position: relative;
  height: 180px;
  overflow: hidden;
}

.course-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  transition: transform 0.5s ease;
}

.course-card:hover .course-image {
  transform: scale(1.1);
}

.course-status {
  position: absolute;
  top: 15px;
  right: 15px;
  padding: 6px 15px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
  color: white;
}

.course-status.complete {
  background: linear-gradient(135deg, #2ecc71, #27ae60);
}

.course-status.in-progress {
  background: linear-gradient(135deg, #f39c12, #e67e22);
}

.course-status.not-started {
  background: linear-gradient(135deg, #95a5a6, #7f8c8d);
}

.course-category {
  position: absolute;
  bottom: 15px;
  left: 15px;
  background: rgba(0,0,0,0.7);
  color: white;
  padding: 5px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}

.course-content {
  padding: 20px;
  flex-grow: 1;
  display: flex;
  flex-direction: column;
}

.course-meta {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
  font-size: 13px;
  color: #7f8c8d;
}

.course-meta span {
  display: flex;
  align-items: center;
  gap: 5px;
}

.course-title {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 15px 0;
  color: #2c3e50;
  line-height: 1.4;
}

.course-progress {
  margin-top: auto;
  margin-bottom: 20px;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 13px;
  color: #7f8c8d;
}

.progress-text {
  font-weight: 600;
  color: #3498db;
}

.progress-bar-bg {
  height: 6px;
  background: #ecf0f1;
  border-radius: 3px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  border-radius: 3px;
  background: linear-gradient(90deg, #3498db, #2ecc71);
  transition: width 0.6s ease;
}

.course-action-btn {
  width: 100%;
  padding: 12px;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
  margin-top: 10px;
  background: linear-gradient(135deg, #3498db, #2980b9);
  color: white;
}

.course-action-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(52, 152, 219, 0.3);
}

@media (max-width: 768px) {
  .header-section {
    flex-direction: column;
    align-items: flex-start;
  }

  .search-filter {
    width: 100%;
  }

  .search-input {
    width: 100%;
  }

  .courses-grid {
    grid-template-columns: 1fr;
  }
}
</style>
