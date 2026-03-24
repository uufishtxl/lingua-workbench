<template>
  <div class="key-trap-container">
    <h2>🔥 Vue v-for Key 陷阱演示实验</h2>
    <button class="btn btn-primary action-btn" @click="addWordTop">
      ➕ 在列表【最顶部】插入新单词 (Django)
    </button>

    <div class="dashboard">
      <div class="panel bad">
        <h3>❌ 错误示范：:key="index"</h3>
        <p class="desc">认座位，不认人</p>
        
        <div class="card" v-for="(word, index) in wordList" :key="index">
          <div class="card-header">
            <strong>{{ word.text }}</strong>
            <span class="badge">Index: {{ index }}</span>
          </div>
          <input type="text" placeholder="在这里写下你的中文批注..." />
          <button class="btn btn-danger" @click="deleteWord(index)">🗑️ 删除这个词</button>
        </div>
      </div>

      <div class="panel good">
        <h3>✅ 正确示范：:key="word.id"</h3>
        <p class="desc">认身份证，精准定位</p>
        
        <div class="card" v-for="(word, index) in wordList" :key="word.id">
          <div class="card-header">
            <strong>{{ word.text }}</strong>
            <span class="badge">ID: {{ word.id }}</span>
          </div>
          <input type="text" placeholder="在这里写下你的中文批注..." />
          <button class="btn btn-danger" @click="deleteWord(index)">🗑️ 删除这个词</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

// 初始数据源（两个列表共用这一份数据）
const wordList = ref([
  { id: 'id-1', text: 'Karamazov' },
  { id: 'id-2', text: 'Zhuangzi' },
  { id: 'id-3', text: 'Python' }
])

// 往数组最前面插入一条数据
const addWordTop = () => {
  wordList.value.unshift({ 
    id: 'id-' + Date.now(), // 生成一个唯一的新 ID
    text: 'Django' 
  })
}

// 根据数组索引删除数据
const deleteWord = (index) => {
  wordList.value.splice(index, 1)
}
</script>

<style scoped>
.key-trap-container {
  font-family: sans-serif;
  padding: 20px;
  max-width: 900px;
  margin: 0 auto;
}

.action-btn {
  margin-bottom: 20px;
  font-size: 16px;
}

.dashboard {
  display: flex;
  gap: 40px;
}

.panel {
  flex: 1;
  border: 2px solid #ccc;
  padding: 20px;
  border-radius: 8px;
}

.panel.bad {
  border-color: #ff4d4f;
  background-color: #fff1f0;
}

.panel.good {
  border-color: #52c41a;
  background-color: #f6ffed;
}

.desc {
  color: #666;
  margin-top: 0;
  margin-bottom: 15px;
}

.card {
  background: white;
  border: 1px solid #ddd;
  padding: 15px;
  margin-bottom: 15px;
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.badge {
  background: #eee;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
  color: #555;
}

input[type="text"] {
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 14px;
}

.btn {
  padding: 8px 16px;
  cursor: pointer;
  border: none;
  border-radius: 4px;
  font-weight: bold;
}

.btn-primary {
  background: #1890ff;
  color: white;
}

.btn-primary:hover {
  background: #40a9ff;
}

.btn-danger {
  background: #ff4d4f;
  color: white;
  align-self: flex-start;
}

.btn-danger:hover {
  background: #ff7875;
}
</style>