<template>
  <div class="dashboard-container">
    <div class="dashboard-content">
      <div class="course-learning-container">
        <!-- Course Header -->
        <div class="course-header">
          <div class="header-top">
            <button class="back-button" @click="$router.go(-1)">
              <i class="fas fa-arrow-left"></i> Back to Course
            </button>
            <div class="progress-container">
              <span class="progress-text">Progress: {{ courseProgress }}%</span>
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: courseProgress + '%' }"></div>
              </div>
            </div>
          </div>

          <h1>{{ course.title }}</h1>

          <div class="course-meta">
            <span class="meta-item">
              <i class="fas fa-book-open"></i>
              {{ completedLessonsCount }}/{{ filteredLessons.length }} Lessons
            </span>
            <span class="meta-item">
              <i class="fas fa-clock"></i> {{ totalDuration }} min
            </span>
            <span class="meta-item" v-if="courseProgress === 100">
              <i class="fas fa-trophy"></i> Course Completed
            </span>
          </div>
        </div>

        <!-- Loading State -->
        <div v-if="loading.lessons" class="loading-message">
          <div class="spinner"></div>
          <p>Loading course content...</p>
        </div>

        <!-- Main Content Area -->
        <div v-else class="course-main-content">
          <!-- Sidebar Toggle for Mobile -->
          <div class="sidebar-toggle" @click="sidebarOpen = !sidebarOpen">
            <i class="fas" :class="sidebarOpen ? 'fa-times' : 'fa-list'"></i>
            {{ sidebarOpen ? 'Close' : 'Contents' }}
          </div>

          <!-- Sidebar -->
          <div class="lessons-sidebar" :class="{ open: sidebarOpen }">
            <div class="sidebar-header">
              <h3>Course Content</h3>
              <span class="completion-status">{{ courseProgress }}% Complete</span>
            </div>
            <div class="lessons-list">
              <div
                v-for="(lesson, index) in filteredLessons"
                :key="lesson.id"
                class="lesson-item"
                :class="{
                  active: currentLessonId === lesson.id,
                  completed: isLessonCompleted(lesson.id)
                }"
                @click="selectLesson(lesson.id)"
              >
                <div class="lesson-number">
                  <span v-if="!isLessonCompleted(lesson.id)">{{ index + 1 }}</span>
                  <i v-else class="fas fa-check"></i>
                </div>
                <div class="lesson-info">
                  <h3>{{ lesson.title || 'Untitled Lesson' }}</h3>
                  <p>{{ lesson.duration || 0 }} min</p>
                </div>
                <div class="lesson-status">
                  <i v-if="isLessonCompleted(lesson.id)" class="fas fa-check-circle"></i>
                </div>
              </div>
            </div>
          </div>

          <!-- Lesson Content Area -->
          <div class="lesson-content-area">
            <div v-if="currentLesson" class="lesson-content">
              <div class="lesson-header">
                <h2>{{ currentLesson.title || 'Untitled Lesson' }}</h2>
                <span class="lesson-duration">
                  <i class="fas fa-clock"></i> {{ currentLesson.duration || 0 }} min
                </span>
              </div>

              <!-- Video Content -->
              <div v-if="currentLesson.video_url" class="video-container">
                <div class="video-wrapper">
                  <iframe
                    width="100%"
                    height="500"
                    :src="formatVideoUrl(currentLesson.video_url)"
                    frameborder="0"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowfullscreen
                  ></iframe>
                </div>
              </div>

              <!-- Text Content -->
              <div class="lesson-text" v-html="formatLessonContent(currentLesson.description)"></div>

              <!-- Lesson Actions -->
              <div class="lesson-actions">
                <button
                  v-if="hasPreviousLesson"
                  class="prev-button"
                  @click="goToPreviousLesson"
                >
                  <i class="fas fa-arrow-left"></i> Previous Lesson
                </button>

                <button
                  v-if="!isLastLesson && !isLessonCompleted(currentLessonId)"
                  class="next-button"
                  @click="goToNextLesson"
                >
                  Next Lesson <i class="fas fa-arrow-right"></i>
                </button>

                <button
                  v-if="isLastLesson && !isLessonCompleted(currentLessonId)"
                  class="complete-button"
                  @click="markLessonComplete(currentLessonId)"
                >
                  <i class="fas fa-check-circle"></i> Complete Lesson
                </button>

                <button
                  v-if="isLessonCompleted(currentLessonId) && !isLastLesson"
                  class="next-button"
                  @click="goToNextLesson"
                >
                  Next Lesson <i class="fas fa-arrow-right"></i>
                </button>
              </div>
            </div>

            <!-- Empty States -->
            <div v-else-if="filteredLessons.length === 0" class="no-lesson-selected">
              <div class="empty-state">
                <i class="fas fa-book-open"></i>
                <h3>No Lessons Available</h3>
                <p>This course doesn't have any lessons yet.</p>
              </div>
            </div>
            <div v-else class="no-lesson-selected">
              <div class="empty-state">
                <i class="fas fa-hand-pointer"></i>
                <h3>Select a Lesson</h3>
                <p>Please select a lesson from the sidebar to get started</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Quiz Access Panel (Only shows when course is completed) -->
        <div v-if="courseProgress === 100" class="quiz-access-panel">
          <div class="quiz-access-card">
            <div class="completion-badge">
              <i class="fas fa-trophy"></i>
            </div>
            <h3>Course Completed!</h3>
            <p>You've successfully finished all lessons in this course.</p>

            <div v-if="hasQuiz" class="quiz-actions">
              <p>Test your knowledge with the final quiz</p>
              <button @click="startQuiz" class="quiz-start-btn">
                Take Final Quiz <i class="fas fa-arrow-right"></i>
              </button>
            </div>

            <div v-else class="no-quiz-message">
              <p>No quiz available for this course</p>
              <button @click="$router.push({ name: 'course-detail', params: { id: course.id } })"
                class="back-to-course-btn">
                <i class="fas fa-arrow-left"></i> Back to Course
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from "axios";

export default {
  layout: "dashboard",
  data() {
    return {
      course: {
        id: null,
        title: "Loading..."
      },
      lessons: [],
      progressData: [],
      completedLessons: [],
      courseProgress: 0,
      currentLessonId: null,
      currentUser: {
        id: 5, // Replace with actual logged-in user ID
        username: "testuser"
      },
      loading: {
        lessons: true,
        progress: true
      },
      hasQuiz: false,
      showQuiz: false,
      sidebarOpen: false
    };
  },
  async created() {
    await this.loadCourseAndLessons();
    await this.fetchProgressData();
    await this.checkForQuiz();
    this.setInitialLesson();
  },
  computed: {
    filteredLessons() {
      if (!Array.isArray(this.lessons)) return [];
      return this.lessons
        .filter(lesson =>
          lesson.course && lesson.course.some(c => c.id === this.course.id)
        )
        .sort((a, b) => parseFloat(a.order) - parseFloat(b.order));
    },
    currentLesson() {
      return this.filteredLessons.find((l) => l.id === this.currentLessonId) || null;
    },
    totalDuration() {
      return this.filteredLessons.reduce((sum, l) => sum + (parseFloat(l.duration) || 0), 0);
    },
    hasPreviousLesson() {
      if (!this.currentLessonId) return false;
      const idx = this.filteredLessons.findIndex((l) => l.id === this.currentLessonId);
      return idx > 0;
    },
    isLastLesson() {
      if (!this.currentLessonId) return false;
      const idx = this.filteredLessons.findIndex((l) => l.id === this.currentLessonId);
      return idx === this.filteredLessons.length - 1;
    },
    completedLessonsCount() {
      return this.completedLessons.length;
    }
  },
  methods: {
    async loadCourseAndLessons() {
      try {
        this.loading.lessons = true;
        const courseId = this.$route.params.id;

        // Fetch course
        const courseRes = await axios.get(`http://localhost/api/teople1/courses/${courseId}/`);

        // Always assign correctly
        if (courseRes.data.course) {
          this.course = courseRes.data.course;
        } else {
          this.course = courseRes.data;
        }

        // Make sure id exists
        if (!this.course.id) {
          this.course.id = parseInt(courseId);
        }

        // Fetch lessons
        const lessonRes = await axios.get(`http://localhost/api/teople1/lessons/`);
        this.lessons = lessonRes.data.lessons || lessonRes.data || [];
      } catch (err) {
        console.error("Error loading course and lessons:", err);
      } finally {
        this.loading.lessons = false;
      }
    },

    async fetchProgressData() {
      try {
        this.loading.progress = true;
        const res = await axios.get("http://localhost/api/teople1/progress/", {
          params: {
            user_id: this.currentUser.id,
            course_id: this.course.id
          }
        });

        if (res.data.status === "success") {
          this.progressData = res.data.progress;
          // Get completed lessons for this user and course
          this.completedLessons = this.getCompletedLessons();
          this.calculateProgress();
        }
      } catch (err) {
        console.error("Error fetching progress data:", err);
      } finally {
        this.loading.progress = false;
      }
    },

    async checkForQuiz() {
      try {
        const response = await axios.get(`http://localhost/api/teople1/quizzes/?course_id=${this.course.id}`);
        this.hasQuiz = response.data.count > 0 &&
                      response.data.quizzes.some(q => q.is_active && q.Questions.length > 0);
      } catch (error) {
        console.error("Error checking for quiz:", error);
        this.hasQuiz = false;
      }
    },

    startQuiz() {
      if (!this.course || !this.course.id) {
        console.error("Course ID missing, cannot start quiz.");
        return;
      }
      this.$router.push({
        name: 'course-quiz',
        params: { id: this.course.id }
      });
    },

    getCompletedLessons() {
      // Get all completed lessons for this user and course
      return this.progressData
        .filter(progress =>
          progress.user.some(u => u.id === this.currentUser.id) &&
          progress.course.some(c => c.id === this.course.id) &&
          progress.completed
        )
        .flatMap(progress => progress.lesson.map(l => l.id));
    },

    calculateProgress() {
      const totalLessons = this.filteredLessons.length;
      const completedCount = this.completedLessons.length;

      this.courseProgress = totalLessons > 0
        ? Math.round((completedCount / totalLessons) * 100)
        : 0;
    },

    setInitialLesson() {
      if (this.filteredLessons.length > 0) {
        // Try to find the first incomplete lesson
        const firstIncomplete = this.filteredLessons.find(
          lesson => !this.isLessonCompleted(lesson.id)
        );

        // Fall back to first lesson if all completed or no progress
        this.currentLessonId = firstIncomplete
          ? firstIncomplete.id
          : this.filteredLessons[0].id;
      }
    },

    async markLessonComplete(lessonId) {
      try {
        // Check if already completed
        if (this.isLessonCompleted(lessonId)) return;

        const payload = {
          order: "1.00000000000000000000",
          Name: `${this.currentUser.username}'s progress on lesson ${lessonId}`,
          user: [this.currentUser.id],
          course: [this.course.id],
          lesson: [lessonId],
          completed: true,
          notes: "Completed via course interface"
        };

        const res = await axios.post(
          "http://localhost/api/teople1/progress/",
          payload
        );

        if (res.data.status === "success") {
          this.completedLessons.push(lessonId);
          this.calculateProgress();

          // If this was the last lesson, show completion message
          if (this.isLastLesson && this.courseProgress === 100) {
            setTimeout(() => {
              alert(`🎉 Congratulations! You've completed the course "${this.course.title}"`);
            }, 500);
          }
        }
      } catch (err) {
        console.error("Error marking lesson complete:", err);
      }
    },

    selectLesson(lessonId) {
      this.currentLessonId = lessonId;
      // On mobile, close sidebar after selecting a lesson
      if (window.innerWidth < 1024) {
        this.sidebarOpen = false;
      }
    },

    async goToNextLesson() {
      const idx = this.filteredLessons.findIndex((l) => l.id === this.currentLessonId);
      if (idx >= 0 && idx < this.filteredLessons.length - 1) {
        // Mark current lesson as complete before proceeding
        await this.markLessonComplete(this.currentLessonId);
        this.currentLessonId = this.filteredLessons[idx + 1].id;
      }
    },

    goToPreviousLesson() {
      const idx = this.filteredLessons.findIndex((l) => l.id === this.currentLessonId);
      if (idx > 0) {
        this.currentLessonId = this.filteredLessons[idx - 1].id;
      }
    },

    isLessonCompleted(lessonId) {
      return this.completedLessons.includes(lessonId);
    },

    formatLessonContent(content) {
      if (!content) return "<p>No content available for this lesson.</p>";
      return `<p>${content.replace(/\n/g, '</p><p>')}</p>`;
    },

    formatVideoUrl(url) {
      if (!url) return '';
      if (url.includes('youtube.com/watch?v=')) {
        const videoId = url.split('v=')[1].split('&')[0];
        return `https://www.youtube.com/embed/${videoId}`;
      }
      return url;
    }
  },
  watch: {
    filteredLessons(newVal) {
      if (newVal.length > 0 && !this.currentLessonId) {
        this.setInitialLesson();
      }
    }
  }
};
</script>

<style scoped>
/* Base Styles */
.dashboard-container {
  display: flex;
  min-height: 100vh;
}

.dashboard-content {
  flex: 1;
  padding: 1.5rem;
  background: #f8fafc;
}

.course-learning-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

/* Header Styles */
.course-header {
  padding: 1.5rem 2rem;
  border-bottom: 1px solid #e2e8f0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.header-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.back-button {
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.2);
  padding: 0.6rem 1.2rem;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: white;
  backdrop-filter: blur(10px);
}

.back-button:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: translateY(-2px);
}

.progress-container {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.progress-text {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 0.25rem;
  font-weight: 500;
}

.progress-bar {
  width: 200px;
  height: 8px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #4fd1c5, #81e6d9);
  transition: width 0.5s ease;
  box-shadow: 0 0 10px rgba(79, 209, 197, 0.4);
}

.course-header h1 {
  margin: 0.5rem 0;
  font-size: 1.8rem;
  color: white;
  font-weight: 700;
}

.course-meta {
  display: flex;
  gap: 1.5rem;
  margin-top: 0.5rem;
  flex-wrap: wrap;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.85);
  background: rgba(255, 255, 255, 0.1);
  padding: 0.4rem 0.8rem;
  border-radius: 20px;
  backdrop-filter: blur(5px);
}

/* Loading State */
.loading-message {
  padding: 3rem;
  text-align: center;
  font-size: 1.2rem;
  color: #666;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e2e8f0;
  border-top: 4px solid #4299e1;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Main Content Layout */
.course-main-content {
  display: flex;
  min-height: 600px;
  position: relative;
}

/* Sidebar Toggle (Mobile) */
.sidebar-toggle {
  display: none;
  background: #4299e1;
  color: white;
  padding: 0.8rem 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  cursor: pointer;
  font-weight: 600;
  align-items: center;
  gap: 0.5rem;
  box-shadow: 0 2px 10px rgba(66, 153, 225, 0.3);
}

.sidebar-toggle i {
  font-size: 1.1rem;
}

/* Sidebar Styles */
.lessons-sidebar {
  width: 320px;
  border-right: 1px solid #e2e8f0;
  background: #f8fafc;
  transition: transform 0.3s ease;
}

.sidebar-header {
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
}

.sidebar-header h3 {
  margin: 0;
  font-size: 1.1rem;
  color: #2d3748;
  font-weight: 600;
}

.completion-status {
  background: #e6fffa;
  color: #38b2ac;
  padding: 0.3rem 0.8rem;
  border-radius: 9999px;
  font-size: 0.8rem;
  font-weight: 600;
}

.lessons-list {
  padding: 0.5rem;
  max-height: calc(100vh - 300px);
  overflow-y: auto;
}

.lesson-item {
  display: flex;
  align-items: center;
  padding: 0.9rem 1rem;
  border-radius: 8px;
  margin-bottom: 0.5rem;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid #e2e8f0;
  background: white;
}

.lesson-item:hover {
  background: #ebf8ff;
  border-color: #bee3f8;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.05);
}

.lesson-item.active {
  background: #ebf8ff;
  border-color: #90cdf4;
  box-shadow: 0 0 0 2px #ebf8ff;
}

.lesson-item.completed {
  border-left: 4px solid #48bb78;
}

.lesson-number {
  width: 30px;
  height: 30px;
  background: #4299e1;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 1rem;
  font-weight: bold;
  font-size: 0.9rem;
  flex-shrink: 0;
  transition: all 0.3s ease;
}

.lesson-item.completed .lesson-number {
  background: #48bb78;
}

.lesson-info {
  flex: 1;
  min-width: 0;
}

.lesson-info h3 {
  margin: 0 0 0.25rem 0;
  font-size: 0.95rem;
  color: #2d3748;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-weight: 500;
}

.lesson-info p {
  margin: 0;
  font-size: 0.8rem;
  color: #718096;
}

.lesson-status {
  width: 20px;
  color: #48bb78;
  flex-shrink: 0;
}

/* Lesson Content Area */
.lesson-content-area {
  flex: 1;
  padding: 2rem;
  background: #fff;
}

.lesson-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #e2e8f0;
  flex-wrap: wrap;
  gap: 1rem;
}

.lesson-header h2 {
  margin: 0;
  font-size: 1.6rem;
  color: #2d3748;
  font-weight: 600;
}

.lesson-duration {
  background: #ebf8ff;
  color: #2b6cb0;
  padding: 0.4rem 1rem;
  border-radius: 9999px;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 500;
}

.video-container {
  margin: 1.5rem 0;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 6px 15px rgba(0, 0, 0, 0.1);
}

.video-wrapper {
  position: relative;
  padding-bottom: 56.25%;
  height: 0;
  overflow: hidden;
}

.video-wrapper iframe {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border-radius: 12px;
}

.lesson-text {
  line-height: 1.7;
  color: #4a5568;
  margin: 2rem 0;
  font-size: 1.05rem;
}

.lesson-text >>> h3 {
  color: #2d3748;
  margin-top: 1.5rem;
  margin-bottom: 1rem;
  font-weight: 600;
}

.lesson-text >>> ul {
  padding-left: 1.5rem;
  margin: 1rem 0;
}

.lesson-text >>> li {
  margin-bottom: 0.5rem;
}

.lesson-actions {
  display: flex;
  justify-content: space-between;
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e2e8f0;
  flex-wrap: wrap;
  gap: 1rem;
}

.prev-button, .next-button, .complete-button {
  padding: 0.9rem 1.8rem;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.95rem;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.prev-button {
  background: #f7fafc;
  color: #4a5568;
  border: 1px solid #cbd5e0;
}

.prev-button:hover {
  background: #edf2f7;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.next-button {
  background: #4299e1;
  color: white;
}

.next-button:hover {
  background: #3182ce;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(66, 153, 225, 0.3);
}

.complete-button {
  background: #48bb78;
  color: white;
}

.complete-button:hover {
  background: #38a169;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(72, 187, 120, 0.3);
}

/* Empty States */
.no-lesson-selected {
  padding: 2rem;
  text-align: center;
  height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-state {
  color: #718096;
}

.empty-state i {
  font-size: 3rem;
  margin-bottom: 1rem;
  color: #cbd5e0;
}

.empty-state h3 {
  margin: 0 0 0.5rem 0;
  color: #4a5568;
  font-size: 1.3rem;
}

.empty-state p {
  margin: 0;
  font-size: 1rem;
}

/* Quiz Access Panel Styles */
.quiz-access-panel {
  margin-top: 40px;
  padding: 30px;
  background: linear-gradient(135deg, #f6f9fc 0%, #e9ecef 100%);
  border-radius: 12px;
  text-align: center;
  border: 1px solid #e9ecef;
}

.quiz-access-card {
  max-width: 600px;
  margin: 0 auto;
}

.completion-badge {
  font-size: 3.5rem;
  color: #ffc107;
  margin-bottom: 1rem;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.quiz-access-card h3 {
  font-size: 1.8rem;
  margin-bottom: 0.5rem;
  color: #343a40;
  font-weight: 700;
}

.quiz-access-card p {
  color: #6c757d;
  margin-bottom: 1.5rem;
  font-size: 1.1rem;
}

.quiz-actions {
  margin-top: 2rem;
}

.quiz-start-btn {
  padding: 14px 28px;
  background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(40, 167, 69, 0.3);
}

.quiz-start-btn:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 20px rgba(40, 167, 69, 0.4);
}

.quiz-start-btn i {
  margin-left: 8px;
}

.no-quiz-message {
  margin-top: 1.5rem;
  color: #6c757d;
}

.back-to-course-btn {
  margin-top: 1rem;
  padding: 10px 20px;
  background: #6c757d;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.3s;
}

.back-to-course-btn:hover {
  background: #5a6268;
}

/* Responsive Design */
@media (max-width: 1024px) {
  .course-main-content {
    flex-direction: column;
  }

  .lessons-sidebar {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid #e2e8f0;
    transform: translateX(-100%);
    position: absolute;
    z-index: 100;
    height: calc(100% - 60px);
    overflow-y: auto;
  }

  .lessons-sidebar.open {
    transform: translateX(0);
  }

  .sidebar-toggle {
    display: flex;
  }

  .lessons-list {
    max-height: none;
  }
}

@media (max-width: 768px) {
  .dashboard-content {
    padding: 1rem;
  }

  .course-header {
    padding: 1.2rem;
  }

  .header-top {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }

  .progress-container {
    width: 100%;
    align-items: flex-start;
  }

  .progress-bar {
    width: 100%;
  }

  .course-header h1 {
    font-size: 1.5rem;
  }

  .course-meta {
    gap: 0.8rem;
  }

  .meta-item {
    font-size: 0.85rem;
  }

  .lesson-content-area {
    padding: 1.5rem;
  }

  .lesson-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.8rem;
  }

  .lesson-header h2 {
    font-size: 1.4rem;
  }

  .lesson-actions {
    flex-direction: column;
    gap: 0.75rem;
  }

  .prev-button, .next-button, .complete-button {
    width: 100%;
    justify-content: center;
  }

  .quiz-access-panel {
    padding: 1.5rem;
    margin-top: 2rem;
  }

  .quiz-access-card h3 {
    font-size: 1.5rem;
  }
}

@media (max-width: 480px) {
  .dashboard-content {
    padding: 0.5rem;
  }

  .course-header {
    padding: 1rem;
  }

  .lesson-content-area {
    padding: 1rem;
  }

  .lesson-text {
    font-size: 1rem;
  }

  .meta-item {
    padding: 0.3rem 0.6rem;
  }

  .quiz-access-card h3 {
    font-size: 1.3rem;
  }

  .quiz-start-btn {
    padding: 12px 20px;
    font-size: 1rem;
  }
}
</style>