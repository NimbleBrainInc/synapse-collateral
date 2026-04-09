// Invoice Template

// === THEME ===
#let primary = rgb("#0066FF")
#let accent = rgb("#00D4FF")
#let ink = rgb("#0F172A")
#let dark = rgb("#1E293B")
#let mid = rgb("#475569")
#let subtle = rgb("#94A3B8")
#let faint = rgb("#CBD5E1")
#let wash = rgb("#F8FAFC")
#let paper = rgb("#FFFFFF")
#let dark-bg = rgb("#0F172A")
#let dark-surface = rgb("#1E293B")
#let success-color = rgb("#10B981")
#let warning-color = rgb("#F59E0B")
#let error-color = rgb("#EF4444")
#let font-display = "Plus Jakarta Sans"
#let font-body = "Avenir Next"
#let font-code = "JetBrains Mono"
#let pad-x = 56pt
#let pad-y = 48pt
#let section-gap = 28pt
#let label-gap = 3pt
#let headline-gap = 10pt
#let para-gap = 10pt
#let card-gap = 14pt
// === END THEME ===

// === VARIABLES (replace with actual values) ===
#let invoice-number = "INV-001"
#let invoice-date = "January 1, 2025"
#let due-date = "January 31, 2025"
#let from-name = "Your Company"
#let from-address = "123 Main St\nCity, State 12345"
#let to-name = "Client Name"
#let to-address = "456 Client Ave\nCity, State 67890"
#let line-items = (
  (description: "Service description", quantity: "1", rate: "$1,000", amount: "$1,000"),
)
#let subtotal = "$1,000"
#let tax-label = "Tax (0%)"
#let tax-amount = "$0"
#let total = "$1,000"
#let payment-instructions = "Wire transfer to Account #12345"
#let notes = ""
// === END VARIABLES ===

// Components
#let section-label(label, color: primary) = {
  text(font: font-display, size: 7.5pt, fill: color, weight: "semibold", tracking: 2pt)[#upper(label)]
}

#let display-heading(body, size: 22pt) = {
  text(font: font-display, size: size, fill: ink, weight: "light", tracking: -0.3pt, body)
}

#let body-text(body) = {
  set par(leading: 8pt, spacing: 8pt)
  text(font: font-body, size: 9.5pt, fill: mid, body)
}

#let callout-box(body, accent-color: primary) = {
  block(
    width: 100%,
    inset: (left: 16pt, right: 16pt, top: 12pt, bottom: 12pt),
    radius: (right: 4pt),
    stroke: (left: 3pt + accent-color),
    fill: wash,
  )[
    #set text(size: 9pt, fill: dark)
    #set par(leading: 7pt)
    #body
  ]
}

#set document(title: "Invoice " + invoice-number)
#set page(paper: "us-letter", margin: (top: 2cm, bottom: 2cm, left: 2.5cm, right: 2.5cm))
#set text(font: font-body, size: 9.5pt, fill: ink)

// Header
#grid(
  columns: (1fr, auto),
  gutter: 2cm,
  [
    #text(font: font-display, size: 28pt, fill: ink, weight: "bold")[INVOICE]
    #v(4pt)
    #text(size: 9pt, fill: subtle)[#sym.hash#invoice-number]
  ],
  align(right)[
    #text(size: 9pt, fill: mid)[*Date:* #invoice-date]
    #linebreak()
    #text(size: 9pt, fill: mid)[*Due:* #due-date]
  ],
)

#v(section-gap)
#line(length: 100%, stroke: 0.5pt + faint)
#v(section-gap)

// Parties
#grid(
  columns: (1fr, 1fr),
  gutter: 2cm,
  [
    #text(size: 7.5pt, fill: subtle, weight: "semibold", tracking: 1.5pt)[FROM]
    #v(4pt)
    #text(size: 10pt, fill: ink, weight: "medium")[#from-name]
    #v(2pt)
    #text(size: 9pt, fill: mid)[#from-address]
  ],
  [
    #text(size: 7.5pt, fill: subtle, weight: "semibold", tracking: 1.5pt)[BILL TO]
    #v(4pt)
    #text(size: 10pt, fill: ink, weight: "medium")[#to-name]
    #v(2pt)
    #text(size: 9pt, fill: mid)[#to-address]
  ],
)

#v(section-gap)

// Line items table header
#block(width: 100%, fill: wash, inset: (x: 12pt, y: 8pt), radius: (top-left: 4pt, top-right: 4pt))[
  #grid(
    columns: (1fr, 60pt, 80pt, 80pt),
    gutter: 8pt,
    text(size: 8pt, fill: subtle, weight: "semibold")[DESCRIPTION],
    align(right)[#text(size: 8pt, fill: subtle, weight: "semibold")[QTY]],
    align(right)[#text(size: 8pt, fill: subtle, weight: "semibold")[RATE]],
    align(right)[#text(size: 8pt, fill: subtle, weight: "semibold")[AMOUNT]],
  )
]

// Line items
#for item in line-items [
  #block(width: 100%, inset: (x: 12pt, y: 8pt), stroke: (bottom: 0.3pt + faint))[
    #grid(
      columns: (1fr, 60pt, 80pt, 80pt),
      gutter: 8pt,
      text(size: 9pt, fill: ink)[#if type(item) == dictionary { item.at("description", default: "") } else { str(item) }],
      align(right)[#text(size: 9pt, fill: mid)[#if type(item) == dictionary { item.at("quantity", default: "") } else { "" }]],
      align(right)[#text(size: 9pt, fill: mid)[#if type(item) == dictionary { item.at("rate", default: "") } else { "" }]],
      align(right)[#text(size: 9pt, fill: ink, weight: "medium")[#if type(item) == dictionary { item.at("amount", default: "") } else { "" }]],
    )
  ]
]

#v(para-gap)

// Totals
#align(right)[
  #block(width: 240pt)[
    #grid(
      columns: (1fr, 100pt),
      gutter: 6pt,
      text(size: 9pt, fill: mid)[Subtotal],
      align(right)[#text(size: 9pt, fill: ink)[#subtotal]],
      text(size: 9pt, fill: mid)[#tax-label],
      align(right)[#text(size: 9pt, fill: ink)[#tax-amount]],
    )
    #v(6pt)
    #line(length: 100%, stroke: 0.5pt + faint)
    #v(6pt)
    #grid(
      columns: (1fr, 100pt),
      gutter: 6pt,
      text(size: 11pt, fill: ink, weight: "bold")[Total Due],
      align(right)[#text(size: 11pt, fill: primary, weight: "bold")[#total]],
    )
  ]
]

#v(1fr)

// Footer
#if payment-instructions != [] [
  #line(length: 100%, stroke: 0.3pt + faint)
  #v(para-gap)
  #text(size: 7.5pt, fill: subtle, weight: "semibold", tracking: 1.5pt)[PAYMENT INSTRUCTIONS]
  #v(4pt)
  #text(size: 9pt, fill: mid)[#payment-instructions]
]

#if notes != [] [
  #v(para-gap)
  #text(size: 7.5pt, fill: subtle, weight: "semibold", tracking: 1.5pt)[NOTES]
  #v(4pt)
  #text(size: 9pt, fill: mid)[#notes]
]
