<template>
  <div class="course-detail-page" v-if="course">
    <!-- Header Section -->
    <div
      class="course-header-image"
      :style="{
        backgroundImage: `linear-gradient(rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.5)), url(${course.image})`
      }"
    >
      <div class="course-header-content">
        <div class="header-top">
          <button class="back-button" @click="$router.go(-1)">
            <i class="fas fa-arrow-left"></i> Back to Courses
          </button>

          <div class="enrollment-info">
            <div class="avatars-group">
              <img
                v-for="(user, idx) in enrolledUsers"
                :key="idx"
                :src="user.avatar"
                alt="avatar"
                class="avatar"
              />
            </div>
            <span class="enrolled-count">+{{ additionalEnrolledCount }} enrolled</span>
          </div>
        </div>

        <div class="header-main">
          <div class="course-meta">
            <span class="course-category">{{ course.category }}</span>
            <span class="course-duration"><i class="far fa-clock"></i> {{ formattedDuration }}</span>
            <span class="course-level"><i class="fas fa-signal"></i> {{ course.level || 'Beginner' }}</span>
          </div>

          <h1 class="course-title">{{ course.title }}</h1>

          <div class="course-rating">
            <div class="stars">
              <i v-for="star in 5" :key="star"
                 :class="star <= 4.7 ? (star === 5 && 4.7 % 1 > 0 ? 'fas fa-star-half-alt' : 'fas fa-star') : 'far fa-star'"
                 class="star"></i>
            </div>
            <span>4.7 (1,245 reviews)</span>
          </div>

          <p class="course-excerpt">{{ course.excerpt || 'Master the fundamentals with this comprehensive course' }}</p>

          <div class="course-actions">
            <button
              class="status-button"
              :class="course.status.toLowerCase().replace(/\s+/g, '-')"
            >
              {{ course.status }}
            </button>
            <button class="share-button">
              <i class="fas fa-share-alt"></i> Share
            </button>
            <button class="wishlist-button">
              <i class="far fa-bookmark"></i> Save
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div class="course-container">
      <div class="course-main-content">
        <div class="course-tabs">
          <button class="tab-button active">Overview</button>
          <button class="tab-button">Curriculum</button>
          <button class="tab-button">Reviews</button>
          <button class="tab-button">Instructor</button>
        </div>

        <div class="course-description">
          <h2>About This Course</h2>
          <p>{{ course.description }}</p>

          <div class="learning-objectives">
            <h3>What You'll Learn</h3>
            <ul>
              <li v-for="(objective, index) in learningObjectives" :key="index">
                <i class="fas fa-check"></i> {{ objective }}
              </li>
            </ul>
          </div>

          <div class="course-requirements">
            <h3>Requirements</h3>
            <ul>
              <li><i class="fas fa-circle"></i> Basic understanding of gardening concepts</li>
              <li><i class="fas fa-circle"></i> Access to outdoor space or garden</li>
              <li><i class="fas fa-circle"></i> Willingness to learn and practice</li>
            </ul>
          </div>
        </div>
      </div>

      <div class="course-sidebar">
        <div class="course-card">
          <div class="course-preview">
            <img :src="course.image" :alt="course.title" />
          </div>

          <div class="course-includes">
            <h3>This Course Includes</h3>
            <ul>
              <li><i class="fas fa-video"></i> {{ course.lessonsCount }} on-demand videos</li>
              <li><i class="fas fa-file-alt"></i> 5 articles and resources</li>
              <li v-if="hasQuiz"><i class="fas fa-question-circle"></i> Final quiz</li>
              <li><i class="fas fa-infinity"></i> Full lifetime access</li>
              <li><i class="fas fa-certificate"></i> Certificate of completion</li>
            </ul>

            <div class="price-container" v-if="!enrolled">
              <div class="price">$49.99</div>
              <div class="original-price">$89.99</div>
              <div class="discount">44% off</div>
            </div>

            <div class="progress-container" v-if="enrolled">
              <div class="progress-info">
                <span>Your Progress</span>
                <span>{{ course.progress }}%</span>
              </div>
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: course.progress + '%' }"></div>
              </div>
            </div>

            <!-- Quiz Status Section -->
            <div v-if="hasQuiz && enrolled" class="quiz-status-section">
              <h4>Quiz Status</h4>
              <div v-if="course.progress === 100">
                <p v-if="quizAttempt && quizAttempt.passed" class="quiz-passed">
                  <i class="fas fa-check-circle"></i> Passed with {{ quizAttempt.score }}%
                </p>
                <p v-else-if="quizAttempt" class="quiz-failed">
                  <i class="fas fa-times-circle"></i> Score: {{ quizAttempt.score }}%
                </p>
                <p v-else class="quiz-not-taken">
                  <i class="fas fa-exclamation-circle"></i> Not attempted yet
                </p>

                <button
                  @click="startQuiz"
                  class="quiz-action-btn"
                  :class="{ 'retake-btn': quizAttempt }"
                >
                  {{ quizAttempt ? 'Retake Quiz' : 'Take Quiz Now' }}
                </button>
              </div>
              <div v-else class="quiz-locked">
                <p><i class="fas fa-lock"></i> Complete all lessons to unlock</p>
              </div>
            </div>

            <button
              @click="handleEnrollClick"
              class="enroll-btn"
              :disabled="enrolling"
              :class="{ 'enrolled': enrolled }"
            >
              {{ enrolled ? 'Continue Learning' : enrolling ? 'Enrolling...' : 'Enroll Now' }}
              <i class="fas" :class="enrolled ? 'fa-play-circle' : 'fa-arrow-right'"></i>
            </button>

            <div class="money-back-guarantee">
              <i class="fas fa-shield-alt"></i>
              <span>30-day money-back guarantee</span>
            </div>
          </div>
        </div>

        <div class="instructor-card">
          <h3>Instructor</h3>
          <div class="instructor-info">
            <img src="https://randomuser.me/api/portraits/men/32.jpg" alt="Instructor" class="instructor-avatar" />
            <div class="instructor-details">
              <h4>Dr. James Greenfield</h4>
              <p>Master Gardener & Botanist</p>
              <div class="instructor-stats">
                <div class="stat">
                  <i class="fas fa-star"></i>
                  <span>4.8 Instructor Rating</span>
                </div>
                <div class="stat">
                  <i class="fas fa-users"></i>
                  <span>12,456 Students</span>
                </div>
                <div class="stat">
                  <i class="fas fa-play-circle"></i>
                  <span>8 Courses</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <login-modal
      ref="loginModal"
      @login-success="startCourse"
    />
  </div>
</template>

<script>
import axios from 'axios';
import LoginModal from './courselogin.vue';

export default {
  layout: 'dashboard',
  props: ['id'],
  components: {
    LoginModal,
  },
  data() {
    return {
      course: null,
      enrolled: false,
      enrolling: false,
      enrollmentId: null,
      hasQuiz: false,
      quizAttempt: null,
      currentUser: { id: 5, username: 'testuser' }, // Replace with actual user
      enrolledUsers: [
        { avatar: 'https://randomuser.me/api/portraits/women/44.jpg' },
        { avatar: 'https://randomuser.me/api/portraits/men/22.jpg' },
        { avatar: 'https://randomuser.me/api/portraits/women/68.jpg' }
      ],
      learningObjectives: [
        'Understand gardening safety fundamentals',
        'Identify potential hazards in your garden',
        'Proper use of gardening tools',
        'First aid for common gardening injuries',
        'Creating a safe garden environment for children',
        'Sustainable and eco-friendly gardening practices'
      ]
    };
  },
  computed: {
    additionalEnrolledCount() {
      return 19;
    },
    formattedDuration() {
      if (!this.course || !this.course.duration) return '';
      let durationMs = Number(this.course.duration);
      if (durationMs < 1000 * 60) {
        durationMs *= 1000;
      }
      const totalMinutes = Math.floor(durationMs / (1000 * 60));
      const hours = Math.floor(totalMinutes / 60);
      const minutes = totalMinutes % 60;
      return `${hours}h ${minutes}m`;
    },
  },
  async created() {
    await this.fetchCourse();
    await this.checkEnrollmentStatus();
    await this.fetchCourseProgress();
    await this.checkQuizStatus();
  },

  watch: {
    id(newId, oldId) {
      if (newId !== oldId) {
        this.fetchCourse();
        this.checkEnrollmentStatus();
        this.fetchCourseProgress();
      }
    },
  },
  methods: {
    async fetchCourse() {
      try {
        const response = await axios.get(`http://localhost/api/teople1/courses/${this.id}/`);
        const courseData = response.data.course || response.data;

        this.course = {
          id: courseData.id,
          title: courseData.title || "Untitled Course",
          description: courseData.description || "No description available.",
          image: courseData.image_url || "/images/default-course.jpg",
          category: courseData.category || "General",
          progress: 0,
          status: "Not Started",
          lessonsCount: courseData.Lessons ? courseData.Lessons.length : 0,
          level: courseData.level || "Beginner",
          excerpt: courseData.excerpt || "Master the fundamentals with this comprehensive course"
        };

      } catch (error) {
        console.error("Error fetching course:", error);
        this.$notify({
          type: 'error',
          title: 'Course Load Failed',
          text: 'Could not load course details. Please try again.'
        });
      }
    },

    async checkQuizStatus() {
      try {
        // Check if course has a quiz
        const quizRes = await axios.get(`http://localhost/api/teople1/quizzes/?course_id=${this.id}`);
        this.hasQuiz = quizRes.data.count > 0 && quizRes.data.quizzes.some(q => q.is_active);

        if (this.hasQuiz && this.enrolled) {
          const quiz = quizRes.data.quizzes.find(q => q.course.some(c => c.id === this.course.id));
          const quizId = quiz.id;

          // Check if user has attempted the quiz
          const attemptRes = await axios.get('http://localhost/api/teople1/quiz_attempts/', {
            params: {
              user_id: this.currentUser.id,
              quiz_id: quizId,
              _sort: '-created_on',
              _limit: 1
            }
          });

          if (attemptRes.data.count > 0) {
            const attempt = attemptRes.data.quiz_attempts[0];
            this.quizAttempt = {
              score: attempt.total_points > 0
                ? Math.round((attempt.score / attempt.total_points) * 100)
                : 0,
              passed: attempt.passed,
              date: new Date(attempt.completed_at).toLocaleDateString()
            };
          }
        }
      } catch (error) {
        console.error('Error checking quiz status:', error);
        this.hasQuiz = false;
      }
    },

    startQuiz() {
      if (!this.enrolled) {
        this.handleEnrollClick();
        return;
      }

      this.$router.push({
        name: 'course-quiz',
        params: { id: this.id }
      });
    },

    async checkEnrollmentStatus() {
      if (!this.course || !this.currentUser) return;

      try {
        const response = await axios.get('http://localhost/api/teople1/enrollments/', {
          params: {
            user_id: this.currentUser.id,
            course_id: this.course.id
          }
        });

        if (response.data.status === 'success') {
          // Find the most recent enrollment for this user/course
          const enrollment = response.data.enrollments
            .filter(e =>
              e.user.some(u => u.id === this.currentUser.id) &&
              e.course.some(c => c.id === this.course.id)
            )
            .sort((a, b) => new Date(b.created_on) - new Date(a.created_on))[0];

          this.enrolled = !!enrollment;
          this.enrollmentId = enrollment?.id || null;

          // Update course status if enrollment exists
          if (enrollment?.completion_status) {
            this.course.status = enrollment.completion_status.value || "Enrolled";
            if (enrollment.progress_percentage) {
              this.course.progress = enrollment.progress_percentage;
            }
          }
        }
      } catch (error) {
        console.error('Error checking enrollment:', error);
        this.enrolled = false;
        this.enrollmentId = null;
      }
    },

    async fetchCourseProgress() {
      if (!this.course || !this.currentUser || !this.enrolled) return;

      try {
        const res = await axios.get('http://localhost/api/teople1/progress/', {
          params: {
            user_id: this.currentUser.id,
            course_id: this.course.id
          }
        });

        if (res.data.status === 'success') {
          // Calculate overall progress
          const courseProgressRecords = res.data.progress.filter(
            p => p.course.some(c => c.id === this.course.id)
          );

          if (courseProgressRecords.length > 0) {
            // Count completed lessons
            const completedLessons = courseProgressRecords
              .filter(p => p.completed)
              .flatMap(p => p.lesson)
              .filter((lesson, index, self) =>
                self.findIndex(l => l.id === lesson.id) === index
              ).length;

            const totalLessons = this.course.lessonsCount || 1; // Avoid division by zero
            const progressPercentage = Math.round((completedLessons / totalLessons) * 100);

            // Update course progress
            this.course.progress = progressPercentage;

            // Update status based on progress
            if (progressPercentage >= 100) {
              this.course.status = "Completed";
            } else if (progressPercentage > 0) {
              this.course.status = "In Progress";
            }

            // Update enrollment record if needed
            if (this.enrollmentId && progressPercentage !== this.course.progress) {
              await this.updateEnrollmentProgress(progressPercentage);
            }
          }
        }
      } catch (error) {
        console.error('Error fetching progress:', error);
        // Don't reset progress on error - use existing values
      }
    },

    async updateEnrollmentProgress(progress) {
      try {
        await axios.patch(
          `http://localhost/api/teople1/enrollments/${this.enrollmentId}/`,
          {
            progress_percentage: progress,
            updated_on: new Date().toISOString()
          }
        );
      } catch (error) {
        console.error('Failed to update enrollment progress:', error);
      }
    },

    async handleEnrollClick() {
      if (this.enrolling) return;

      if (this.enrolled) {
        // Already enrolled - go to learning page
        this.$router.push({
          name: 'course-learn',
          params: { id: this.course.id }
        });
        return;
      }

      // New enrollment
      this.enrolling = true;

      try {
        // Create new enrollment with the correct structure
        const payload = {
          course: this.course.id,
          user: this.currentUser.id,
          status: "active",
          enrollment_date: new Date().toISOString().split('T')[0], // YYYY-MM-DD format
          completion_percentage: 0
        };

        const response = await axios.post(
          'http://localhost/api/teople1/enrollments/',
          payload
        );

        if (response.status === 201 || response.data.status === 'success') {
          this.enrolled = true;
          this.enrollmentId = response.data.id || response.data.enrollment?.id || null;

          // Create initial progress records for each lesson
          if (this.course.lessonsCount > 0) {
            await this.createInitialProgressRecords();
          }

          // Refresh data
          await Promise.all([
            this.fetchCourseProgress(),
            this.checkEnrollmentStatus()
          ]);

          // Redirect to learning page
          this.$router.push({
            name: 'course-learn',
            params: { id: this.course.id }
          });

          this.$notify({
            type: 'success',
            title: 'Enrollment Successful',
            text: `You've been enrolled in ${this.course.title}`
          });
        } else {
          throw new Error(response.data.message || 'Enrollment failed');
        }
      } catch (error) {
        console.error('Enrollment failed:', error);

        if (error.response?.status === 401) {
          this.$refs.loginModal.show();
          return;
        }

        this.$notify({
          type: 'error',
          title: 'Enrollment Failed',
          text: error.response?.data?.message || 'Could not enroll. Please try again.'
        });
      } finally {
        this.enrolling = false;
      }
    },

    async createInitialProgressRecords() {
      try {
        // Fetch course lessons
        const lessonsRes = await axios.get(`http://localhost/api/teople1/lessons/?course_id=${this.course.id}`);

        if (lessonsRes.data.status === 'success' && lessonsRes.data.lessons.length > 0) {
          // Create progress record for each lesson
          for (const lesson of lessonsRes.data.lessons) {
            const progressPayload = {
              course: [this.course.id],
              user: [this.currentUser.id],
              lesson: [lesson.id],
              completed: false,
              time_spent: 0,
              notes: ""
            };

            await axios.post('http://localhost/api/teople1/progress/', progressPayload);
          }
        }
      } catch (error) {
        console.error('Error creating initial progress records:', error);
      }
    },

    startCourse() {
      this.enrolled = true;
      this.$router.push({
        name: 'course-learn',
        params: { id: this.course.id },
      });
    },
  },
};
</script>

<style scoped>
@import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css');
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

.course-detail-page {
  font-family: 'Poppins', sans-serif;
  background: #f9fafb;
  color: #333;
  line-height: 1.6;
}

.course-header-image {
  position: relative;
  height: 500px;
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  color: white;
  padding: 0;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.course-header-content {
  padding: 40px 5% 60px;
  background: linear-gradient(transparent, rgba(0,0,0,0.8));
  width: 100%;
}

.header-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  flex-wrap: wrap;
  gap: 15px;
}

.back-button {
  background: rgba(255,255,255,0.2);
  border: none;
  color: white;
  padding: 10px 20px;
  border-radius: 30px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 8px;
  backdrop-filter: blur(5px);
}

.back-button:hover {
  background: rgba(255,255,255,0.3);
  transform: translateY(-2px);
}

.enrollment-info {
  display: flex;
  align-items: center;
  gap: 15px;
}

.avatars-group {
  display: flex;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 2px solid white;
  margin-left: -10px;
  object-fit: cover;
}

.avatar:first-child {
  margin-left: 0;
}

.enrolled-count {
  font-size: 14px;
  opacity: 0.9;
}

.header-main {
  max-width: 800px;
}

.course-meta {
  display: flex;
  gap: 15px;
  margin-bottom: 15px;
  flex-wrap: wrap;
}

.course-category, .course-duration, .course-level {
  background: rgba(255,255,255,0.2);
  padding: 6px 15px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 5px;
  backdrop-filter: blur(5px);
}

.course-title {
  font-size: 2.8rem;
  font-weight: 800;
  margin: 0 0 15px 0;
  line-height: 1.2;
  text-shadow: 0 2px 4px rgba(0,0,0,0.5);
}

.course-excerpt {
  font-size: 1.1rem;
  opacity: 0.9;
  margin-bottom: 25px;
  max-width: 600px;
}

.course-rating {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 15px;
}

.stars {
  display: flex;
  gap: 2px;
}

.star {
  color: #f1c40f;
  font-size: 16px;
}

.course-rating span {
  font-size: 16px;
  opacity: 0.9;
}

.course-actions {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
}

.status-button, .share-button, .wishlist-button {
  border: none;
  padding: 12px 25px;
  font-weight: 600;
  border-radius: 30px;
  font-size: 15px;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-button.complete {
  background: linear-gradient(135deg, #2ecc71, #27ae60);
  color: white;
}

.status-button.start-course {
  background: linear-gradient(135deg, #f39c12, #e67e22);
  color: white;
}

.share-button, .wishlist-button {
  background: rgba(255,255,255,0.2);
  color: white;
  backdrop-filter: blur(5px);
}

.share-button:hover, .wishlist-button:hover {
  background: rgba(255,255,255,0.3);
  transform: translateY(-2px);
}

.course-container {
  display: flex;
  max-width: 1200px;
  margin: -40px auto 0;
  padding: 0 20px 40px;
  gap: 30px;
}

.course-main-content {
  flex: 1;
  background: white;
  border-radius: 12px;
  box-shadow: 0 5px 20px rgba(0,0,0,0.08);
  padding: 30px;
  margin-top: 20px;
}

.course-tabs {
  display: flex;
  border-bottom: 1px solid #eee;
  margin-bottom: 30px;
  overflow-x: auto;
  scrollbar-width: none;
}

.course-tabs::-webkit-scrollbar {
  display: none;
}

.tab-button {
  padding: 12px 25px;
  background: none;
  border: none;
  font-weight: 600;
  color: #7f8c8d;
  cursor: pointer;
  position: relative;
  white-space: nowrap;
  flex-shrink: 0;
}

.tab-button.active {
  color: #3498db;
}

.tab-button.active::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  width: 100%;
  height: 3px;
  background: #3498db;
  border-radius: 3px 3px 0 0;
}

.course-description h2 {
  font-size: 24px;
  margin: 0 0 20px 0;
  color: #2c3e50;
}

.course-description p {
  font-size: 16px;
  line-height: 1.8;
  color: #34495e;
  margin-bottom: 30px;
}

.learning-objectives, .course-requirements {
  background: #f8f9fa;
  border-radius: 10px;
  padding: 25px;
  margin-top: 30px;
}

.learning-objectives h3, .course-requirements h3 {
  font-size: 20px;
  margin: 0 0 15px 0;
  color: #2c3e50;
}

.learning-objectives ul, .course-requirements ul {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 15px;
}

.learning-objectives li, .course-requirements li {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  font-size: 15px;
  color: #34495e;
}

.learning-objectives i {
  color: #2ecc71;
  margin-top: 3px;
}

.course-requirements i {
  color: #3498db;
  font-size: 8px;
  margin-top: 8px;
}

.course-sidebar {
  width: 350px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.course-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 5px 20px rgba(0,0,0,0.08);
  overflow: hidden;
}

.course-preview {
  height: 200px;
  overflow: hidden;
}

.course-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.course-includes {
  padding: 25px;
}

.course-includes h3 {
  font-size: 20px;
  margin: 0 0 20px 0;
  color: #2c3e50;
}

.course-includes ul {
  list-style: none;
  padding: 0;
  margin: 0 0 25px 0;
}

.course-includes li {
  padding: 12px 0;
  border-bottom: 1px solid #eee;
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 15px;
  color: #34495e;
}

.course-includes li:last-child {
  border-bottom: none;
}

.course-includes i {
  color: #00568f;
  width: 20px;
  text-align: center;
}

.price-container {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
}

.price {
  font-size: 28px;
  font-weight: 700;
  color: #2c3e50;
}

.original-price {
  font-size: 18px;
  text-decoration: line-through;
  color: #7f8c8d;
}

.discount {
  background: #e74c3c;
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.progress-container {
  margin: 25px 0;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 14px;
  color: #34495e;
}

.progress-bar {
  height: 8px;
  background: #ecf0f1;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 4px;
  background: linear-gradient(90deg, #3498db, #2ecc71);
  transition: width 0.5s ease;
}

/* Quiz Status Styles */
.quiz-status-section {
  margin: 20px 0;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
}

.quiz-status-section h4 {
  margin-bottom: 10px;
  color: #343a40;
}

.quiz-passed {
  color: #28a745;
}

.quiz-failed {
  color: #dc3545;
}

.quiz-not-taken, .quiz-locked {
  color: #6c757d;
}

.quiz-status-section i {
  margin-right: 8px;
}

.quiz-action-btn {
  width: 100%;
  margin-top: 10px;
  padding: 10px 16px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.3s;
  font-weight: 600;
}

.quiz-action-btn:hover {
  background: #0069d9;
  transform: translateY(-2px);
}

.retake-btn {
  background: #6c757d;
}

.retake-btn:hover {
  background: #5a6268;
}

.quiz-locked {
  font-size: 0.9rem;
  text-align: center;
  padding: 5px;
}

.enroll-btn {
  width: 100%;
  padding: 16px;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.3s;
  background: linear-gradient(135deg, #00568f, #2980b9);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin-bottom: 15px;
}

.enroll-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(52, 152, 219, 0.3);
}

.enroll-btn.enrolled {
  background: linear-gradient(135deg, #2ecc71, #27ae60);
}

.enroll-btn.enrolled:hover {
  box-shadow: 0 8px 20px rgba(46, 204, 113, 0.3);
}

.enroll-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
}

.money-back-guarantee {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 14px;
  color: #7f8c8d;
}

.money-back-guarantee i {
  color: #3498db;
}

.instructor-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 5px 20px rgba(0,0,0,0.08);
  padding: 25px;
}

.instructor-card h3 {
  font-size: 20px;
  margin: 0 0 20px 0;
  color: #2c3e50;
}

.instructor-info {
  display: flex;
  gap: 15px;
}

.instructor-avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  object-fit: cover;
}

.instructor-details h4 {
  font-size: 18px;
  margin: 0 0 5px 0;
  color: #2c3e50;
}

.instructor-details p {
  color: #7f8c8d;
  margin-bottom: 15px;
}

.instructor-stats {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.stat {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #34495e;
}

.stat i {
  color: #00568f;
  width: 16px;
}

/* Responsive Design */
@media (max-width: 992px) {
  .course-container {
    flex-direction: column;
  }

  .course-sidebar {
    width: 100%;
  }

  .learning-objectives ul {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .course-header-image {
    height: 450px;
  }

  .course-title {
    font-size: 2rem;
  }

  .header-top {
    flex-direction: column;
    align-items: flex-start;
  }

  .enrollment-info {
    width: 100%;
    justify-content: flex-end;
  }

  .course-actions {
    flex-direction: column;
    align-items: flex-start;
  }

  .course-meta {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
}

@media (max-width: 576px) {
  .course-header-content {
    padding: 20px 5% 40px;
  }

  .course-header-image {
    height: 400px;
  }

  .course-title {
    font-size: 1.8rem;
  }

  .course-main-content {
    padding: 20px;
  }

  .course-tabs {
    overflow-x: auto;
  }

  .tab-button {
    padding: 10px 15px;
    font-size: 14px;
  }

  .instructor-info {
    flex-direction: column;
    text-align: center;
  }

  .instructor-stats {
    align-items: center;
  }
}

/* Animation for better UX */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.course-card, .course-main-content, .instructor-card {
  animation: fadeIn 0.5s ease-out;
}

/* Loading state for buttons */
.enroll-btn:disabled::after {
  content: '';
  width: 16px;
  height: 16px;
  border: 2px solid transparent;
  border-top: 2px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-left: 8px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>