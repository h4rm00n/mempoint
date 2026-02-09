declare module 'markdown-it' {
  interface MarkdownItOptions {
    html?: boolean
    xhtmlOut?: boolean
    breaks?: boolean
    langPrefix?: string
    linkify?: boolean
    typographer?: boolean
    quotes?: string | string[]
    highlight?: (str: string, lang: string) => string
  }

  interface Renderer {
    render(tokens: any[], options: any, env?: any): string
  }

  interface Utils {
    escapeHtml(str: string): string
  }

  class MarkdownIt {
    constructor(options?: MarkdownItOptions)
    render(src: string, env?: any): string
    utils: Utils
    static parse(src: string, env?: any): any[]
  }

  export = MarkdownIt
}
