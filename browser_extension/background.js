// background.js - Service Worker
// 处理后台任务（如果需要）

chrome.runtime.onInstalled.addListener(() => {
  console.log('视频转文字插件已安装');
});