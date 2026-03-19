<template>
  <div class="weather-widget">
    <!-- 加载中 -->
    <div v-if="loading" class="weather-loading">
      <el-icon :size="24" class="is-loading"><Loading /></el-icon>
    </div>

    <!-- 天气内容 -->
    <template v-else-if="weather">
      <div class="weather-main">
        <span class="weather-icon">{{ weatherIcon }}</span>
        <span class="weather-temp">{{ weather.temperature }}°</span>
      </div>
      <div class="weather-desc">{{ weatherDesc }}</div>
      <div class="weather-range" v-if="weather.tempMax != null">
        {{ weather.tempMin }}° / {{ weather.tempMax }}°
      </div>
      <div class="weather-city" @click="showCityDialog = true">
        {{ cityName }} <el-icon :size="12"><Edit /></el-icon>
      </div>
    </template>

    <!-- 失败 -->
    <template v-else>
      <div class="weather-error">加载失败</div>
      <el-button text size="small" @click="init">重试</el-button>
    </template>

    <!-- 修改城市对话框 -->
    <el-dialog v-model="showCityDialog" title="设置城市" width="360px" append-to-body>
      <el-autocomplete
        v-model="cityInput"
        :fetch-suggestions="searchCity"
        placeholder="输入城市名搜索"
        style="width: 100%"
        @select="handleCitySelect"
        value-key="label"
      />
      <template #footer>
        <el-button @click="showCityDialog = false">取消</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Loading, Edit } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import { getWeatherCity, saveWeatherCity } from '../api'

// WMO Weather Code → 图标 + 描述
const WMO_MAP = {
  0: ['☀️', '晴'],
  1: ['🌤️', '大部晴朗'], 2: ['⛅', '多云'], 3: ['☁️', '阴'],
  45: ['🌫️', '雾'], 48: ['🌫️', '冻雾'],
  51: ['🌦️', '小毛毛雨'], 53: ['🌦️', '毛毛雨'], 55: ['🌧️', '大毛毛雨'],
  61: ['🌧️', '小雨'], 63: ['🌧️', '中雨'], 65: ['🌧️', '大雨'],
  71: ['🌨️', '小雪'], 73: ['🌨️', '中雪'], 75: ['❄️', '大雪'],
  77: ['🌨️', '雪粒'],
  80: ['🌧️', '阵雨'], 81: ['🌧️', '中阵雨'], 82: ['⛈️', '大阵雨'],
  85: ['🌨️', '阵雪'], 86: ['❄️', '大阵雪'],
  95: ['⛈️', '雷暴'], 96: ['⛈️', '雷暴+冰雹'], 99: ['⛈️', '强雷暴'],
}

const loading = ref(true)
const weather = ref(null)
const cityName = ref('')
const weatherIcon = ref('')
const weatherDesc = ref('')
const showCityDialog = ref(false)
const cityInput = ref('')

let cityLat = 0
let cityLon = 0

async function init() {
  loading.value = true
  weather.value = null
  try {
    const cityRes = await getWeatherCity()
    cityName.value = cityRes.data.city

    const geo = await geocode(cityName.value)
    if (!geo) {
      loading.value = false
      return
    }
    cityLat = geo.lat
    cityLon = geo.lon

    await fetchWeather()
  } catch {
    weather.value = null
  } finally {
    loading.value = false
  }
}

async function geocode(name) {
  const { data } = await axios.get('https://geocoding-api.open-meteo.com/v1/search', {
    params: { name, count: 1, language: 'zh' },
  })
  if (!data.results || data.results.length === 0) return null
  const r = data.results[0]
  return { lat: r.latitude, lon: r.longitude }
}

async function fetchWeather() {
  const { data } = await axios.get('https://api.open-meteo.com/v1/forecast', {
    params: {
      latitude: cityLat,
      longitude: cityLon,
      current: 'temperature_2m,weather_code',
      daily: 'temperature_2m_max,temperature_2m_min',
      timezone: 'auto',
      forecast_days: 1,
    },
  })
  const code = data.current.weather_code
  const mapped = WMO_MAP[code] || ['🌡️', '未知']
  weatherIcon.value = mapped[0]
  weatherDesc.value = mapped[1]
  weather.value = {
    temperature: Math.round(data.current.temperature_2m),
    tempMax: data.daily ? Math.round(data.daily.temperature_2m_max[0]) : null,
    tempMin: data.daily ? Math.round(data.daily.temperature_2m_min[0]) : null,
  }
}

async function searchCity(query, cb) {
  if (!query || query.length < 1) { cb([]); return }
  try {
    const { data } = await axios.get('https://geocoding-api.open-meteo.com/v1/search', {
      params: { name: query, count: 5, language: 'zh' },
    })
    const results = (data.results || []).map(r => ({
      label: `${r.name}${r.admin1 ? ', ' + r.admin1 : ''}${r.country ? ', ' + r.country : ''}`,
      name: r.name,
      lat: r.latitude,
      lon: r.longitude,
    }))
    cb(results)
  } catch { cb([]) }
}

async function handleCitySelect(item) {
  showCityDialog.value = false
  cityName.value = item.name
  cityLat = item.lat
  cityLon = item.lon
  try { await saveWeatherCity(item.name) } catch { /* 静默 */ }
  loading.value = true
  try { await fetchWeather() } catch { weather.value = null }
  loading.value = false
  ElMessage.success(`已切换到 ${item.name}`)
}

onMounted(init)
</script>

<style scoped>
.weather-widget {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 8px;
  user-select: none;
}

.weather-loading {
  color: var(--text-muted);
}

.weather-main {
  display: flex;
  align-items: center;
  gap: 6px;
}

.weather-icon {
  font-size: 36px;
  line-height: 1;
}

.weather-temp {
  font-family: var(--font-display);
  font-size: 36px;
  font-weight: 700;
  color: var(--text-primary);
}

.weather-desc {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 4px;
}

.weather-range {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 2px;
}

.weather-city {
  font-size: 12px;
  color: var(--accent);
  margin-top: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 2px;
}

.weather-city:hover {
  color: var(--accent-hover);
}

.weather-error {
  font-size: 13px;
  color: #f56c6c;
}
</style>
