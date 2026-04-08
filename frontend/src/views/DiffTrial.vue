<template>
  <div class="app-container">
    
    <section class="screen first-screen">
      <div class="feedback-header">
        <div class="medal-badge">
          <svg viewBox="0 0 24 24" fill="none" stroke="#000" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="8" r="6"></circle>
            <path d="M15.477 12.89 17 22l-5-3-5 3 1.523-9.11"></path>
            <polygon points="12 5 13 7 15 7 13.5 8.5 14 10.5 12 9.5 10 10.5 10.5 8.5 9 7 11 7"></polygon>
          </svg>
        </div>
        <h1>PRACTICE COMPLETE!</h1>
        <!-- <p class="subtitle">You've leveled up your phrasing skills. Level 12 reached!</p> -->
         <div class="flex justify-between gap-4">
            <div class="bg-blue-400 px-2 py-1 rounded-lg text-white text-xs">DOWNSTREAM PROVIDER</div>
            <div class="bg-blue-400 px-2 py-1 rounded-lg text-white text-xs">SMOKE AND MIRRORS</div>
            <div class="bg-blue-400 px-2 py-1 rounded-lg text-white text-xs">WHERE THE RUBBER MEATS THE ROAT</div>
         </div>
      </div>

      <div class="main-content-wrapper">
        <div class="scenario-banner">
          <div class="s-label">SCENARIO</div>
          <p>你的下游供应商觉得你现在的 AI 方案只是在虚张声势。请写一段话，向他证明当项目真正落地时，这套方案是能跑通的。</p>
        </div>

        <div class="cards-wrapper">
          <div class="game-card card-white">
            <div class="icon-circle icon-gray">✏️</div>
            <div class="card-label gray-text">USER COMPOSITION</div>
            <div class="inner-bubble bubble-gray">
              "I totally understand your concerns. But I assure you, it can definitely work out where the rubber meets the road. This is not smoke and mirrors. We've done a full-scale pilot and can give downstream providers demos anytime they want."
            </div>
          </div>

          <div class="game-card card-teal">
            <div class="powerful-tag">⚡ POLISHED</div>
            <div class="avatar-box">
               <img src="https://api.dicebear.com/7.x/avataaars/svg?seed=Erik&backgroundColor=b6e3f4" alt="AI Avatar">
            </div>
            <div class="card-label cyan-text">AI ENHANCEMENT</div>
            <div class="inner-bubble bubble-teal">
              "I completely understand your concerns. However, I can assure you that our solution proves its value <strong>where the rubber meets the road</strong>. This isn't just <strong>smoke and mirrors</strong>; we’ve already synced with our <strong>downstream providers</strong> for a full-scale pilot, and we can walk you through a demo whenever you’re ready."
            </div>
          </div>

          <div class="game-card card-dark">
            <div class="icon-circle icon-green">★</div>
            <div class="card-label neon-green-text">COMMUNITY / IDIOMATIC</div>
            <div class="inner-bubble bubble-dark">
              "I get the skepticism—honestly, most AI pitches these days are 90% <strong>smoke and mirrors</strong>. But look, <strong>where the rubber meets the road</strong>, our tech actually holds up. We’ve battle-tested this with our <strong>downstream providers</strong> in a pilot. If you want to see it in action without the fluff, I’m down for a demo anytime."
            </div>
          </div>
        </div>
      </div>

      <div class="scroll-hint">向下滑动查看宇宙图谱 ↓</div>
    </section>

    <section class="screen second-screen">
      <div class="orbit-header">
        <h2>Variations & Deep Dive</h2>
        <p>Hover over satellites to see example sentences</p>
      </div>

      <svg id="orbit-svg" viewBox="0 0 800 600" preserveAspectRatio="xMidYMid meet">
        <defs>
          <linearGradient id="meteor-grad" x1="100%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#ffffff" stop-opacity="1" />
            <stop offset="100%" stop-color="#ffffff" stop-opacity="0" />
          </linearGradient>

          <symbol id="mtx-earth" viewBox="0 0 100 100">
            <circle cx="50" cy="50" r="40" fill="#247693" />
            <path d="M30 40 Q 40 30 60 35 T 70 50 Q 60 70 40 65 Z" fill="#52D1C5" opacity="0.8" />
            <circle cx="50" cy="50" r="45" fill="none" stroke="rgba(82,209,197,0.3)" stroke-width="2" />
          </symbol>
          <symbol id="mtx-saturn" viewBox="0 0 100 100">
            <circle cx="50" cy="50" r="25" fill="#E97451" />
            <ellipse cx="50" cy="50" rx="45" ry="12" fill="none" stroke="#FFD066" stroke-width="4" transform="rotate(-20 50 50)" />
          </symbol>
          <symbol id="mtx-moon" viewBox="0 0 100 100">
            <circle cx="50" cy="50" r="35" fill="#BABABA" />
            <circle cx="35" cy="35" r="8" fill="#888" opacity="0.4" />
            <circle cx="65" cy="55" r="6" fill="#888" opacity="0.4" />
          </symbol>
          <symbol id="mtx-rocket" viewBox="0 0 100 100">
            <path d="M50 20 L65 60 L35 60 Z" fill="#fff" />
            <path d="M45 60 L50 75 L55 60 Z" fill="#FFC022" />
          </symbol>
          <symbol id="mtx-satellite" viewBox="0 0 100 100">
            <circle cx="50" cy="50" r="15" fill="#52D1C5" />
            <circle cx="50" cy="50" r="20" fill="none" stroke="#fff" stroke-dasharray="4,4" />
          </symbol>
        </defs>

        <path 
          id="orbit-line"
          d="M128,114 C277,165 408,89 594,100 S 753,312 600,289 S 324,241 215,267 S 102,447 241,460 S 450,376 572,410 S 681,480 690,495"
          fill="none" stroke="rgba(255,255,255,0.2)" stroke-width="2" stroke-dasharray="6,6"
        />

        <g id="meteor-shower">
          <line x1="250" y1="-50" x2="100" y2="100" class="meteor m1" />
          <line x1="650" y1="50" x2="450" y2="250" class="meteor m2" />
          <line x1="900" y1="200" x2="650" y2="450" class="meteor m3" />
          <line x1="450" y1="500" x2="250" y2="700" class="meteor m4" />
        </g>

        <g v-for="(node, index) in renderedNodes" :key="'main-'+index">
          
          <use 
            :href="node.symbol" 
            :x="node.x - 30" 
            :y="node.y - 30" 
            width="60" 
            height="60" 
            class="celestial-body"
          />
          <text :x="node.x" :y="node.y + 45" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">
            {{ node.name }}
          </text>
        </g>

        <g v-for="(vNode, index) in renderedVariants" :key="'var-'+index" 
           @mouseenter="showTooltip(vNode.sentence, $event)" 
           @mouseleave="hideTooltip" 
           style="cursor: pointer;">
          <use 
            :href="vNode.symbol" 
            :x="vNode.x - 15" 
            :y="vNode.y - 15" 
            width="30" 
            height="30" 
            class="celestial-body"
          />
          <text :x="vNode.x" :y="vNode.y - 20" fill="#a5b4fc" font-size="12" text-anchor="middle">
            {{ vNode.name }}
          </text>
        </g>
      </svg>

      <div v-if="hoverText" class="glass-tooltip" :style="tooltipPos">
        <p>{{ hoverText }}</p>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue';

const nodeData = [
  {
    name: 'downstream provider',
    pct: 0.15,
    symbol: '#mtx-earth',
    variants: [
      { name: 'sub-processors', symbol: '#mtx-satellite', offset: -0.07, sentence: '"We\'ve cleared this with our sub-processors."' },
      { name: 'the folks handling our data', symbol: '#mtx-rocket', offset: 0.08, sentence: '"I’ve checked with the folks handling our data."' }
    ]
  },
  {
    name: 'smoke and mirrors',
    pct: 0.50,
    symbol: '#mtx-saturn',
    variants: [
      { name: 'vaporware', symbol: '#mtx-rocket', offset: -0.07, sentence: '"The tech community is tired of vaporware; we need to ship functional code."' },
      { name: 'all flash and no substance', symbol: '#mtx-satellite', offset: 0.07, sentence: '"This isn\'t all flash and no substance; it\'s solid."' }
    ]
  },
  {
    name: 'where the rubber meets the road',
    pct: 0.85,
    symbol: '#mtx-moon',
    variants: [
      { name: 'push comes to shove', symbol: '#mtx-satellite', offset: -0.06, sentence: '"When push comes to shove, will our API handle 10k concurrent users?"' },
      { name: 'the moment of truth', symbol: '#mtx-rocket', offset: 0.06, sentence: '"The live demo was the moment of truth for the entire development team."' }
    ]
  }
];

const renderedNodes = ref([]);
const renderedVariants = ref([]);
const hoverText = ref('');
const tooltipPos = reactive({ top: '0px', left: '0px' });

const showTooltip = (text, event) => {
  hoverText.value = text;
  tooltipPos.top = `${event.clientY - 80}px`;
  tooltipPos.left = `${event.clientX + 20}px`;
};

const hideTooltip = () => {
  hoverText.value = '';
};

onMounted(() => {
  const pathEl = document.getElementById('orbit-line');
  if (!pathEl) return;
  const pathLen = pathEl.getTotalLength();

  const mNodes = [];
  const vNodes = [];

  nodeData.forEach(node => {
    const pt = pathEl.getPointAtLength(node.pct * pathLen);
    mNodes.push({ name: node.name, symbol: node.symbol, x: pt.x, y: pt.y });

    node.variants.forEach(v => {
      const vPt = pathEl.getPointAtLength((node.pct + v.offset) * pathLen);
      vNodes.push({ name: v.name, symbol: v.symbol, sentence: v.sentence, x: vPt.x, y: vPt.y });
    });
  });

  renderedNodes.value = mNodes;
  renderedVariants.value = vNodes;
});
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Nunito:ital,wght@0,500;0,800;0,900;1,500&display=swap');

.app-container {
  height: calc(100vh - 100px);
  overflow-y: scroll;
  scroll-snap-type: y mandatory;
  font-family: 'Nunito', sans-serif;
  background: #fafafa;
}

.screen {
  min-height: calc(100vh - 100px);
  width: 100%;
  scroll-snap-align: start;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
}

/* ================= 第一屏：GAME-FI 样式 ================= */
.feedback-header { text-align: center; margin-bottom: 30px; }
.medal-badge {
  width: 60px; height: 60px; background: #ffc800; border-radius: 16px;
  margin: 0 auto 15px; display: flex; align-items: center; justify-content: center;
  box-shadow: 0 6px 0 #e5b400;
}
.medal-badge svg { width: 30px; }
.feedback-header h1 { font-size: 2.8rem; font-weight: 900; color: #333; margin: 0 0 5px 0; }
.subtitle { color: #888; font-size: 1.1rem; font-weight: 500; }

.main-content-wrapper { max-width: 1200px; width: 90%; }

.scenario-banner {
  background: #fff; border: 2px solid #eee; border-left: 6px solid #ffc800;
  padding: 20px 25px; border-radius: 16px; margin-bottom: 30px;
  box-shadow: 0 4px 15px rgba(0,0,0,0.03);
}
.s-label { font-weight: 800; color: #ffc800; font-size: 0.8rem; letter-spacing: 1px; margin-bottom: 5px; }
.scenario-banner p { margin: 0; color: #555; line-height: 1.6; }

.cards-wrapper { display: flex; gap: 25px; }
.game-card {
  flex: 1; border-radius: 24px; padding: 30px 20px;
  display: flex; flex-direction: column; align-items: center; text-align: center;
  position: relative;
}

.card-white { background: #fff; border: 2px solid #f0f0f0; box-shadow: 0 8px 0 #e5e5e5; }
.card-teal { background: #006b8f; border: 2px solid #005b7a; box-shadow: 0 8px 0 #00506b; transform: scale(1.05); z-index: 2; }
.card-dark { background: #111412; border: 2px solid #1a241c; box-shadow: 0 8px 0 #090a09; }

.icon-circle, .avatar-box { width: 65px; height: 65px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-bottom: 15px; font-size: 1.5rem; }
.icon-gray { background: #e5e5e5; }
.icon-green { background: #264a1a; color: #65d036; font-size: 2rem; }
.avatar-box img { width: 65px; height: 65px; border-radius: 50%; border: 3px solid #006b8f; }

.powerful-tag {
  position: absolute; top: -15px; right: 20px; background: #a3e635; color: #1a2e05;
  font-weight: 800; font-size: 0.75rem; padding: 6px 14px; border-radius: 12px; box-shadow: 0 4px 0 #84cc16;
}

.card-label { font-size: 0.7rem; font-weight: 800; letter-spacing: 1.5px; margin-bottom: 20px; }
.gray-text { color: #999; }
.cyan-text { color: #88d4e7; }
.neon-green-text { color: #65d036; }

.inner-bubble {
  width: 100%; padding: 20px; border-radius: 16px; font-style: italic;
  font-size: 0.95rem; line-height: 1.6; font-weight: 500;
}
.inner-bubble strong { font-weight: 900; text-decoration: underline; }
.bubble-gray { background: #f5f5f5; color: #555; }
.bubble-teal { background: #005a78; color: #fff; border: 1px solid #004d66; }
.bubble-dark { background: #1c211d; color: #65d036; border: 1px solid #2a332c; }

.scroll-hint { margin-top: 30px; color: #aaa; font-weight: bold; font-size: 0.9rem; }

/* ================= 第二屏：深空图谱 ================= */
.second-screen { background: #001a26; }
.orbit-header { text-align: center; margin-bottom: 10px; }
.orbit-header h2 { margin: 0 0 5px 0; color: #fff; font-weight: 900; }
.orbit-header p { margin: 0; color: #94a3b8; font-size: 0.9rem; }

#orbit-svg { width: 100%; height: 80vh; overflow: visible; }

/* 天体悬浮动画 */
.celestial-body {
  transform-origin: center;
  transform-box: fill-box;
}

/* 斜上旋转 */
.float-up-right {
  animation: float-ur 5s ease-in-out infinite alternate;
}
/* 斜下旋转 */
.float-down-right {
  animation: float-dr 6s ease-in-out infinite alternate;
}

@keyframes float-ur {
  0% { transform: translate(-4px, 4px) rotate(-8deg); }
  100% { transform: translate(4px, -4px) rotate(8deg); }
}

@keyframes float-dr {
  0% { transform: translate(-4px, -4px) rotate(8deg); }
  100% { transform: translate(4px, 4px) rotate(-8deg); }
}

/* 流星雨动画 */
.meteor {
  stroke: url(#meteor-grad);
  stroke-linecap: round;
  opacity: 0;
}
/* 分别错开流星出现的时间和速度 */
.m1 { animation: meteor-fall 8s linear infinite 1s; stroke-width: 2; }
.m2 { animation: meteor-fall 11s linear infinite 4s; stroke-width: 3; }
.m3 { animation: meteor-fall 14s linear infinite 6s; stroke-width: 1.5; }
.m4 { animation: meteor-fall 10s linear infinite 9s; stroke-width: 2; }

@keyframes meteor-fall {
  0% { transform: translate(0, 0); opacity: 0; }
  5% { opacity: 1; }
  15% { transform: translate(-250px, 250px); opacity: 0; }
  100% { transform: translate(-250px, 250px); opacity: 0; }
}

.glass-tooltip {
  position: fixed; background: rgba(15, 23, 42, 0.9); backdrop-filter: blur(10px);
  padding: 15px 25px; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.5);
  border: 1px solid rgba(255,255,255,0.1); max-width: 320px; z-index: 1000;
  pointer-events: none; color: #e2e8f0; font-style: italic; font-size: 0.95rem; line-height: 1.5;
}
</style>