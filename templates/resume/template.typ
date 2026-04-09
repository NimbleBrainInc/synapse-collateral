// Resume Template

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
#let full-name = "Your Name"
#let title = "Your Title"
#let email = "email@example.com"
#let phone = "(555) 123-4567"
#let location = "City, State"
#let website = "yoursite.com"
#let summary = "Brief professional summary."
#let experience = (
  (company: "Company Name", role: "Role Title", dates: "2020 – Present", bullets: ("Key achievement or responsibility",)),
)
#let education = (
  (institution: "University Name", degree: "Degree, Field of Study", dates: "2016 – 2020"),
)
#let skills = ("Skill 1", "Skill 2", "Skill 3")
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

#set document(title: full-name + " — Resume")
#set page(paper: "us-letter", margin: (top: 2cm, bottom: 2cm, left: 2.5cm, right: 2.5cm))
#set text(font: font-body, size: 9.5pt, fill: ink)
#set par(leading: 7pt, spacing: 8pt)

// Header
#align(center)[
  #text(font: font-display, size: 24pt, fill: ink, weight: "bold")[#full-name]
  #if title != "" [
    #v(2pt)
    #text(font: font-display, size: 12pt, fill: mid, weight: "light")[#title]
  ]
  #v(6pt)
  #{
    let items = ()
    if email != "" { items.push(email) }
    if phone != "" { items.push(phone) }
    if location != "" { items.push(location) }
    if website != "" { items.push(website) }
    text(size: 8.5pt, fill: subtle)[#items.join("  |  ")]
  }
]

#v(section-gap)
#line(length: 100%, stroke: 0.5pt + faint)

// Summary
#if summary != [] [
  #v(section-gap)
  #section-label("Summary")
  #v(label-gap)
  #body-text[#summary]
]

// Experience
#if experience.len() > 0 [
  #v(section-gap)
  #section-label("Experience")
  #v(label-gap)
  #for exp in experience [
    #{
      let company = if type(exp) == dictionary { exp.at("company", default: "") } else { str(exp) }
      let role = if type(exp) == dictionary { exp.at("role", default: "") } else { "" }
      let dates = if type(exp) == dictionary { exp.at("dates", default: "") } else { "" }
      let bullets = if type(exp) == dictionary { exp.at("bullets", default: ()) } else { () }

      grid(
        columns: (1fr, auto),
        gutter: 8pt,
        [
          #text(size: 10pt, fill: ink, weight: "semibold")[#role]
          #if company != "" [
            #text(size: 9pt, fill: mid)[ at #company]
          ]
        ],
        text(size: 8.5pt, fill: subtle)[#dates],
      )

      if type(bullets) == array {
        for b in bullets [
          #grid(
            columns: (auto, 1fr),
            gutter: 6pt,
            text(size: 8pt, fill: faint)[#sym.bullet],
            text(size: 9pt, fill: mid)[#b],
          )
        ]
      }
      v(para-gap)
    }
  ]
]

// Education
#if education.len() > 0 [
  #v(section-gap)
  #section-label("Education")
  #v(label-gap)
  #for edu in education [
    #{
      let institution = if type(edu) == dictionary { edu.at("institution", default: "") } else { str(edu) }
      let degree = if type(edu) == dictionary { edu.at("degree", default: "") } else { "" }
      let dates = if type(edu) == dictionary { edu.at("dates", default: "") } else { "" }

      grid(
        columns: (1fr, auto),
        gutter: 8pt,
        [
          #text(size: 10pt, fill: ink, weight: "semibold")[#institution]
          #if degree != "" [
            #linebreak()
            #text(size: 9pt, fill: mid)[#degree]
          ]
        ],
        text(size: 8.5pt, fill: subtle)[#dates],
      )
      v(para-gap / 2)
    }
  ]
]

// Skills
#if skills.len() > 0 [
  #v(section-gap)
  #section-label("Skills")
  #v(label-gap)
  #text(size: 9pt, fill: mid)[#skills.join("  ·  ")]
]
