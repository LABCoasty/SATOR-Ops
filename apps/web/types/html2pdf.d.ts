declare module "html2pdf.js" {
  interface Html2PdfOptions {
    margin?: number | number[]
    filename?: string
    image?: {
      type?: string
      quality?: number
    }
    html2canvas?: {
      scale?: number
      useCORS?: boolean
      letterRendering?: boolean
      backgroundColor?: string
    }
    jsPDF?: {
      unit?: string
      format?: string | number[]
      orientation?: "portrait" | "landscape"
    }
    pagebreak?: {
      mode?: string | string[]
      before?: string | string[]
      after?: string | string[]
      avoid?: string | string[]
    }
  }

  interface Html2PdfInstance {
    set(options: Html2PdfOptions): Html2PdfInstance
    from(element: Element | string): Html2PdfInstance
    save(): Promise<void>
    toPdf(): Html2PdfInstance
    output(type: string, options?: object): Promise<string | Blob | ArrayBuffer>
  }

  function html2pdf(): Html2PdfInstance
  export default html2pdf
}
