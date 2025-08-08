<template>
  <div class="dashboard-container">
    <div class="dashboard-content">
      <div class="course-learning-container">
        <!-- Course header section -->
        <div class="course-header">
          <div class="header-top">
            <button class="back-button" @click="$router.go(-1)">
              <i class="fas fa-arrow-left"></i> Back to Course
            </button>
            <div class="progress-container">
              <span class="progress-text">Progress: {{ course.progress }}%</span>
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: course.progress + '%' }"></div>
              </div>
            </div>
          </div>
          <h1>{{ course.title }}</h1>
          <div class="course-meta">
            <span class="meta-item">
              <i class="fas fa-book-open"></i> {{ completedLessons }}/{{ lessons.length }} Lessons
            </span>
            <span class="meta-item">
              <i class="fas fa-clock"></i> {{ totalDuration }} min
            </span>
          </div>
        </div>

        <!-- Main content area -->
        <div class="course-main-content">
          <!-- Lessons sidebar -->
          <div class="lessons-sidebar">
            <div class="sidebar-header">
              <h3>Course Content</h3>
              <span class="completion-status">{{ course.progress }}% Complete</span>
            </div>
            <div class="lessons-list">
              <div
                v-for="(lesson, index) in lessons"
                :key="lesson.id"
                class="lesson-item"
                :class="{
                  active: currentLessonId === lesson.id,
                  completed: lesson.completed
                }"
                @click="selectLesson(lesson.id)"
              >
                <div class="lesson-number">
                  <span v-if="!lesson.completed">{{ index + 1 }}</span>
                  <i v-else class="fas fa-check"></i>
                </div>
                <div class="lesson-info">
                  <h3>{{ lesson.title }}</h3>
                  <p>{{ lesson.duration }} min</p>
                </div>
                <div class="lesson-status">
                  <i v-if="lesson.completed" class="fas fa-check-circle"></i>
                </div>
              </div>
            </div>
          </div>

          <!-- Lesson content -->
          <div class="lesson-content-area">
            <div v-if="currentLesson" class="lesson-content">
              <div class="lesson-header">
                <h2>{{ currentLesson.title }}</h2>
                <span class="lesson-duration">
                  <i class="fas fa-clock"></i> {{ currentLesson.duration }} min
                </span>
              </div>

              <div v-if="currentLesson.videoUrl" class="video-container">
                <div class="video-wrapper">
                  <iframe
                    width="100%"
                    height="500"
                    :src="currentLesson.videoUrl"
                    frameborder="0"
                    allowfullscreen
                  ></iframe>
                </div>
              </div>

              <div class="lesson-text" v-html="currentLesson.content"></div>

              <div class="lesson-actions">
                <button
                  v-if="hasPreviousLesson"
                  class="prev-button"
                  @click="goToPreviousLesson"
                >
                  <i class="fas fa-arrow-left"></i> Previous Lesson
                </button>

                <button
                  v-if="!isLastLesson"
                  class="next-button"
                  @click="goToNextLesson"
                >
                  Next Lesson <i class="fas fa-arrow-right"></i>
                </button>

                <button
                  v-else
                  class="complete-button"
                  @click="completeCourse"
                >
                  <i class="fas fa-check-circle"></i> Complete Course
                </button>
              </div>
            </div>
          </div>
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
      course: {
        id: null,
        title: '',
        progress: 0
      },
      currentLessonId: null,
      lessons: [
        {
          id: 1,
          title: 'Introduction to Gardening Safety',
          duration: 15,
          content: `
            <p>Welcome to the Home Gardening Safety course. Gardening is a rewarding activity, but it's important to be aware of potential hazards.</p>
            <h3>Key Safety Principles:</h3>
            <ul>
              <li>Always wear appropriate protective gear</li>
              <li>Be aware of your surroundings</li>
              <li>Use tools properly</li>
              <li>Stay hydrated and take breaks</li>
            </ul>
            <p>In this lesson, we'll cover the basics of creating a safe gardening environment.</p>
          `,
          videoUrl: 'https://www.youtube.com/embed/dQw4w9WgXcQ',
          completed: false
        },
        {
          id: 2,
          title: 'Identifying Garden Hazards',
          duration: 20,
          content: `
            <p>Gardens contain many potential hazards that you should be aware of:</p>
            <h3>Common Hazards:</h3>
            <ul>
              <li>Sharp tools and equipment</li>
              <li>Poisonous plants</li>
              <li>Uneven terrain</li>
              <li>Sun exposure</li>
              <li>Insect bites and stings</li>
            </ul>
            <p>We'll go through each of these in detail and discuss how to mitigate the risks.</p>
          `,
          videoUrl: 'https://www.youtube.com/embed/dQw4w9WgXcQ',
          completed: false
        },
        {
          id: 3,
          title: 'Proper Tool Usage',
          duration: 25,
          content: `
            <p>Using garden tools properly is essential for both safety and effectiveness.</p>
            <h3>Tool Safety Tips:</h3>
            <ul>
              <li>Keep tools clean and sharp</li>
              <li>Store tools properly when not in use</li>
              <li>Use the right tool for the job</li>
              <li>Wear gloves when handling sharp tools</li>
            </ul>
            <p>This lesson includes demonstrations of proper tool techniques.</p>
          `,
          videoUrl: 'https://www.youtube.com/embed/dQw4w9WgXcQ',
          completed: false
        }
      ]
    }
  },
  computed: {
    currentLesson() {
      return this.lessons.find(l => l.id === this.currentLessonId)
    },
    hasPreviousLesson() {
      const index = this.lessons.findIndex(l => l.id === this.currentLessonId)
      return index > 0
    },
    isLastLesson() {
      const index = this.lessons.findIndex(l => l.id === this.currentLessonId)
      return index === this.lessons.length - 1
    },
    completedLessons() {
      return this.lessons.filter(l => l.completed).length
    },
    totalDuration() {
      return this.lessons.reduce((total, lesson) => total + lesson.duration, 0)
    }
  },
  created() {
    this.loadCourse()
  },
  methods: {
    loadCourse() {
      const courseId = this.$route.params.id
      // Load from localStorage if available
      const savedProgress = localStorage.getItem(`course-${courseId}-progress`)

      if (savedProgress) {
        const { course, lessons } = JSON.parse(savedProgress)
        this.course = course
        this.lessons = lessons
        this.currentLessonId = lessons.find(l => !l.completed)?.id || lessons[0].id
      } else {
        this.course = {
          id: courseId,
          title: 'Home Gardening Safety',
          progress: 0
        }
        this.currentLessonId = this.lessons[0].id
      }
    },
    selectLesson(lessonId) {
      this.currentLessonId = lessonId
    },
    goToNextLesson() {
      const index = this.lessons.findIndex(l => l.id === this.currentLessonId)
      if (index < this.lessons.length - 1) {
        this.currentLessonId = this.lessons[index + 1].id
        this.markLessonCompleted(this.currentLessonId)
      }
    },
    goToPreviousLesson() {
      const index = this.lessons.findIndex(l => l.id === this.currentLessonId)
      if (index > 0) {
        this.currentLessonId = this.lessons[index - 1].id
      }
    },
    markLessonCompleted(lessonId) {
      const lesson = this.lessons.find(l => l.id === lessonId)
      if (lesson && !lesson.completed) {
        lesson.completed = true
        this.updateCourseProgress()
        this.saveProgress()
      }
    },
    updateCourseProgress() {
      const completedCount = this.lessons.filter(l => l.completed).length
      this.course.progress = Math.round((completedCount / this.lessons.length) * 100)
    },
    saveProgress() {
      localStorage.setItem(`course-${this.course.id}-progress`, JSON.stringify({
        course: this.course,
        lessons: this.lessons
      }))
    },
    completeCourse() {
  // 1. Mark the current lesson as completed
  this.markLessonCompleted(this.currentLessonId);

  // 2. Update course progress to 100%
  this.course.progress = 100;
  this.course.status = "Complete";

  // 3. Save the updated progress to localStorage
  this.saveProgress();

  // 4. Show success notification
  this.$notify({
    title: 'Congratulations!',
    message: 'You have successfully completed the course!',
    type: 'success',
    duration: 3000 // Show for 3 seconds
  });

  // 5. Redirect to the courses page after a short delay
  setTimeout(() => {
    this.$router.push('/course/courses');
  }, 1000);
}
  }
}
</script>

<style scoped>
/* Dashboard layout */
.dashboard-container {
  display: flex;
  min-height: 100vh;
}

.dashboard-content {
  flex: 1;
  padding: 2rem;
  background: #f8fafc;
}

/* Course learning container */
.course-learning-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

/* Course header */
.course-header {
  padding: 1.5rem 2rem;
  border-bottom: 1px solid #e2e8f0;
  background: linear-gradient(135deg, #f7fafc, #edf2f7);
}

.header-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.back-button {
  background: white;
  border: 1px solid #cbd5e0;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.back-button:hover {
  background: #edf2f7;
  border-color: #a0aec0;
}

.progress-container {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.progress-text {
  font-size: 0.9rem;
  color: #4a5568;
  margin-bottom: 0.25rem;
}

.progress-bar {
  width: 200px;
  height: 8px;
  background: #e2e8f0;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #4299e1, #48bb78);
  transition: width 0.5s ease;
}

.course-header h1 {
  margin: 0.5rem 0;
  font-size: 1.75rem;
  color: #2d3748;
}

.course-meta {
  display: flex;
  gap: 1.5rem;
  margin-top: 0.5rem;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  color: #4a5568;
}

.meta-item i {
  color: #718096;
}

/* Main content layout */
.course-main-content {
  display: flex;
  min-height: 600px;
}

/* Lessons sidebar */
.lessons-sidebar {
  width: 320px;
  border-right: 1px solid #e2e8f0;
  background: #f8fafc;
}

.sidebar-header {
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sidebar-header h3 {
  margin: 0;
  font-size: 1.1rem;
  color: #2d3748;
}

.completion-status {
  background: #e6fffa;
  color: #38b2ac;
  padding: 0.25rem 0.75rem;
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
  padding: 0.75rem 1rem;
  border-radius: 8px;
  margin-bottom: 0.5rem;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid #e2e8f0;
  background: white;
}

.lesson-item:hover {
  background: #ebf8ff;
  border-color: #bee3f8;
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
  width: 28px;
  height: 28px;
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

/* Lesson content area */
.lesson-content-area {
  flex: 1;
  padding: 2rem;
}

.lesson-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.lesson-header h2 {
  margin: 0;
  font-size: 1.5rem;
  color: #2d3748;
}

.lesson-duration {
  background: #ebf8ff;
  color: #2b6cb0;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.video-container {
  margin: 1.5rem 0;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.video-wrapper {
  position: relative;
  padding-bottom: 56.25%; /* 16:9 aspect ratio */
  height: 0;
  overflow: hidden;
}

.video-wrapper iframe {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.lesson-text {
  line-height: 1.7;
  color: #4a5568;
  margin: 2rem 0;
}

.lesson-text >>> h3 {
  color: #2d3748;
  margin-top: 1.5rem;
  margin-bottom: 1rem;
}

.lesson-text >>> ul {
  padding-left: 1.5rem;
  margin: 1rem 0;
}

.lesson-text >>> li {
  margin-bottom: 0.5rem;
}

/* Lesson actions */
.lesson-actions {
  display: flex;
  justify-content: space-between;
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e2e8f0;
}

.prev-button, .next-button, .complete-button {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.95rem;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.prev-button {
  background: #f7fafc;
  color: #4a5568;
  border: 1px solid #cbd5e0;
}

.prev-button:hover {
  background: #edf2f7;
}

.next-button {
  background: #4299e1;
  color: white;
}

.next-button:hover {
  background: #3182ce;
}

.complete-button {
  background: #48bb78;
  color: white;
}

.complete-button:hover {
  background: #38a169;
}

/* Responsive design */
@media (max-width: 1024px) {
  .course-main-content {
    flex-direction: column;
  }

  .lessons-sidebar {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid #e2e8f0;
  }

  .lessons-list {
    max-height: none;
  }
}

@media (max-width: 768px) {
  .dashboard-content {
    padding: 1rem;
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

  .lesson-actions {
    flex-direction: column;
    gap: 0.75rem;
  }

  .prev-button, .next-button, .complete-button {
    width: 100%;
    justify-content: center;
  }

  .lesson-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
}
</style>