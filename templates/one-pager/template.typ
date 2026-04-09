// One-Pager Template

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
#let font-display = "Helvetica Neue"
#let font-body = "Helvetica Neue"
#let font-code = "JetBrains Mono"
#let pad-x = 56pt
#let pad-y = 48pt
#let section-gap = 28pt
#let label-gap = 3pt
#let headline-gap = 10pt
#let para-gap = 10pt
#let card-gap = 14pt
// === END THEME ===

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

// ════════════════════════════════════════════════════════════════
// DOCUMENT
// ════════════════════════════════════════════════════════════════

#set document(title: "Your Product Name")
#set page(paper: "us-letter", margin: (top: 0pt, bottom: 1.2cm, left: 2.2cm, right: 2.2cm))
#set text(font: font-body, size: 9.5pt, fill: ink)

// Gradient header bar
#block(width: 100%, height: 6pt, fill: gradient.linear(primary, accent))

#v(2cm)

// Hero
#section-label("Overview")
#v(label-gap)
#display-heading([Your Product Name], size: 28pt)

#v(6pt)
#text(font: font-display, size: 14pt, fill: mid, weight: "light")[A brief supporting tagline goes here]

#v(headline-gap)
#body-text[
  Describe what your product or service does in 2-3 sentences. Focus on the outcome for the reader, not the features. What problem does this solve and why should they care?
]

#v(section-gap)

// Features
#section-label("Features")
#v(label-gap)
#grid(
  columns: (1fr, 1fr),
  gutter: card-gap,
  block(
    width: 100%,
    inset: (x: 14pt, y: 12pt),
    radius: 6pt,
    stroke: 0.5pt + faint,
  )[
    #text(font: font-display, size: 10pt, fill: ink, weight: "semibold")[Feature One]
    #v(4pt)
    #text(size: 8.5pt, fill: mid)[Brief description of this feature and its benefit.]
  ],
  block(
    width: 100%,
    inset: (x: 14pt, y: 12pt),
    radius: 6pt,
    stroke: 0.5pt + faint,
  )[
    #text(font: font-display, size: 10pt, fill: ink, weight: "semibold")[Feature Two]
    #v(4pt)
    #text(size: 8.5pt, fill: mid)[Brief description of this feature and its benefit.]
  ],
)

#v(section-gap)

// Stats
#section-label("By the Numbers")
#v(label-gap)
#grid(
  columns: (1fr, 1fr, 1fr),
  gutter: card-gap,
  align(center)[
    #text(font: font-display, size: 32pt, fill: primary, weight: "bold")[99%]
    #v(4pt)
    #text(size: 8pt, fill: subtle)[Satisfaction]
  ],
  align(center)[
    #text(font: font-display, size: 32pt, fill: primary, weight: "bold")[3x]
    #v(4pt)
    #text(size: 8pt, fill: subtle)[Faster]
  ],
  align(center)[
    #text(font: font-display, size: 32pt, fill: primary, weight: "bold")[50%]
    #v(4pt)
    #text(size: 8pt, fill: subtle)[Cost Reduction]
  ],
)

#v(1fr)

// CTA Footer
#block(
  width: 100%,
  inset: (x: 24pt, y: 16pt),
  radius: 8pt,
  fill: dark-bg,
)[
  #grid(
    columns: (1fr, auto),
    gutter: 16pt,
    align: (left + horizon, right + horizon),
    text(font: font-display, size: 14pt, fill: white, weight: "medium")[Get Started Today],
    text(size: 9pt, fill: accent)[yoursite.com],
  )
]
