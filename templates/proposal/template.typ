// Business Proposal Template

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
#let client-name = "Client Name"
#let proposal-date = "January 1, 2025"
#let recipient-name = "Recipient Name"
#let recipient-title = "Title"
#let subject-line = "Proposal Subject"
#let cover-letter-body = "We are pleased to present this proposal for your consideration."
#let summary-headline = "Summary Headline"
#let summary-body = "Executive summary of the proposed engagement."
#let deliverables = ("Deliverable 1", "Deliverable 2", "Deliverable 3")
#let fee = "$10,000"
#let payment-terms = "50% upfront, 50% on completion"
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

#set document(title: "Proposal — " + client-name)
#set page(paper: "us-letter", margin: (top: 2.2cm, bottom: 2.8cm, left: 3cm, right: 3cm))
#set text(font: font-body, size: 9.5pt, fill: ink)
#set par(leading: 7pt, spacing: 9pt)

// --- Page 1: Cover Letter ---
#page(footer: none)[
  #v(1cm)
  #text(font: font-display, size: 9pt, fill: subtle)[#proposal-date]
  #v(1.5cm)

  #text(size: 10pt, fill: ink)[#recipient-name]
  #if recipient-title != "" [
    #linebreak()
    #text(size: 9pt, fill: mid)[#recipient-title]
  ]
  #linebreak()
  #text(size: 9pt, fill: mid)[#client-name]

  #v(1.5cm)
  #text(font: font-display, size: 7.5pt, fill: primary, weight: "semibold", tracking: 1.5pt)[RE:]
  #h(6pt)
  #text(size: 10pt, fill: ink, weight: "medium")[#subject-line]

  #v(1cm)
  #line(length: 100%, stroke: 0.5pt + faint)
  #v(0.8cm)

  #set par(leading: 8pt, spacing: 10pt)
  #text(size: 9.5pt, fill: mid)[#cover-letter-body]

  #v(1fr)
  #line(length: 40%, stroke: 0.3pt + faint)
  #v(0.5cm)
  #text(size: 9pt, fill: ink, weight: "medium")[Prepared with care.]
]

// --- Page 2: Executive Summary ---
#page[
  #section-label("Executive Summary")
  #v(label-gap)
  #display-heading(summary-headline, size: 28pt)
  #v(headline-gap)

  #body-text[#summary-body]

  #v(section-gap)

  #if deliverables.len() > 0 [
    #section-label("Deliverables")
    #v(label-gap)
    #for item in deliverables [
      #grid(
        columns: (auto, 1fr),
        gutter: 8pt,
        text(size: 9pt, fill: primary, weight: "bold")[#sym.checkmark],
        text(size: 9pt, fill: mid)[#item],
      )
      #v(4pt)
    ]
  ]
]

// --- Page 3: Pricing ---
#page[
  #section-label("Investment")
  #v(label-gap)
  #display-heading([Your Investment], size: 28pt)
  #v(headline-gap)

  #block(
    width: 100%,
    inset: (x: 24pt, y: 20pt),
    radius: 8pt,
    fill: wash,
    stroke: 0.5pt + faint,
  )[
    #text(font: font-display, size: 36pt, fill: primary, weight: "bold")[#fee]
    #v(8pt)
    #text(size: 9pt, fill: mid)[#payment-terms]
  ]

  #v(section-gap)
  #body-text[This investment covers all deliverables outlined in the executive summary. We are confident this approach will deliver meaningful results for your team.]
]

// --- Page 4: Authorization ---
#page[
  #section-label("Authorization")
  #v(label-gap)
  #display-heading([Ready to Proceed], size: 28pt)
  #v(headline-gap)

  #body-text[To authorize this engagement, please sign below. We look forward to working with you.]

  #v(2cm)

  #grid(
    columns: (1fr, 1fr),
    gutter: 2cm,
    [
      #line(length: 100%, stroke: 0.5pt + faint)
      #v(4pt)
      #text(size: 8pt, fill: subtle)[Client Signature]
      #v(1.5cm)
      #line(length: 100%, stroke: 0.5pt + faint)
      #v(4pt)
      #text(size: 8pt, fill: subtle)[Date]
    ],
    [
      #line(length: 100%, stroke: 0.5pt + faint)
      #v(4pt)
      #text(size: 8pt, fill: subtle)[Provider Signature]
      #v(1.5cm)
      #line(length: 100%, stroke: 0.5pt + faint)
      #v(4pt)
      #text(size: 8pt, fill: subtle)[Date]
    ],
  )
]
