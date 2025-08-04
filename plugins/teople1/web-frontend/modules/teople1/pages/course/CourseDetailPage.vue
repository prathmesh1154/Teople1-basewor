<template>
  <div class="course-detail-page">
    <div
      class="course-header-image"
      :style="{ backgroundImage: `linear-gradient(rgba(0, 0, 0, 0.6), rgba(0, 0, 0, 0.6)), url(${course.image})` }"
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
            <span class="course-category">Lifestyle</span>
            <span class="course-duration"><i class="far fa-clock"></i> 3h 45m</span>
          </div>

          <h1 class="course-title">{{ course.title }}</h1>

          <div class="course-rating">
            <i class="fas fa-star"></i>
            <i class="fas fa-star"></i>
            <i class="fas fa-star"></i>
            <i class="fas fa-star"></i>
            <i class="fas fa-star-half-alt"></i>
            <span>4.7 (1,245 reviews)</span>
          </div>

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
          </div>
        </div>
      </div>
    </div>

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
              <li><i class="fas fa-check"></i> Understand gardening safety fundamentals</li>
              <li><i class="fas fa-check"></i> Identify potential hazards in your garden</li>
              <li><i class="fas fa-check"></i> Proper use of gardening tools</li>
              <li><i class="fas fa-check"></i> First aid for common gardening injuries</li>
            </ul>
          </div>
        </div>
      </div>

      <div class="course-sidebar">
        <div class="course-includes">
          <h3>Course Includes</h3>
          <ul>
            <li><i class="fas fa-video"></i> {{ course.lessons }} on-demand videos</li>
            <li><i class="fas fa-file-alt"></i> {{ course.topics }} articles</li>
            <li><i class="fas fa-question-circle"></i> {{ course.quiz }} practice quizzes</li>
            <li><i class="fas fa-certificate"></i> Certificate of completion</li>
            <li><i class="fas fa-mobile-alt"></i> Access on mobile and TV</li>
          </ul>

          <div class="progress-container">
            <div class="progress-info">
              <span>Your Progress</span>
              <span>{{ course.progress }}%</span>
            </div>
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: course.progress + '%' }"></div>
            </div>
          </div>

          <button @click="toggleEnrollment" class="enroll-btn">
            {{ enrolled ? 'Continue Learning' : 'Enroll Now' }}
            <i class="fas fa-arrow-right"></i>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
 layout: 'dashboard',
  props: ['id'],
  data() {
    return {
      course: null,
      enrolled: false,
      enrolledUsers: [
        { avatar: 'https://randomuser.me/api/portraits/women/1.jpg' },
        { avatar: 'https://randomuser.me/api/portraits/men/2.jpg' },
        { avatar: 'https://randomuser.me/api/portraits/women/3.jpg' },
      ],
    };
  },
  computed: {
    additionalEnrolledCount() {
      return 19;
    },
  },
  created() {
    this.fetchCourse();
  },
  methods: {
    fetchCourse() {
     const allCourses = [
  {
    id: 1,
    title: "Home Gardening Safety",
    lessons: 3,
    topics: 4,
    quiz: 1,
    description: "Gardening can be a fulfilling hobby, but...",
    progress: 100,
    status: "Complete",
    image: "https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=800&q=60",
  },
  {
    id: 2,
    title: "Get Cash for Your Annuity",
    lessons: 2,
    topics: 3,
    quiz: 1,
    description: "Learn how to get cash for your annuity...",
    progress: 0,
    status: "Start Course",
    image: "https://images.unsplash.com/photo-1515377905703-c4788e51af15?auto=format&fit=crop&w=800&q=60",
  },
  {
    id: 3,
    title: "Concepts of Computer Engineering",
    lessons: 3,
    topics: 5,
    quiz: 2,
    description: "An introduction to the fundamentals of computer engineering...",
    progress: 100,
    status: "Complete",
    image: "https://images.unsplash.com/photo-1519389950473-47ba0277781c?auto=format&fit=crop&w=800&q=60",
  },
  {
    id: 4,
    title: "The American Frontier",
    lessons: 5,
    topics: 6,
    quiz: 2,
    description: "Explore American history and the settling of the frontier...",
    progress: 0,
    status: "Start Course",
    image: "https://images.unsplash.com/photo-1500534623283-312aade485b7?auto=format&fit=crop&w=800&q=60",
  },
  {
    id: 5,
    title: "Cybersecurity Standards",
    lessons: 5,
    topics: 7,
    quiz: 2,
    description: "Understand the basics of cybersecurity practices and standards...",
    progress: 100,
    status: "Complete",
    image: "https://images.unsplash.com/photo-1504384308090-c894fdcc538d?auto=format&fit=crop&w=800&q=60",
  },
  {
    id: 6,
    title: "How to Fundraise",
    lessons: 4,
    topics: 2,
    quiz: 1,
    description: "Master modern fundraising strategies and campaigns...",
    progress: 0,
    status: "Start Course",
    image: "https://images.unsplash.com/photo-1504384308090-c894fdcc538d?auto=format&fit=crop&w=800&q=60",
  },
];


     this.course = allCourses.find((c) => c.id === parseInt(this.id, 10));
console.log("this.course",  this.course)
      if (!this.course) {
        this.course = {
          title: "Course Not Found",
          lessons: 0,
          topics: 0,
          quiz: 0,
          description: "The course you are looking for does not exist.",
          progress: 0,
          status: "N/A",
          image: "",
        };
      }
    },
    toggleEnrollment() {
      this.enrolled = !this.enrolled;
    },
  },
};
</script>

<style scoped>
@import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css');
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

.course-detail-page {
  font-family: 'Poppins', sans-serif;
  background: #f9fafb;
}

.course-header-image {
  position: relative;
  height: 450px;
  background-size: cover;
  background-position: center;
  color: white;
  padding: 0;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
}

.course-header-content {
  padding: 40px 5% 60px;
  background: linear-gradient(transparent, rgba(0,0,0,0.8));
}

.header-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
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
}

.back-button:hover {
  background: rgba(255,255,255,0.3);
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
}

.course-category, .course-duration {
  background: rgba(255,255,255,0.2);
  padding: 6px 15px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 5px;
}

.course-title {
  font-size: 42px;
  font-weight: 700;
  margin: 0 0 15px 0;
  line-height: 1.3;
}

.course-rating {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 25px;
}

.course-rating i {
  color: #f1c40f;
  font-size: 18px;
}

.course-rating span {
  font-size: 16px;
  opacity: 0.9;
}

.course-actions {
  display: flex;
  gap: 15px;
}

.status-button, .share-button {
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

.share-button {
  background: rgba(255,255,255,0.2);
  color: white;
}

.share-button:hover {
  background: rgba(255,255,255,0.3);
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
  padding: 60px 30px 30px 30px;
}

.course-tabs {
  display: flex;
  border-bottom: 1px solid #eee;
  margin-bottom: 30px;
}

.tab-button {
  padding: 12px 25px;
  background: none;
  border: none;
  font-weight: 600;
  color: #7f8c8d;
  cursor: pointer;
  position: relative;
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

.learning-objectives {
  background: #f8f9fa;
  border-radius: 10px;
  padding: 25px;
  margin-top: 30px;
}

.learning-objectives h3 {
  font-size: 20px;
  margin: 0 0 15px 0;
  color: #2c3e50;
}

.learning-objectives ul {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
}

.learning-objectives li {
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

.course-sidebar {
  width: 350px;
}

.course-includes {
  background: #e9851e;
  border-radius: 12px;
  box-shadow: 0 5px 20px rgba(0,0,0,0.08);
  padding: 25px;
  position: sticky;
  top: 20px;
}

.course-includes h3 {
  font-size: 20px;
  margin: 0 0 20px 0;
  color: #000;
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
  color: #000;
}

.course-includes li:last-child {
  border-bottom: none;
}

.course-includes i {
  color: #00568f;
  width: 20px;
  text-align: center;
}

.progress-container {
  margin: 25px 0;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 14px;
  color: #000;
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
}

.enroll-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(52, 152, 219, 0.3);
}

@media (max-width: 992px) {
  .course-container {
    flex-direction: column;
  }

  .course-sidebar {
    width: 100%;
  }
}

@media (max-width: 768px) {
  .course-header-image {
    height: 400px;
  }

  .course-title {
    font-size: 32px;
  }

  .learning-objectives ul {
    grid-template-columns: 1fr;
  }
}
</style>