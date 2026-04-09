// Deep Agent Method — 1-Page Collateral

// === THEME ===
#let blue = rgb("#0066FF")
#let cyan = rgb("#00D4FF")
#let ink = rgb("#0F172A")
#let dark = rgb("#1E293B")
#let mid = rgb("#475569")
#let subtle = rgb("#64748B")
#let subtle-on-dark = rgb("#94A3B8")
#let faint = rgb("#CBD5E1")
#let wash = rgb("#F8FAFC")
#let blue-wash = rgb("#EFF6FF")
#let rule-color = rgb("#E2E8F0")
#let dark-bg = rgb("#0d1b2a")
#let green = rgb("#16A34A")
#let green-wash = rgb("#F0FDF4")
#let red-muted = rgb("#94A3B8")
#let font-display = "Didot"
#let font-body = "Avenir Next"
// === END THEME ===

// ============================================================
// PAGE SETUP
// ============================================================

#set page(
  paper: "us-letter",
  margin: (top: 0pt, bottom: 1.2cm, left: 2.2cm, right: 2.2cm),
  footer: none,
)

#set text(font: font-body, size: 9pt, fill: dark, weight: "regular")
#set par(justify: false, leading: 0.6em)
#set heading(numbering: none)

// ============================================================
// HELPERS
// ============================================================

#let week-block(week-label, title, body) = {
  block(
    width: 100%,
    inset: (x: 10pt, y: 9pt),
    radius: 5pt,
    fill: blue-wash,
  )[
    #text(size: 6.5pt, fill: blue, weight: "bold", tracking: 1pt)[#week-label]
    #v(2pt)
    #text(size: 9.5pt, weight: "semibold", fill: ink)[#title]
    #v(2pt)
    #text(size: 8pt, fill: mid)[#body]
  ]
}

#let deliverable-row(get, not-this) = {
  grid(
    columns: (1fr, 1fr),
    gutter: 8pt,
    [
      #grid(
        columns: (auto, 1fr),
        gutter: 5pt,
        align(top)[#text(size: 8pt, fill: green, weight: "bold")[+]],
        text(size: 8pt, fill: ink, weight: "medium")[#get],
      )
    ],
    [
      #grid(
        columns: (auto, 1fr),
        gutter: 5pt,
        align(top)[#text(size: 8pt, fill: red-muted, weight: "bold")[--]],
        text(size: 8pt, fill: red-muted, style: "italic")[#not-this],
      )
    ],
  )
}

// ============================================================
// PAGE
// ============================================================

// Top accent bar
#block(
  width: 100%,
  height: 4pt,
  fill: gradient.linear(blue, cyan),
)

#v(0.5cm)

// Header
#grid(
  columns: (1fr, auto),
  align: (left + horizon, right + horizon),
  [
    #image("/assets/nimblebrain-logo-color-dark-text.png", width: 110pt)
  ],
  [
    #text(size: 7pt, fill: blue, weight: "semibold", tracking: 1.5pt)[THE DEEP AGENT#super[TM] METHOD]
  ],
)

#v(0.4cm)

// Headline
#text(font: font-display, size: 28pt, fill: ink, weight: "regular")[
  We embed. We build. \
  #text(style: "italic")[We leave you better.]
]

#v(0.2cm)

// Positioning
#{
  set par(leading: 0.65em)
  text(size: 9.5pt, fill: ink, weight: "medium")[
    NimbleBrain is the anti-consultancy. We drop a small, AI-native team into your operations for 4 weeks. We learn how your business actually works. We build production automations from day one. When we leave, you own everything — and the system keeps getting smarter without us.
  ]
}

#v(0.4cm)

// -- THE 4-WEEK EMBED --
#text(size: 7pt, fill: blue, weight: "semibold", tracking: 1.5pt)[THE 4-WEEK EMBED]
#v(0.2cm)

#grid(
  columns: (1fr, 1fr, 1fr),
  gutter: 8pt,

  week-block(
    "WEEK 1",
    "Immersion",
    "We're inside your workflows — Slack, standups, real work. We build while we learn. First automations ship by Friday.",
  ),

  week-block(
    "WEEKS 2–3",
    "Saturation",
    "Automations compound across departments. Your tribal knowledge gets encoded into AI skills that agents can execute.",
  ),

  week-block(
    "WEEK 4",
    "Installation",
    "The recursive loop goes live. Agents monitor agents. Independence kit delivered. Expansion map handed over.",
  ),
)

#v(0.35cm)

// -- WHAT YOU WALK AWAY WITH --
#text(size: 7pt, fill: blue, weight: "semibold", tracking: 1.5pt)[WHAT YOU WALK AWAY WITH]
#v(0.15cm)

#block(
  width: 100%,
  inset: (x: 10pt, y: 10pt),
  radius: 5pt,
  fill: wash,
)[
  #grid(
    columns: (1fr),
    row-gutter: 6pt,

    deliverable-row(
      "8–12 working automations in production",
      "Not a recommendations report",
    ),
    deliverable-row(
      "Business expertise encoded as AI skills",
      "Not a training manual nobody reads",
    ),
    deliverable-row(
      "Live integrations to your actual tools",
      "Not an architecture diagram",
    ),
    deliverable-row(
      "A self-improving system that learns",
      "Not a one-time build that decays",
    ),
    deliverable-row(
      "Embed Report with ROI scorecard",
      "Not a 50-page assessment",
    ),
    deliverable-row(
      "Expansion map with your next 20 opportunities",
      "Not a vague transformation roadmap",
    ),
    deliverable-row(
      "Everything open-source, everything yours",
      "Not vendor lock-in",
    ),
  )
]

#v(0.35cm)

// -- WHY NIMBLEBRAIN --
#text(size: 7pt, fill: blue, weight: "semibold", tracking: 1.5pt)[WHY NIMBLEBRAIN]
#v(0.15cm)

#grid(
  columns: (1fr, 1fr, 1fr),
  gutter: 14pt,

  block(width: 100%)[
    #text(size: 9.5pt, weight: "semibold", fill: ink)[We embed, not advise.]
    #v(2pt)
    #text(size: 8pt, fill: mid)[
      Same Slack channels, same standups, same problems. We build alongside your team with our own AI-native tools — no subcontractors, no vaporware.
    ]
  ],

  block(width: 100%)[
    #text(size: 9.5pt, weight: "semibold", fill: ink)[You own everything.]
    #v(2pt)
    #text(size: 8pt, fill: mid)[
      Every automation, every skill, every integration — exportable, inspectable, open source. If you want to bring it in-house, you can. Nothing held hostage.
    ]
  ],

  block(width: 100%)[
    #text(size: 9.5pt, weight: "semibold", fill: ink)[Production in weeks.]
    #v(2pt)
    #text(size: 8pt, fill: mid)[
      Traditional consulting takes 6–12 months. We ship working systems in 4 weeks. Fixed scope, real outcomes, fast.
    ]
  ],
)

// Push CTA to bottom
#v(1fr)

// CTA block
#block(
  width: 100%,
  fill: dark-bg,
  radius: 6pt,
  inset: (x: 20pt, y: 14pt),
)[
  #grid(
    columns: (1fr, auto),
    gutter: 16pt,
    align: (left + horizon, right + horizon),

    [
      #text(size: 13pt, weight: "bold", fill: white)[See what 4 weeks can do.]
      #v(3pt)
      #text(size: 9pt, fill: subtle-on-dark)[
        30 minutes. No pitch deck. We'll look at your operations together and show you what's possible.
      ]
      #v(6pt)
      #link("https://nimblebrain.ai/demo")[
        #block(
          inset: (x: 14pt, y: 8pt),
          radius: 4pt,
          fill: blue,
        )[
          #text(size: 9pt, fill: white, weight: "semibold")[Book a Discovery Call #sym.arrow.r]
        ]
      ]
    ],

    [
      #text(size: 9pt, fill: cyan, weight: "medium")[mat\@nimblebrain.ai] \
      #text(size: 9pt, fill: subtle-on-dark)[(808) 498-1809]
    ],
  )
]

#v(4pt)

// Footer
#line(length: 100%, stroke: 0.3pt + rule-color)
#v(4pt)
#grid(
  columns: (1fr, auto),
  align: (left + horizon, right + horizon),
  text(size: 7pt, fill: subtle)[nimblebrain.ai],
  text(size: 7pt, fill: subtle)[The Deep Agent#super[TM] Method — Fixed-scope engagements starting at \$50K],
)
