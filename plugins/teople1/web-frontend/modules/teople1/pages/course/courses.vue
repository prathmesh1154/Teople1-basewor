<template>
  <div class="courses-dashboard">

    <!-- Dashboard Header -->
    <div class="dashboard-header">
      <div class="header-content">
        <h1 class="page-title">Learning Dashboard</h1>
        <p class="page-subtitle">Track your learning progress and explore courses</p>
      </div>
      <div class="user-profile">
        <div class="user-avatar">
          <i class="fas fa-user"></i>
        </div>
      </div>
    </div>

    <!-- Statistics Cards -->
    <div class="stats-container">
      <div class="stat-card">
        <div class="stat-icon" style="background-color: rgba(79, 70, 229, 0.1);">
          <i class="fas fa-book-open" style="color: #4f46e5;"></i>
        </div>
        <div class="stat-info">
          <h3>{{ courses.length }}</h3>
          <p>Total Courses</p>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon" style="background-color: rgba(16, 185, 129, 0.1);">
          <i class="fas fa-check-circle" style="color: #10b981;"></i>
        </div>
        <div class="stat-info">
          <h3>{{ completedCoursesCount }}</h3>
          <p>Completed</p>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon" style="background-color: rgba(245, 158, 11, 0.1);">
          <i class="fas fa-spinner" style="color: #f59e0b;"></i>
        </div>
        <div class="stat-info">
          <h3>{{ inProgressCoursesCount }}</h3>
          <p>In Progress</p>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon" style="background-color: rgba(156, 163, 175, 0.1);">
          <i class="fas fa-clock" style="color: #9ca3af;"></i>
        </div>
        <div class="stat-info">
          <h3>{{ notStartedCoursesCount }}</h3>
          <p>Not Started</p>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div class="dashboard-content">
      <!-- Charts Section -->
      <div class="charts-section">
        <div class="chart-card">
          <div class="chart-header">
            <h3>Course Progress Overview</h3>
            <select class="chart-filter">
              <option>Last 7 Days</option>
              <option>Last 30 Days</option>
              <option>All Time</option>
            </select>
          </div>
          <div class="chart-container">
            <canvas ref="progressChart" height="250"></canvas>
          </div>
        </div>

        <div class="chart-card">
          <div class="chart-header">
            <h3>Course Distribution</h3>
          </div>
          <div class="chart-container">
            <canvas ref="distributionChart" height="250"></canvas>
          </div>
        </div>
      </div>

      <!-- Courses Section -->
      <div class="courses-section">
        <div class="section-header">
          <h2>Available Courses</h2>
          <div class="controls">
            <div class="search-box">
              <i class="fas fa-search"></i>
              <input
                type="text"
                placeholder="Search courses..."
                v-model="searchQuery"
                @input="filterCourses"
              />
            </div>
            <select class="filter-select" v-model="filterStatus" @change="filterCourses">
              <option value="all">All Courses</option>
              <option value="in-progress">In Progress</option>
              <option value="completed">Completed</option>
              <option value="not-started">Not Started</option>
            </select>
            <div class="view-toggle">
              <button :class="['view-btn', { active: viewMode === 'grid' }]" @click="viewMode = 'grid'">
                <i class="fas fa-th"></i>
              </button>
              <button :class="['view-btn', { active: viewMode === 'list' }]" @click="viewMode = 'list'">
                <i class="fas fa-list"></i>
              </button>
            </div>
          </div>
        </div>

        <div :class="['courses-container', viewMode]">
          <div
            v-for="course in filteredCourses"
            :key="course.id"
            :class="['course-card', viewMode]"
          >
            <div class="course-image-container" @click="openCourseDetails(course.id)">
              <img :src="course.image" :alt="course.title" class="course-image" />
              <span class="course-status" :class="statusClass(course.status)">
                {{ course.status }}
                <span v-if="course.hasQuiz && course.status === 'Completed'" class="quiz-badge">
                  <i class="fas fa-question-circle"></i>
                </span>
              </span>
              <div class="course-category">{{ course.category }}</div>
            </div>

            <div class="course-content">
              <div class="course-meta">
                <span class="course-instructor">
                  <i class="fas fa-user"></i> {{ course.instructor }}
                </span>
                <span class="course-duration">
                  <i class="fas fa-clock"></i> {{ course.lessons }} Lessons
                </span>
              </div>

              <h3 class="course-title" @click="openCourseDetails(course.id)">{{ course.title }}</h3>
              <p class="course-description">{{ truncateDescription(course.description) }}</p>

              <div class="course-progress" v-if="course.lessons > 0">
                <div class="progress-info">
                  <span class="progress-text">{{ course.progress }}% Complete</span>
                  <span class="progress-lessons">{{ getCompletedLessons(course) }}/{{ course.lessons }} lessons</span>
                </div>
                <div class="progress-bar">
                  <div
                    class="progress-fill"
                    :style="{ width: course.progress + '%' }"
                  ></div>
                </div>
              </div>

              <button
                class="course-action-btn"
                @click.stop="handleCourseAction(course)"
                :class="{
                  'start-btn': course.progress === 0,
                  'continue-btn': course.progress > 0 && course.progress < 100,
                  'complete-btn': course.progress === 100
                }"
              >
                {{ getButtonText(course) }}
                <span v-if="course.hasQuiz && course.status === 'Completed'" class="quiz-indicator">
                  <i class="fas fa-question-circle"></i>
                </span>
              </button>
            </div>
          </div>
        </div>

        <div v-if="filteredCourses.length === 0" class="no-courses">
          <i class="fas fa-search"></i>
          <h3>No courses found</h3>
          <p>Try adjusting your search or filter criteria</p>
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
import Chart from 'chart.js/auto'


export default {
  layout: 'dashboard',
  name: "CoursesDashboard",
  components: {
    LoginModal
  },
  data() {
    return {
      courses: [],
      filteredCourses: [],
      selectedCourseId: null,
      searchQuery: '',
      filterStatus: 'all',
      quizzes: [],
      viewMode: 'grid',
      progressChart: null,
      distributionChart: null
    };
  },
  computed: {
    completedCoursesCount() {
      return this.courses.filter(course => course.status === 'Completed').length;
    },
    inProgressCoursesCount() {
      return this.courses.filter(course => course.status === 'In Progress').length;
    },
    notStartedCoursesCount() {
      return this.courses.filter(course => course.status === 'Not Started').length;
    }
  },
  async created() {
    await this.fetchCourses();
    await this.fetchQuizzes();
  },
  mounted() {
    this.$nextTick(() => {
      this.createCharts();
    });

    // Update charts on window resize
    window.addEventListener('resize', this.handleResize);
  },
  beforeDestroy() {
    if (this.progressChart) {
      this.progressChart.destroy();
    }
    if (this.distributionChart) {
      this.distributionChart.destroy();
    }

    window.removeEventListener('resize', this.handleResize);
  },
  methods: {
    handleResize() {
      if (this.progressChart) {
        this.progressChart.resize();
      }
      if (this.distributionChart) {
        this.distributionChart.resize();
      }
    },
    async fetchCourses() {
      try {
        const [courseRes, progressRes] = await Promise.all([
          axios.get('http://localhost/api/teople1/courses/'),
          axios.get('http://localhost/api/teople1/progress/')
        ]);

        const progressList = progressRes.data.status === 'success' ? progressRes.data.progress : [];

        if (courseRes.data.status === 'success') {
          this.courses = courseRes.data.courses.map(c => {
            const courseProgressItems = progressList.filter(
              p => p.course && p.course.some(co => co.id === c.id)
            );

            const totalLessons = c.Lessons ? c.Lessons.length : 0;
            let completedLessons = 0;

            if (totalLessons > 0 && courseProgressItems.length > 0) {
              const completedLessonIds = new Set();
              courseProgressItems.forEach(progressItem => {
                if (progressItem.lesson) {
                  progressItem.lesson.forEach(lesson => {
                    if (c.Lessons.some(courseLesson => courseLesson.id === lesson.id)) {
                      completedLessonIds.add(lesson.id);
                    }
                  });
                }
              });
              completedLessons = completedLessonIds.size;
            }

            const progress = totalLessons > 0
              ? Math.min(100, Math.floor((completedLessons / totalLessons) * 100))
              : 0;

            let status = 'Not Started';
            if (progress === 100) status = 'Completed';
            else if (progress > 0) status = 'In Progress';

            const isCompleted = courseProgressItems.some(item => item.completed);

            return {
              id: c.id,
              title: c.title || 'Untitled Course',
              description: c.description || '',
              lessons: totalLessons,
              completedLessons,
              instructor: c.instructor && c.instructor.length > 0
                ? c.instructor.join(', ')
                : 'N/A',
              progress,
              status: isCompleted ? 'Completed' : status,
              image: c.image_url || 'https://via.placeholder.com/340x180?text=No+Image',
              category: c.difficulty ? c.difficulty.value : '',
              hasQuiz: this.quizzes.some(q => q.course && q.course.some(co => co.id === c.id))
            };
          });

          this.filteredCourses = [...this.courses];
          this.$nextTick(() => {
            this.updateCharts();
          });
        }
      } catch (err) {
        console.error('Error fetching courses/progress:', err);
      }
    },

    async fetchQuizzes() {
      try {
        const response = await axios.get('http://localhost/api/teople1/quizzes/');

        if (response.data?.status === 'success') {
          // Filter only active quizzes with questions
          this.quizzes = (response.data.quizzes || []).filter(q =>
            q?.is_active &&
            Array.isArray(q.Questions) &&
            q.Questions.length > 0
          );

          // Update courses with quiz info if we have courses
          if (Array.isArray(this.courses)) {
            this.courses = this.courses.map(course => {
              if (!course?.id) return course;

              const hasQuiz = this.quizzes.some(q =>
                Array.isArray(q.course) &&
                q.course.some(co => co?.id === course.id)
              );

              return {
                ...course,
                hasQuiz
              };
            });

            // Update filtered courses while preserving any existing filters
            this.filteredCourses = this.applyFilters([...this.courses]);
          }
        } else {
          console.warn('Unexpected quiz response format:', response.data);
        }
      } catch (error) {
        console.error('Error fetching quizzes:', error);
        this.$notify({
          type: 'error',
          title: 'Quiz Error',
          text: 'Failed to load quiz information. Please try again later.'
        });
      }
    },

    createCharts() {
      const progressCtx = this.$refs.progressChart;
      const distributionCtx = this.$refs.distributionChart;

      if (progressCtx && distributionCtx) {
        // Progress Chart
        this.progressChart = new Chart(progressCtx, {
          type: 'bar',
          data: {
            labels: this.courses.map(c => c.title.length > 15 ? c.title.substring(0, 15) + '...' : c.title),
            datasets: [{
              label: 'Progress (%)',
              data: this.courses.map(c => c.progress),
              backgroundColor: this.courses.map(c => {
                if (c.progress === 100) return '#10B981';
                if (c.progress > 0) return '#3B82F6';
                return '#EF4444';
              }),
              borderWidth: 0,
              borderRadius: 6,
              barPercentage: 0.6,
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                display: false
              },
              tooltip: {
                backgroundColor: '#1F2937',
                titleFont: {
                  family: "'Poppins', sans-serif"
                },
                bodyFont: {
                  family: "'Poppins', sans-serif"
                }
              }
            },
            scales: {
              y: {
                beginAtZero: true,
                max: 100,
                grid: {
                  color: 'rgba(0, 0, 0, 0.05)'
                },
                ticks: {
                  font: {
                    family: "'Poppins', sans-serif"
                  },
                  callback: function(value) {
                    return value + '%';
                  }
                }
              },
              x: {
                grid: {
                  display: false
                },
                ticks: {
                  font: {
                    family: "'Poppins', sans-serif"
                  }
                }
              }
            }
          }
        });

        // Distribution Chart
        this.distributionChart = new Chart(distributionCtx, {
          type: 'doughnut',
          data: {
            labels: ['Completed', 'In Progress', 'Not Started'],
            datasets: [{
              data: [this.completedCoursesCount, this.inProgressCoursesCount, this.notStartedCoursesCount],
              backgroundColor: ['#10B981', '#F59E0B', '#9CA3AF'],
              borderWidth: 0,
              hoverOffset: 10
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                position: 'bottom',
                labels: {
                  font: {
                    family: "'Poppins', sans-serif"
                  },
                  padding: 20
                }
              }
            },
            cutout: '70%'
          }
        });
      }
    },

    updateCharts() {
      if (this.progressChart) {
        this.progressChart.data.labels = this.courses.map(c => c.title.length > 15 ? c.title.substring(0, 15) + '...' : c.title);
        this.progressChart.data.datasets[0].data = this.courses.map(c => c.progress);
        this.progressChart.data.datasets[0].backgroundColor = this.courses.map(c => {
          if (c.progress === 100) return '#10B981';
          if (c.progress > 0) return '#3B82F6';
          return '#EF4444';
        });
        this.progressChart.update();
      }

      if (this.distributionChart) {
        this.distributionChart.data.datasets[0].data = [
          this.completedCoursesCount,
          this.inProgressCoursesCount,
          this.notStartedCoursesCount
        ];
        this.distributionChart.update();
      }
    },

    openCourseDetails(courseId) {
      if (!courseId) {
        console.error('Cannot open course details - missing course ID');
        return;
      }
      this.$router.push({
        name: 'course-detail',
        params: { id: courseId }
      }).catch(err => {
        if (err.name !== 'NavigationDuplicated') {
          console.error('Navigation error:', err);
        }
      });
    },

    getButtonText(course) {
      if (!course) return 'Start Now';

      if (course.progress === 0) return 'Start Now';
      if (course.progress === 100) {
        return course.hasQuiz ? 'Take Quiz' : 'View Certificate';
      }
      return 'Continue';
    },

    handleCourseAction(course) {
      if (!course?.id) {
        console.error('Invalid course data - missing ID');
        return;
      }

      this.selectedCourseId = course.id;

      if (course.progress === 100) {
        if (course.hasQuiz) {
          this.navigateToQuiz(course.id);
        } else {
          this.showCertificateAlert(course.title);
        }
      } else {
        this.openCourseDetails(course.id);
      }
    },

    navigateToQuiz(courseId) {
      this.$router.push({
        name: 'course-quiz',
        params: { id: courseId }
      }).catch(err => {
        if (err.name !== 'NavigationDuplicated') {
          console.error('Quiz navigation error:', err);
          this.$notify({
            type: 'error',
            title: 'Navigation Error',
            text: 'Could not open quiz. Please try again.'
          });
        }
      });
    },

    showCertificateAlert(courseTitle) {
      this.$notify({
        type: 'info',
        title: 'Certificate Available',
        text: `View certificate for ${courseTitle || 'this course'}`
      });
    },

    applyFilters(courses) {
      let filtered = courses || [];

      if (this.searchQuery.trim() !== '') {
        const q = this.searchQuery.toLowerCase();
        filtered = filtered.filter(c =>
          (c.title?.toLowerCase().includes(q) || '') ||
          (c.category?.toLowerCase().includes(q) || '') ||
          (c.instructor?.toLowerCase().includes(q) || '')
        );
      }

      if (this.filterStatus !== 'all') {
        const statusMap = {
          'in-progress': 'In Progress',
          'completed': 'Completed',
          'not-started': 'Not Started'
        };
        filtered = filtered.filter(c => c.status === statusMap[this.filterStatus]);
      }

      return filtered;
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
      this.filteredCourses = this.applyFilters([...this.courses]);
    },

    truncateDescription(description) {
      if (!description) return '';
      return description.length > 100
        ? description.substring(0, 100) + '...'
        : description;
    },

    getCompletedLessons(course) {
      return course.completedLessons || 0;
    }
  }
};
</script>

<style scoped>
/* Base Styles */
.courses-dashboard {
  min-height: 100vh;
  background-color: #F9FAFB;
  padding: 20px;
  font-family: 'Poppins', sans-serif;
}

/* Dashboard Header */
.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.header-content .page-title {
  font-size: 24px;
  font-weight: 700;
  color: #111827;
  margin: 0 0 8px 0;
}

.header-content .page-subtitle {
  font-size: 14px;
  color: #6B7280;
  margin: 0;
}

.user-profile {
  display: flex;
  align-items: center;
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: #E5E7EB;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #4B5563;
}

/* Stats Container */
.stats-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  border: 1px solid #E5E7EB;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
  font-size: 20px;
}

.stat-info h3 {
  font-size: 24px;
  font-weight: 700;
  color: #111827;
  margin: 0 0 4px 0;
}

.stat-info p {
  font-size: 14px;
  color: #6B7280;
  margin: 0;
}

/* Dashboard Content */
.dashboard-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* Charts Section */
.charts-section {
  display: grid;
  grid-template-columns: repeat(1, 1fr);
  gap: 24px;
}

@media (min-width: 1024px) {
  .charts-section {
    grid-template-columns: repeat(2, 1fr);
  }
}

.chart-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  border: 1px solid #E5E7EB;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.chart-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
  margin: 0;
}

.chart-filter {
  padding: 6px 12px;
  border: 1px solid #D1D5DB;
  border-radius: 6px;
  font-size: 14px;
  color: #4B5563;
  background-color: white;
}

.chart-container {
  position: relative;
  height: 250px;
  width: 100%;
}

/* Courses Section */
.courses-section {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  border: 1px solid #E5E7EB;
}

.section-header {
  margin-bottom: 24px;
}

.section-header h2 {
  font-size: 20px;
  font-weight: 600;
  color: #111827;
  margin: 0 0 16px 0;
}

.controls {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-items: center;
}

.search-box {
  position: relative;
  flex: 1;
  min-width: 200px;
}

.search-box i {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: #9CA3AF;
}

.search-box input {
  width: 100%;
  padding: 10px 12px 10px 36px;
  border: 1px solid #D1D5DB;
  border-radius: 8px;
  font-size: 14px;
  color: #4B5563;
}

.search-box input:focus {
  outline: none;
  border-color: #3B82F6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.filter-select {
  padding: 10px 12px;
  border: 1px solid #D1D5DB;
  border-radius: 8px;
  font-size: 14px;
  color: #4B5563;
  background-color: white;
  min-width: 150px;
}

.view-toggle {
  display: flex;
  border: 1px solid #D1D5DB;
  border-radius: 8px;
  overflow: hidden;
}

.view-btn {
  padding: 10px 12px;
  background: white;
  border: none;
  color: #9CA3AF;
  cursor: pointer;
  transition: all 0.2s;
}

.view-btn.active {
  background-color: #F3F4F6;
  color: #374151;
}

.view-btn:first-child {
  border-right: 1px solid #D1D5DB;
}

/* Courses Container */
.courses-container.grid {
  display: grid;
  grid-template-columns: repeat(1, 1fr);
  gap: 20px;
}

@media (min-width: 640px) {
  .courses-container.grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 1024px) {
  .courses-container.grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

.courses-container.list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* Course Cards */
.course-card.grid {
  background: white;
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  border: 1px solid #E5E7EB;
  transition: all 0.2s;
}

.course-card.grid:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
}

.course-card.list {
  display: flex;
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  border: 1px solid #E5E7EB;
  transition: all 0.2s;
}

.course-card.list:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
}

.course-card.list .course-image-container {
  width: 240px;
  height: 180px;
  flex-shrink: 0;
}

.course-card.list .course-content {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
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
  transition: transform 0.3s ease;
}

.course-card:hover .course-image {
  transform: scale(1.05);
}

.course-status {
  position: absolute;
  top: 12px;
  right: 12px;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  color: white;
}

.course-status.complete {
  background-color: #10B981;
}

.course-status.in-progress {
  background-color: #F59E0B;
}

.course-status.not-started {
  background-color: #9CA3AF;
}

.course-category {
  position: absolute;
  bottom: 12px;
  left: 12px;
  background: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}

.course-content {
  padding: 16px;
  flex-grow: 1;
  display: flex;
  flex-direction: column;
}

.course-meta {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
  font-size: 13px;
  color: #6B7280;
}

.course-meta span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.course-title {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 8px 0;
  color: #111827;
  line-height: 1.4;
  cursor: pointer;
  transition: color 0.2s;
}

.course-title:hover {
  color: #3B82F6;
}

.course-description {
  font-size: 14px;
  color: #6B7280;
  margin: 0 0 16px 0;
  line-height: 1.5;
}

.course-progress {
  margin-top: auto;
  margin-bottom: 16px;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 13px;
}

.progress-text {
  font-weight: 600;
  color: #3B82F6;
}

.progress-lessons {
  color: #6B7280;
}

.progress-bar {
  height: 6px;
  background: #E5E7EB;
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 3px;
  background: #3B82F6;
  transition: width 0.6s ease;
}

.course-action-btn {
  width: 100%;
  padding: 10px 16px;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.start-btn {
  background-color: #3B82F6;
}

.start-btn:hover {
  background-color: #2563EB;
}

.continue-btn {
  background-color: #F59E0B;
}

.continue-btn:hover {
  background-color: #D97706;
}

.complete-btn {
  background-color: #10B981;
}

.complete-btn:hover {
  background-color: #059669;
}

.quiz-badge, .quiz-indicator {
  margin-left: 4px;
  color: white;
}

.course-status.complete {
  position: relative;
  padding-right: 25px;
}

.quiz-badge {
  position: absolute;
  right: 5px;
  top: 50%;
  transform: translateY(-50%);
}

.quiz-indicator {
  margin-left: 8px;
}

/* No Courses */
.no-courses {
  text-align: center;
  padding: 40px 20px;
  color: #6B7280;
}

.no-courses i {
  font-size: 48px;
  margin-bottom: 16px;
  color: #D1D5DB;
}

.no-courses h3 {
  font-size: 18px;
  margin: 0 0 8px 0;
  color: #374151;
}

.no-courses p {
  margin: 0;
  font-size: 14px;
}

/* Responsive Adjustments */
@media (max-width: 768px) {
  .courses-dashboard {
    padding: 16px;
  }

  .dashboard-header {
    flex-direction: column;
    gap: 16px;
  }

  .stats-container {
    grid-template-columns: repeat(2, 1fr);
  }

  .controls {
    flex-direction: column;
    align-items: stretch;
  }

  .search-box {
    min-width: auto;
  }

  .course-card.list {
    flex-direction: column;
  }

  .course-card.list .course-image-container {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .stats-container {
    grid-template-columns: 1fr;
  }

  .chart-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .chart-filter {
    align-self: flex-end;
  }
}
</style>