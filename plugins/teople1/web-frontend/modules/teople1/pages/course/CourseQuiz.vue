<template>
  <div class="quiz-container">
    <!-- Quiz Header -->
    <div class="quiz-header">
      <div class="quiz-title-section">
        <h1>{{ quiz.title }}</h1>
        <p class="quiz-description" v-if="quiz.description">{{ quiz.description }}</p>
      </div>
      <div class="quiz-meta">
        <span class="time-remaining" v-if="timeLimit > 0 && !quizCompleted">
          <i class="fas fa-clock"></i> Time remaining: {{ formattedTime }}
        </span>
        <span class="score" v-if="showResults || quizCompleted">
          <i class="fas fa-star"></i> Score: {{ score }}/{{ totalPoints }}
        </span>
        <div class="progress-bar-container">
          <div class="progress-bar" :style="{ width: progressPercentage + '%' }"></div>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-message">
      <div class="spinner"></div>
      <p>Loading quiz...</p>
    </div>

    <!-- Quiz Results -->
    <div v-else-if="quizCompleted" class="quiz-results">
      <div class="result-card" :class="passed ? 'passed' : 'failed'">
        <div class="result-icon">
          <i class="fas" :class="passed ? 'fa-trophy' : 'fa-redo-alt'"></i>
        </div>

        <h2 v-if="passed">Congratulations!</h2>
        <h2 v-else>Quiz Complete</h2>

        <div class="result-score">
          You scored <span class="score-value">{{ score }}</span> out of <span class="score-total">{{ totalPoints }}</span>
          <span class="score-percentage">({{ percentageScore }}%)</span>
        </div>

        <div class="result-details">
          <div class="detail-item">
            <span class="detail-label">Correct Answers:</span>
            <span class="detail-value">{{ correctCount }}/{{ quiz.questions.length }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Passing Score:</span>
            <span class="detail-value">{{ quiz.passing_score }}%</span>
          </div>
          <div class="detail-item" v-if="timeLimit > 0">
            <span class="detail-label">Time Spent:</span>
            <span class="detail-value">{{ formatTimeSpent() }}</span>
          </div>
        </div>

        <div v-if="passed" class="pass-message">
          <i class="fas fa-check-circle"></i>
          <p>You passed the quiz!</p>
        </div>
        <div v-else class="fail-message">
          <i class="fas fa-times-circle"></i>
          <p>You need {{ quiz.passing_score }}% to pass. Try again?</p>
        </div>

        <div class="result-actions">
          <button @click="retakeQuiz" class="retake-btn">
            <i class="fas fa-redo"></i> Retake Quiz
          </button>
          <button @click="reviewAnswers" class="review-btn" v-if="!showingReview">
            <i class="fas fa-list-ol"></i> Review Answers
          </button>
          <button @click="exitQuiz" class="exit-btn">
            <i class="fas fa-home"></i> Back to Course
          </button>
        </div>
      </div>

      <!-- Answers Review Section -->
      <div v-if="showingReview" class="answers-review">
        <h3>Review Your Answers</h3>
        <div class="review-list">
          <div v-for="(question, index) in quiz.questions" :key="index" class="review-item">
            <div class="review-question">
              <span class="review-number">Q{{ index + 1 }}:</span>
              {{ question.question_text }}
              <span class="review-points">({{ question.points }} point{{ question.points !== 1 ? 's' : '' }})</span>
            </div>

            <div class="review-options">
              <div v-for="(option, optIndex) in question.options" :key="optIndex"
                   class="review-option"
                   :class="{
                     correct: option.is_correct,
                     selected: selectedAnswers[index]?.includes(optIndex),
                     incorrect: selectedAnswers[index]?.includes(optIndex) && !option.is_correct
                   }">
                <div class="option-indicator">
                  <i class="fas" :class="{
                    'fa-check-circle': option.is_correct,
                    'fa-times-circle': selectedAnswers[index]?.includes(optIndex) && !option.is_correct,
                    'fa-dot-circle': selectedAnswers[index]?.includes(optIndex) && option.is_correct
                  }"></i>
                </div>
                <div class="option-text">{{ option.text }}</div>
              </div>
            </div>

            <div v-if="question.explanation" class="review-explanation">
              <p><strong>Explanation:</strong> {{ question.explanation }}</p>
            </div>

            <div class="review-status" :class="isQuestionCorrect(index) ? 'correct' : 'incorrect'">
              <i class="fas" :class="isQuestionCorrect(index) ? 'fa-check' : 'fa-times'"></i>
              {{ isQuestionCorrect(index) ? 'Correct' : 'Incorrect' }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Active Question -->
    <div v-if="!quizCompleted && quiz.questions.length > 0 && quiz.questions[currentQuestionIndex]"
         class="question-container">
      <div class="question-card">
        <div class="question-header">
          <span class="question-number">
            Question {{ currentQuestionIndex + 1 }} of {{ quiz.questions.length }}
          </span>
          <span class="question-points">
            {{ quiz.questions[currentQuestionIndex].points }}
            point{{ quiz.questions[currentQuestionIndex].points !== 1 ? 's' : '' }}
          </span>
        </div>

        <h3 class="question-text">
          {{ quiz.questions[currentQuestionIndex].question_text }}
        </h3>

        <div v-if="quiz.questions[currentQuestionIndex].image" class="question-image">
          <img :src="quiz.questions[currentQuestionIndex].image"
               :alt="'Image for question ' + (currentQuestionIndex + 1)" />
        </div>

        <div class="options-container">
          <div
            v-for="(option, optIndex) in quiz.questions[currentQuestionIndex].options"
            :key="optIndex"
            class="option"
            :class="{
              selected: selectedAnswers[currentQuestionIndex]?.includes(optIndex),
              correct: showResults && option.is_correct,
              incorrect: showResults && selectedAnswers[currentQuestionIndex]?.includes(optIndex) && !option.is_correct
            }"
            @click="selectAnswer(currentQuestionIndex, optIndex, quiz.questions[currentQuestionIndex].question_type)"
          >
            <div class="option-selector">
              <span v-if="quiz.questions[currentQuestionIndex].question_type === 'single_choice'">
                <i
                  class="fas"
                  :class="{
                    'fa-check-circle': selectedAnswers[currentQuestionIndex]?.includes(optIndex),
                    'fa-circle': !selectedAnswers[currentQuestionIndex]?.includes(optIndex)
                  }"
                ></i>
              </span>
              <span v-else>
                <i
                  class="fas"
                  :class="{
                    'fa-check-square': selectedAnswers[currentQuestionIndex]?.includes(optIndex),
                    'fa-square': !selectedAnswers[currentQuestionIndex]?.includes(optIndex)
                  }"
                ></i>
              </span>
            </div>
            <div class="option-text">{{ option.text }}</div>
            <div v-if="showResults && option.is_correct" class="correct-indicator">
              <i class="fas fa-check"></i> Correct Answer
            </div>
          </div>
        </div>

        <div v-if="showResults && quiz.questions[currentQuestionIndex].explanation" class="explanation">
          <p><strong>Explanation:</strong> {{ quiz.questions[currentQuestionIndex].explanation }}</p>
        </div>
      </div>
    </div>

    <!-- Quiz Navigation -->
    <div v-if="!quizCompleted && !loading" class="quiz-navigation">
      <button
        @click="previousQuestion"
        :disabled="currentQuestionIndex === 0"
        class="nav-btn prev-btn"
      >
        <i class="fas fa-arrow-left"></i> Previous
      </button>

      <div class="progress-indicator">
        <div class="progress-dots">
          <span
            v-for="(question, index) in quiz.questions"
            :key="index"
            :class="{
              'dot': true,
              'active': index === currentQuestionIndex,
              'answered': selectedAnswers[index] && selectedAnswers[index].length > 0,
              'current': index === currentQuestionIndex
            }"
            @click="goToQuestion(index)"
          ></span>
        </div>
      </div>

      <button
        v-if="currentQuestionIndex < quiz.questions.length - 1"
        @click="nextQuestion"
        class="nav-btn next-btn"
        :disabled="!isQuestionAnswered(currentQuestionIndex)"
      >
        Next <i class="fas fa-arrow-right"></i>
      </button>

      <button
        v-else
        @click="submitQuiz"
        class="nav-btn submit-btn"
        :disabled="!allQuestionsAnswered"
      >
        Submit Quiz <i class="fas fa-paper-plane"></i>
      </button>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  layout: "dashboard",
  data() {
    return {
      quiz: {
        id: null,
        title: '',
        description: '',
        passing_score: 70,
        time_limit: 0,
        questions: []
      },
      currentQuestionIndex: 0,
      selectedAnswers: [],
      score: 0,
      totalPoints: 0,
      showResults: false,
      quizCompleted: false,
      passed: false,
      loading: true,
      timeRemaining: 0,
      timer: null,
      courseId: null,
      startTime: null,
      timeSpent: 0,
      showingReview: false,
      correctCount: 0
    };
  },
  computed: {
    percentageScore() {
      return this.totalPoints > 0 ? Math.round((this.score / this.totalPoints) * 100) : 0;
    },
    formattedTime() {
      const minutes = Math.floor(this.timeRemaining / 60);
      const seconds = this.timeRemaining % 60;
      return `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
    },
    timeLimit() {
      return this.quiz.time_limit * 60; // Convert minutes to seconds
    },
    progressPercentage() {
      return ((this.currentQuestionIndex + 1) / this.quiz.questions.length) * 100;
    },
    allQuestionsAnswered() {
      return this.selectedAnswers.every(answers => answers && answers.length > 0);
    }
  },
  async created() {
    this.courseId = this.$route.params.id;
    if (!this.courseId) {
      console.error("Course ID is missing");
      this.$router.push({ name: 'courses' });
      return;
    }
    await this.fetchQuiz();
    this.initializeQuiz();
  },
  beforeDestroy() {
    this.clearTimer();
  },
  methods: {
    async fetchQuiz() {
      try {
        // Fetch quiz for this course
        const quizResponse = await axios.get(`http://localhost/api/teople1/quizzes/?course_id=${this.courseId}`);

        if (quizResponse.data.status === 'success' && quizResponse.data.quizzes.length > 0) {
          const quizData = quizResponse.data.quizzes[0];
          this.quiz = {
            id: quizData.id,
            title: quizData.title || 'Untitled Quiz',
            description: quizData.description || '',
            passing_score: quizData.passing_score || 70,
            time_limit: quizData.time_limit || 30,
            questions: []
          };

          // Fetch questions for this quiz
          const questionIds = quizData.Questions.map(q => q.id);
          if (questionIds.length > 0) {
            const questionsResponse = await axios.get('http://localhost/api/teople1/questions/', {
              params: {
                id: `in(${questionIds.join(',')})`
              }
            });

            if (questionsResponse.data.status === 'success') {
              this.quiz.questions = questionsResponse.data.questions
                .filter(q => q.Quiz.some(quiz => quiz.id === this.quiz.id))
                .map(question => {
                  try {
                    // Parse options if they're stored as JSON string
                    let options = question.Options;
                    if (typeof options === 'string') {
                      options = JSON.parse(options);
                    }

                    return {
                      id: question.id,
                      question_text: question['Question Text'] || 'No question text',
                      question_type: question['Question Type']?.value || 'single_choice',
                      options: options || [],
                      points: 1, // Default points per question
                      explanation: question.explanation || '' // Add explanations if available in your API
                    };
                  } catch (e) {
                    console.error('Error parsing question:', question, e);
                    return {
                      id: question.id,
                      question_text: 'Invalid question format',
                      question_type: 'single_choice',
                      options: [],
                      points: 0,
                      explanation: ''
                    };
                  }
                });

              // Calculate total points
              this.totalPoints = this.quiz.questions.reduce((sum, q) => sum + q.points, 0);
            }
          }
        } else {
          throw new Error('No quiz found for this course');
        }
      } catch (error) {
        console.error('Error fetching quiz:', error);
        alert("⚠️ Failed to load quiz. Please try again.");

        this.$router.push({ name: 'course-detail', params: { id: this.courseId } });
      } finally {
        this.loading = false;
      }
    },

    initializeQuiz() {
      // Initialize selected answers array
      this.selectedAnswers = Array(this.quiz.questions.length).fill().map(() => []);
      this.startTime = new Date();

      // Start timer if time limit exists
      if (this.timeLimit > 0) {
        this.timeRemaining = this.timeLimit;
        this.startTimer();
      }
    },

    startTimer() {
      this.clearTimer();
      this.timer = setInterval(() => {
        this.timeRemaining--;
        if (this.timeRemaining <= 0) {
          this.submitQuiz();
        }
      }, 1000);
    },

    clearTimer() {
      if (this.timer) {
        clearInterval(this.timer);
        this.timer = null;
      }
    },

    selectAnswer(questionIndex, optionIndex, questionType) {
      if (this.showResults) return;

      if (questionType === 'single_choice') {
        this.selectedAnswers[questionIndex] = [optionIndex];
      } else {
        const currentAnswers = this.selectedAnswers[questionIndex] || [];
        const answerIndex = currentAnswers.indexOf(optionIndex);

        if (answerIndex === -1) {
          this.selectedAnswers[questionIndex] = [...currentAnswers, optionIndex];
        } else {
          this.selectedAnswers[questionIndex] = currentAnswers.filter(i => i !== optionIndex);
        }
      }

      // Update the array reactively
      this.$set(this.selectedAnswers, questionIndex, [...this.selectedAnswers[questionIndex]]);
    },

    nextQuestion() {
      if (this.currentQuestionIndex < this.quiz.questions.length - 1) {
        this.currentQuestionIndex++;
        this.showResults = false;
      }
    },

    previousQuestion() {
      if (this.currentQuestionIndex > 0) {
        this.currentQuestionIndex--;
        this.showResults = false;
      }
    },

    goToQuestion(index) {
      if (index >= 0 && index < this.quiz.questions.length) {
        this.currentQuestionIndex = index;
        this.showResults = false;
      }
    },

    isQuestionAnswered(index) {
      return this.selectedAnswers[index] && this.selectedAnswers[index].length > 0;
    },

    calculateScore() {
      let score = 0;
      let correctCount = 0;

      this.quiz.questions.forEach((question, index) => {
        const selected = this.selectedAnswers[index] || [];
        const correctAnswers = question.options
          .map((opt, i) => opt.is_correct ? i : null)
          .filter(i => i !== null);

        let isCorrect = false;

        if (question.question_type === 'single_choice') {
          if (selected.length === 1 && correctAnswers.includes(selected[0])) {
            score += question.points;
            isCorrect = true;
          }
        } else {
          // For multiple choice, all correct answers must be selected and no incorrect ones
          const allCorrectSelected = correctAnswers.every(opt => selected.includes(opt));
          const noIncorrectSelected = selected.every(opt => correctAnswers.includes(opt));

          if (allCorrectSelected && noIncorrectSelected) {
            score += question.points;
            isCorrect = true;
          }
        }

        if (isCorrect) correctCount++;
      });

      this.correctCount = correctCount;
      return score;
    },

    async submitQuiz() {
      this.clearTimer(); // stop timer if running
      this.timeSpent = Math.floor((new Date() - this.startTime) / 1000); // in seconds

      // calculate score using your method
      this.score = this.calculateScore();

      // check if passed
      this.passed = this.percentageScore >= this.quiz.passing_score;

      // mark as completed
      this.quizCompleted = true;
      this.showResults = true;

      // (optional) save attempt in backend
      try {
        await axios.post("http://localhost/api/teople1/quizzes/", {
          quiz: this.quiz.id,
          course: this.courseId,
          score: this.score,
          percentage: this.percentageScore,
          passed: this.passed,
          time_spent: this.timeSpent
        });
      } catch (error) {
        console.warn("⚠️ Could not save attempt:", error.response?.data || error);
      }
    },

    formatTimeSpent() {
      const minutes = Math.floor(this.timeSpent / 60);
      const seconds = this.timeSpent % 60;
      return `${minutes}m ${seconds}s`;
    },

    isQuestionCorrect(index) {
      const question = this.quiz.questions[index];
      const selected = this.selectedAnswers[index] || [];
      const correctAnswers = question.options
        .map((opt, i) => opt.is_correct ? i : null)
        .filter(i => i !== null);

      if (question.question_type === 'single_choice') {
        return selected.length === 1 && correctAnswers.includes(selected[0]);
      } else {
        // For multiple choice, all correct answers must be selected and no incorrect ones
        const allCorrectSelected = correctAnswers.every(opt => selected.includes(opt));
        const noIncorrectSelected = selected.every(opt => correctAnswers.includes(opt));
        return allCorrectSelected && noIncorrectSelected;
      }
    },

    retakeQuiz() {
      this.currentQuestionIndex = 0;
      this.selectedAnswers = Array(this.quiz.questions.length).fill().map(() => []);
      this.showResults = false;
      this.quizCompleted = false;
      this.score = 0;
      this.showingReview = false;
      this.startTime = new Date();

      if (this.timeLimit > 0) {
        this.timeRemaining = this.timeLimit;
        this.startTimer();
      }
    },

    reviewAnswers() {
      this.showingReview = true;
    },

    exitQuiz() {
      this.$router.push({
        name: 'course-detail',
        params: { id: this.courseId }
      });
    }
  }
};
</script>

<style scoped>
.quiz-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 5px 20px rgba(0,0,0,0.08);
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.quiz-header {
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 1px solid #eaeaea;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.quiz-title-section h1 {
  margin: 0 0 8px 0;
  color: #2c3e50;
  font-size: 1.8rem;
}

.quiz-description {
  margin: 0;
  color: #7f8c8d;
  font-size: 0.95rem;
}

.quiz-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 10px;
}

.time-remaining, .score {
  padding: 6px 12px;
  border-radius: 20px;
  font-weight: 600;
  font-size: 0.9rem;
}

.time-remaining {
  background-color: #fff4e5;
  color: #e67e22;
}

.score {
  background-color: #e8f5e9;
  color: #2e7d32;
}

.progress-bar-container {
  width: 150px;
  height: 6px;
  background-color: #f0f0f0;
  border-radius: 3px;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  background-color: #42a5f5;
  border-radius: 3px;
  transition: width 0.3s ease;
}

.loading-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: #7f8c8d;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e0e0e0;
  border-top: 4px solid #42a5f5;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 15px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.question-card {
  background: #f9f9f9;
  border-radius: 10px;
  padding: 25px;
  margin-bottom: 25px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.question-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
  color: #666;
  font-size: 0.9rem;
}

.question-text {
  margin: 0 0 20px 0;
  color: #2c3e50;
  font-size: 1.2rem;
  line-height: 1.5;
}

.question-image {
  margin-bottom: 20px;
  text-align: center;
}

.question-image img {
  max-width: 100%;
  border-radius: 8px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.1);
}

.options-container {
  margin-top: 20px;
}

.option {
  display: flex;
  align-items: center;
  padding: 15px;
  margin-bottom: 12px;
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
}

.option:hover {
  background: #f5f5f5;
  transform: translateY(-2px);
  box-shadow: 0 2px 6px rgba(0,0,0,0.05);
}

.option.selected {
  background: #e1f5fe;
  border-color: #4fc3f7;
}

.option.correct {
  background: #e8f5e9;
  border-color: #66bb6a;
}

.option.incorrect {
  background: #ffebee;
  border-color: #ef9a9a;
}

.option-selector {
  margin-right: 15px;
  color: #4fc3f7;
  font-size: 1.1rem;
}

.option.correct .option-selector {
  color: #66bb6a;
}

.option.incorrect .option-selector {
  color: #ef9a9a;
}

.option-text {
  flex: 1;
  font-size: 1rem;
}

.correct-indicator {
  margin-left: 10px;
  padding: 4px 8px;
  background: #66bb6a;
  color: white;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 500;
}

.explanation {
  margin-top: 20px;
  padding: 15px;
  background: #f0f4f8;
  border-radius: 8px;
  font-size: 0.95rem;
  color: #2c3e50;
  border-left: 4px solid #42a5f5;
}

.quiz-navigation {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #eaeaea;
}

.nav-btn {
  padding: 12px 20px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s ease;
  font-size: 0.95rem;
}

.nav-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.prev-btn {
  background: #f0f0f0;
  color: #555;
}

.prev-btn:hover:not(:disabled) {
  background: #e0e0e0;
}

.next-btn, .submit-btn {
  background: #42a5f5;
  color: white;
}

.next-btn:hover:not(:disabled), .submit-btn:hover:not(:disabled) {
  background: #1e88e5;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(30, 136, 229, 0.3);
}

.progress-indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.progress-dots {
  display: flex;
  gap: 8px;
}

.dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background-color: #e0e0e0;
  cursor: pointer;
  transition: all 0.2s ease;
}

.dot.active {
  background-color: #42a5f5;
  transform: scale(1.2);
}

.dot.answered {
  background-color: #66bb6a;
}

.dot.current {
  box-shadow: 0 0 0 2px rgba(66, 165, 245, 0.3);
}

.quiz-results {
  margin-top: 20px;
}

.result-card {
  text-align: center;
  padding: 30px;
  border-radius: 12px;
  margin: 20px 0;
  box-shadow: 0 5px 15px rgba(0,0,0,0.08);
}

.result-card.passed {
  background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
  border: 1px solid #a5d6a7;
}

.result-card.failed {
  background: linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%);
  border: 1px solid #ef9a9a;
}

.result-icon {
  font-size: 3rem;
  margin-bottom: 15px;
}

.result-card.passed .result-icon {
  color: #2e7d32;
}

.result-card.failed .result-icon {
  color: #c62828;
}

.result-card h2 {
  margin: 0 0 15px 0;
  color: #2c3e50;
}

.result-score {
  font-size: 1.3rem;
  margin: 20px 0;
  color: #34495e;
}

.score-value {
  font-weight: 700;
  color: #2e7d32;
}

.score-total {
  font-weight: 600;
}

.score-percentage {
  font-weight: 700;
  color: #42a5f5;
}

.result-details {
  display: flex;
  justify-content: center;
  gap: 30px;
  margin: 20px 0;
  flex-wrap: wrap;
}

.detail-item {
  display: flex;
  flex-direction: column;
  padding: 10px 15px;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 8px;
  min-width: 120px;
}

.detail-label {
  font-size: 0.85rem;
  color: #7f8c8d;
  margin-bottom: 5px;
}

.detail-value {
  font-weight: 600;
  color: #2c3e50;
  font-size: 1.1rem;
}

.pass-message, .fail-message {
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 20px 0;
  font-size: 1.1rem;
  font-weight: 500;
}

.pass-message i {
  color: #2e7d32;
  font-size: 1.5rem;
  margin-right: 10px;
}

.fail-message i {
  color: #c62828;
  font-size: 1.5rem;
  margin-right: 10px;
}

.result-actions {
  margin-top: 30px;
  display: flex;
  justify-content: center;
  gap: 15px;
  flex-wrap: wrap;
}

.retake-btn, .review-btn, .exit-btn {
  padding: 12px 20px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s ease;
  font-size: 0.95rem;
}

.retake-btn {
  background: #42a5f5;
  color: white;
}

.retake-btn:hover {
  background: #1e88e5;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(30, 136, 229, 0.3);
}

.review-btn {
  background: #9c27b0;
  color: white;
}

.review-btn:hover {
  background: #7b1fa2;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(123, 31, 162, 0.3);
}

.exit-btn {
  background: #f0f0f0;
  color: #555;
}

.exit-btn:hover {
  background: #e0e0e0;
  transform: translateY(-2px);
}

.answers-review {
  margin-top: 30px;
  padding: 25px;
  background: #f9f9f9;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.05);
}

.answers-review h3 {
  margin-top: 0;
  color: #2c3e50;
  padding-bottom: 15px;
  border-bottom: 1px solid #eaeaea;
}

.review-list {
  display: flex;
  flex-direction: column;
  gap: 25px;
}

.review-item {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.05);
}

.review-question {
  font-weight: 600;
  margin-bottom: 15px;
  color: #2c3e50;
  font-size: 1.05rem;
}

.review-number {
  color: #42a5f5;
  font-weight: 700;
  margin-right: 5px;
}

.review-points {
  font-size: 0.9rem;
  color: #7f8c8d;
  margin-left: 8px;
}

.review-options {
  margin-bottom: 15px;
}

.review-option {
  display: flex;
  align-items: center;
  padding: 12px 15px;
  margin-bottom: 8px;
  border-radius: 6px;
  border: 1px solid #e0e0e0;
}

.review-option.correct {
  background: #e8f5e9;
  border-color: #a5d6a7;
}

.review-option.selected {
  background: #e3f2fd;
  border-color: #90caf9;
}

.review-option.incorrect {
  background: #ffebee;
  border-color: #ef9a9a;
}

.option-indicator {
  margin-right: 12px;
  font-size: 1.1rem;
}

.review-option.correct .option-indicator {
  color: #2e7d32;
}

.review-option.incorrect .option-indicator {
  color: #c62828;
}

.review-option.selected .option-indicator {
  color: #1565c0;
}

.review-explanation {
  padding: 12px 15px;
  background: #f0f4f8;
  border-radius: 6px;
  margin-top: 10px;
  font-size: 0.95rem;
  color: #2c3e50;
  border-left: 4px solid #42a5f5;
}

.review-status {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  border-radius: 20px;
  font-weight: 600;
  font-size: 0.9rem;
}

.review-status.correct {
  background: #e8f5e9;
  color: #2e7d32;
}

.review-status.incorrect {
  background: #ffebee;
  color: #c62828;
}

.review-status i {
  margin-right: 5px;
}

@media (max-width: 768px) {
  .quiz-header {
    flex-direction: column;
    gap: 15px;
  }

  .quiz-meta {
    align-items: flex-start;
    width: 100%;
  }

  .result-details {
    flex-direction: column;
    align-items: center;
    gap: 15px;
  }

  .result-actions {
    flex-direction: column;
  }

  .quiz-navigation {
    flex-direction: column;
    gap: 15px;
  }

  .progress-dots {
    flex-wrap: wrap;
    justify-content: center;
  }
}
</style>