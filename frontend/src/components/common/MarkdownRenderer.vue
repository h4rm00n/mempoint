<template>
  <div class="markdown-renderer" v-html="renderedHtml"></div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'

const props = defineProps<{
  content: string
}>()

const md = new MarkdownIt({
  highlight: function (str, lang) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return `<pre class="hljs"><code>${hljs.highlight(str, { language: lang }).value}</code></pre>`
      } catch (__) {}
    }
    return `<pre class="hljs"><code>${md.utils.escapeHtml(str)}</code></pre>`
  }
})

const renderedHtml = computed(() => {
  return md.render(props.content || '')
})
</script>

<style scoped>
.markdown-renderer :deep(h1) {
  font-size: 2em;
  font-weight: bold;
  margin: 0.67em 0;
  padding-bottom: 0.3em;
  border-bottom: 1px solid #eaecef;
}

.markdown-renderer :deep(h2) {
  font-size: 1.5em;
  font-weight: bold;
  margin: 0.83em 0;
  padding-bottom: 0.3em;
  border-bottom: 1px solid #eaecef;
}

.markdown-renderer :deep(h3) {
  font-size: 1.25em;
  font-weight: bold;
  margin: 1em 0;
}

.markdown-renderer :deep(p) {
  margin: 1em 0;
  line-height: 1.6;
}

.markdown-renderer :deep(code) {
  padding: 0.2em 0.4em;
  margin: 0;
  font-size: 85%;
  background-color: rgba(27, 31, 35, 0.05);
  border-radius: 3px;
}

.markdown-renderer :deep(pre) {
  padding: 16px;
  overflow: auto;
  font-size: 85%;
  line-height: 1.45;
  background-color: #f6f8fa;
  border-radius: 6px;
}

.markdown-renderer :deep(pre code) {
  background-color: transparent;
  padding: 0;
}

.markdown-renderer :deep(ul),
.markdown-renderer :deep(ol) {
  padding-left: 2em;
  margin: 1em 0;
}

.markdown-renderer :deep(li) {
  margin: 0.5em 0;
}

.markdown-renderer :deep(a) {
  color: #0969da;
  text-decoration: none;
}

.markdown-renderer :deep(a:hover) {
  text-decoration: underline;
}

.markdown-renderer :deep(blockquote) {
  padding: 0 1em;
  color: #57606a;
  border-left: 0.25em solid #d0d7de;
  margin: 1em 0;
}

.markdown-renderer :deep(table) {
  border-spacing: 0;
  border-collapse: collapse;
  margin: 1em 0;
  width: 100%;
}

.markdown-renderer :deep(th),
.markdown-renderer :deep(td) {
  padding: 6px 13px;
  border: 1px solid #d0d7de;
}

.markdown-renderer :deep(th) {
  font-weight: 600;
  background-color: #f6f8fa;
}
</style>
