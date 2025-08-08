<template>
  <div class="courses-page">
    <div class="header-section">
      <h1 class="page-title">Available Courses</h1>
      <div class="search-filter">
        <input type="text" placeholder="Search courses..." class="search-input">
        <select class="filter-select">
          <option>All Courses</option>
          <option>In Progress</option>
          <option>Completed</option>
          <option>Not Started</option>
        </select>
      </div>
    </div>

    <div class="courses-grid">
      <div
        v-for="(course, index) in courses"
        :key="course.id"
        class="course-card"
      >
        <div class="course-image-container" @click="openCourseDetails(course.id)">
          <img :src="course.image" :alt="course.title" class="course-image" />
          <span class="course-status" :class="course.status.toLowerCase().replace(/\s+/g, '-')">
            {{ course.status }}
          </span>
          <div class="course-category">Lifestyle</div>
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

          <div class="course-progress">
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
import LoginModal from './courselogin.vue'

export default {
  layout: 'dashboard',
  name: "CoursesPage",
  components: {
    LoginModal
  },
  data() {
    return {
      courses: [
        {
          id: 1,
          title: "Home Gardening Safety",
          lessons: 3,
          instructor: "Arianna",
          progress: 100,
          status: "Complete",
          image: "https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=800&q=60",
        },
        {
          id: 2,
          title: "Get Cash for Your Annuity",
          lessons: 2,
          instructor: "Adele",
          progress: 0,
          status: "Start Course",
          image: "https://images.unsplash.com/photo-1515377905703-c4788e51af15?auto=format&fit=crop&w=800&q=60",
        },
        {
          id: 3,
          title: "Concepts of Computer Engineering",
          lessons: 3,
          instructor: "Charles",
          progress: 100,
          status: "Complete",
          image: "https://images.unsplash.com/photo-1519389950473-47ba0277781c?auto=format&fit=crop&w=800&q=60",
        },
        {
          id: 4,
          title: "The American Frontier",
          lessons: 5,
          instructor: "Joseph",
          progress: 0,
          status: "Start Course",
          image: "https://images.unsplash.com/photo-1500534623283-312aade485b7?auto=format&fit=crop&w=800&q=60",
        },
        {
          id: 5,
          title: "Cybersecurity Standards",
          lessons: 5,
          instructor: "Robert",
          progress: 100,
          status: "Complete",
          image: "https://images.unsplash.com/photo-1504384308090-c894fdcc538d?auto=format&fit=crop&w=800&q=60",
        },
        {
          id: 6,
          title: "How to Fundraise",
          lessons: 4,
          instructor: "John",
          progress: 0,
          status: "Start Course",
          image: "https://images.unsplash.com/photo-1504384308090-c894fdcc538d?auto=format&fit=crop&w=800&q=60",
        },
      ],
      selectedCourseId: null,
      isLoggedIn: false
    };
  },
  methods: {
    openCourseDetails(courseId) {
      this.$router.push({ name: 'course-detail', params: { id: courseId } });
    },
    getButtonText(course) {
      if (course.progress === 0) return 'Start Now'
      if (course.progress === 100) return 'View Certificate'
      return 'Continue'
    },
    handleCourseAction(course) {
      this.selectedCourseId = course.id
      if (course.progress === 100) {
        // Handle view certificate
        alert('View certificate for ' + course.title)
      } else {
        // For static demo, we'll always show login
        this.$refs.loginModal.openModal()
      }
    },
     startCourse(courseId) {
    this.$router.push({
      name: 'course-learn',
      params: { id: courseId }
    })
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
}

.course-status.complete {
  background: linear-gradient(135deg, #2ecc71, #27ae60);
  color: white;
}

.course-status.start-course {
  background: linear-gradient(135deg, #f39c12, #e67e22);
  color: white;
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