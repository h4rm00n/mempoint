// 本地存储工具函数

export const storage = {
  // 获取
  get<T>(key: string): T | null {
    const value = localStorage.getItem(key)
    if (value === null) return null
    try {
      return JSON.parse(value) as T
    } catch {
      return value as T
    }
  },

  // 设置
  set<T>(key: string, value: T): void {
    const jsonValue = typeof value === 'string' ? value : JSON.stringify(value)
    localStorage.setItem(key, jsonValue)
  },

  // 删除
  remove(key: string): void {
    localStorage.removeItem(key)
  },

  // 清空
  clear(): void {
    localStorage.clear()
  }
}
