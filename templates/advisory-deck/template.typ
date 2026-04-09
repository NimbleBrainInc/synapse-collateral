// NimbleBrain AI Advisory — 2-Page Capability PDF

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
#let font-display = "Didot"
#let font-body = "Avenir Next"
// === END THEME ===

// ============================================================
// PAGE SETUP
// ============================================================

#set page(
  paper: "us-letter",
  margin: (top: 0pt, bottom: 1.4cm, left: 2.2cm, right: 2.2cm),
  footer: none,
)

#set text(font: font-body, size: 9pt, fill: dark, weight: "regular")
#set par(justify: false, leading: 0.6em)
#set heading(numbering: none)

// ============================================================
// HELPERS
// ============================================================

#let pillar-card(num, title, body) = {
  block(
    width: 100%,
    inset: (x: 12pt, y: 12pt),
    radius: 5pt,
    fill: blue-wash,
  )[
    #grid(
      columns: (auto, 1fr),
      gutter: 10pt,
      align(top)[
        #block(
          width: 26pt,
          height: 26pt,
          radius: 5pt,
          fill: blue,
          inset: 0pt,
        )[
          #align(center + horizon)[
            #text(size: 11pt, fill: white, weight: "bold")[#num]
          ]
        ]
      ],
      [
        #text(size: 10pt, weight: "semibold", fill: ink)[#title]
        #v(2pt)
        #text(size: 8.5pt, fill: mid, weight: "regular")[#body]
      ],
    )
  ]
}

#let scenario(title, body) = {
  grid(
    columns: (auto, 1fr),
    gutter: 6pt,
    align(top)[#text(size: 8pt, fill: blue, weight: "bold")[#sym.diamond.filled]],
    [
      #text(size: 9pt, weight: "semibold", fill: ink)[#title]
      #h(4pt)
      #text(size: 8.5pt, fill: mid)[#body]
    ],
  )
}

#let step-box(number, title, body) = {
  block(
    width: 100%,
    inset: (x: 10pt, y: 10pt),
    radius: 5pt,
    fill: wash,
  )[
    #grid(
      columns: (auto, 1fr),
      gutter: 8pt,
      align(top + center)[
        #block(
          width: 22pt,
          height: 22pt,
          radius: 11pt,
          fill: blue,
          inset: 0pt,
        )[
          #align(center + horizon)[
            #text(size: 9pt, weight: "bold", fill: white)[#number]
          ]
        ]
      ],
      [
        #text(size: 10pt, weight: "semibold", fill: ink)[#title]
        #v(2pt)
        #text(size: 8.5pt, fill: mid)[#body]
      ],
    )
  ]
}

// ════════════════════════════════════════════════════════════
// PAGE 1
// ════════════════════════════════════════════════════════════

// Top accent bar
#block(
  width: 100%,
  height: 4pt,
  fill: gradient.linear(blue, cyan),
)

#v(0.7cm)

// Header with company descriptor
#grid(
  columns: (1fr, auto),
  align: (left + horizon, right + horizon),
  [
    #image("/assets/nimblebrain-logo-color-dark-text.png", width: 110pt)
  ],
  [
    #text(size: 7.5pt, fill: subtle, weight: "medium", tracking: 0.5pt)[AI ADVISORY & ENGINEERING]
  ],
)

#v(0.5cm)

// Headline
#text(font: font-display, size: 30pt, fill: ink, weight: "regular")[
  Your competitors aren't waiting. \
  #text(style: "italic")[Neither should you.]
]

#v(0.25cm)

// Positioning
#{
  set par(leading: 0.65em)
  text(size: 9.5pt, fill: ink, weight: "medium")[
    NimbleBrain is an AI advisory and engineering firm that builds production automation for mid-market companies. We handle strategy, engineering, and ongoing operations — so AI actually works in your business, not just in a demo.
  ]
}

#v(0.5cm)

// Section label
#text(size: 7pt, fill: blue, weight: "semibold", tracking: 1.5pt)[WHAT WE BUILD FOR YOU]
#v(0.2cm)

// Pillar cards
#grid(
  columns: (1fr, 1fr),
  gutter: 10pt,

  pillar-card(
    "01",
    "Operations Automation",
    "Manual workflows become AI-operated processes — intake, routing, follow-up, reporting — all running on your business rules.",
  ),

  pillar-card(
    "02",
    "Tool Integration",
    "AI that plugs into Salesforce, Zoho, Slack, HubSpot, QuickBooks, and 50+ other systems. No rip-and-replace.",
  ),

  pillar-card(
    "03",
    "Document Generation",
    "Proposals, quotes, invoices, and briefs created from conversations and data. Minutes after a call, branded and accurate.",
  ),

  pillar-card(
    "04",
    "AI-Powered Teams",
    "Every employee gets an AI assistant trained on your rules, processes, and data. Not a generic chatbot — one built for your company.",
  ),
)

#v(0.3cm)

// Social proof bridge
#text(size: 8.5pt, fill: mid, style: "italic")[
  Deployed across energy, automotive, real estate, and financial services.
]

#v(0.45cm)

// Section label
#text(size: 7pt, fill: blue, weight: "semibold", tracking: 1.5pt)[IN PRACTICE]
#v(0.25cm)

// Scenarios — 2-column
#grid(
  columns: (1fr, 1fr),
  column-gutter: 16pt,
  row-gutter: 12pt,

  scenario(
    "Sales follow-up",
    "AI finds 200 stale CRM leads, drafts personalized follow-ups, and queues them for your team to review and send.",
  ),
  scenario(
    "Quote generation",
    "A rep finishes a call. 90 seconds later, a branded proposal lands in the prospect's inbox — priced from your rules.",
  ),
  scenario(
    "Service triage",
    "AI reads, categorizes, and routes tickets. Resolves the simple ones. Escalates the rest with full context.",
  ),
  scenario(
    "Weekly reporting",
    "Ask \"What happened this week?\" and get a formatted summary pulled from your actual systems.",
  ),
  scenario(
    "Employee onboarding",
    "A new hire triggers the sequence: accounts created, docs sent, training scheduled, manager notified.",
  ),
  scenario(
    "Invoice processing",
    "AI extracts invoices, matches them to POs, flags exceptions, and routes approvals automatically.",
  ),
)

// Push callout toward bottom
#v(1fr)

// Bridge callout
#block(
  width: 100%,
  inset: (x: 16pt, y: 12pt),
  radius: 5pt,
  stroke: (left: 3pt + blue),
  fill: wash,
)[
  #text(size: 9pt, fill: ink, weight: "medium")[Fixed-scope engagements starting at \$10K.] #text(size: 9pt, fill: mid)[We build working systems in weeks, not quarters. No open-ended consulting. See how it works on the next page.]
]

#v(0.3cm)

// Footer
#line(length: 100%, stroke: 0.3pt + rule-color)
#v(4pt)
#grid(
  columns: (1fr, auto),
  align: (left + horizon, right + horizon),
  text(size: 7pt, fill: subtle)[nimblebrain.ai],
  text(size: 7pt, fill: subtle)[1 / 2],
)

// ════════════════════════════════════════════════════════════
// PAGE 2
// ════════════════════════════════════════════════════════════

#pagebreak()

#set page(margin: (top: 0pt, bottom: 1.4cm, left: 2.2cm, right: 2.2cm))

// Top accent bar
#block(
  width: 100%,
  height: 4pt,
  fill: gradient.linear(blue, cyan),
)

#v(0.6cm)

// Header
#grid(
  columns: (1fr, auto),
  align: (left + horizon, right + horizon),
  [
    #image("/assets/nimblebrain-logo-color-dark-text.png", width: 110pt)
  ],
  [
    #text(size: 7.5pt, fill: subtle, weight: "medium", tracking: 0.5pt)[AI ADVISORY & ENGINEERING]
  ],
)

#v(0.4cm)

// Section label
#text(size: 7pt, fill: blue, weight: "semibold", tracking: 1.5pt)[HOW WE WORK]
#v(0.15cm)

#text(font: font-display, size: 24pt, fill: ink, weight: "regular")[
  See it working #text(style: "italic")[before] you commit.
]

#v(0.4cm)

// Three steps
#grid(
  columns: (1fr, 1fr, 1fr),
  gutter: 10pt,

  step-box(
    "1",
    "Discovery",
    "We learn your business, map your workflows, and build 2-3 working demos with your real data. You see it before you commit.",
  ),

  step-box(
    "2",
    "Pilot",
    "We build and deploy production automations. Fixed scope, fixed price. Working systems, not a strategy deck. Weeks, not quarters.",
  ),

  step-box(
    "3",
    "Grow",
    "Add automations as you see results. Each builds on the foundation. We maintain it or hand it off. Your call.",
  ),
)

#v(0.4cm)

// Divider
#line(length: 100%, stroke: 0.3pt + rule-color)

#v(0.3cm)

// Section label
#text(size: 7pt, fill: blue, weight: "semibold", tracking: 1.5pt)[WHY NIMBLEBRAIN]
#v(0.2cm)

#grid(
  columns: (1fr, 1fr, 1fr),
  gutter: 14pt,

  block(width: 100%)[
    #text(size: 10pt, weight: "semibold", fill: ink)[We build, not just advise.]
    #v(3pt)
    #text(size: 8.5pt, fill: mid)[
      We've done this before — same tools, same process, different businesses. When we say "we'll automate that," we have the engine to back it up. No subcontractors. No vaporware.
    ]
  ],

  block(width: 100%)[
    #text(size: 10pt, weight: "semibold", fill: ink)[You own everything.]
    #v(3pt)
    #text(size: 8.5pt, fill: mid)[
      Every automation we build is yours — exportable, inspectable, built on open-source tools. No lock-in. If you want to bring it in-house later, you can. Nothing held hostage.
    ]
  ],

  block(width: 100%)[
    #text(size: 10pt, weight: "semibold", fill: ink)[Production in weeks.]
    #v(3pt)
    #text(size: 8.5pt, fill: mid)[
      Traditional consulting: 6-12 months. We deployed a fully automated quote generation system for an energy company in 4 weeks. Fixed scope, real outcomes, fast.
    ]
  ],
)

#v(0.3cm)

// Divider
#line(length: 100%, stroke: 0.3pt + rule-color)

#v(0.3cm)

// Team
#text(size: 7pt, fill: blue, weight: "semibold", tracking: 1.5pt)[WHO YOU'LL WORK WITH]
#v(0.2cm)

#grid(
  columns: (1fr, 1fr),
  gutter: 20pt,

  grid(
    columns: (auto, 1fr),
    gutter: 12pt,
    align(top)[
      #block(
        width: 52pt,
        height: 52pt,
        radius: 26pt,
        clip: true,
      )[
        #image("/assets/mat-headshot.png", width: 52pt)
      ]
    ],
    [
      #text(size: 10pt, weight: "semibold", fill: ink)[Mathew Goldsborough]
      #h(4pt)
      #text(size: 8.5pt, fill: blue, weight: "medium")[CEO]
      #v(3pt)
      #text(size: 8.5pt, fill: mid)[
        Former defense and enterprise systems engineer. Builds production AI infrastructure and runs NimbleBrain on the same technology deployed for clients.
      ]
    ],
  ),

  grid(
    columns: (auto, 1fr),
    gutter: 12pt,
    align(top)[
      #block(
        width: 52pt,
        height: 52pt,
        radius: 26pt,
        clip: true,
      )[
        #image("/assets/matt-headshot.jpg", width: 52pt)
      ]
    ],
    [
      #text(size: 10pt, weight: "semibold", fill: ink)[Matthew Gerard]
      #h(4pt)
      #text(size: 8.5pt, fill: blue, weight: "medium")[Principal]
      #v(3pt)
      #text(size: 8.5pt, fill: mid)[
        Finance and technology strategist. \$6.5B+ in structured transactions across project finance, capital markets, and infrastructure development.
      ]
    ],
  ),
)

// Push CTA to bottom
#v(1fr)

// CTA block
#block(
  width: 100%,
  fill: dark-bg,
  radius: 6pt,
  inset: (x: 20pt, y: 16pt),
)[
  #grid(
    columns: (1fr, auto),
    gutter: 16pt,
    align: (left + horizon, right + horizon),

    [
      #text(size: 13pt, weight: "bold", fill: white)[See it working in your business.]
      #v(3pt)
      #text(size: 9pt, fill: subtle-on-dark)[
        30 minutes. No pitch deck. We'll discuss your operations and show you what's possible.
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
  text(size: 7pt, fill: subtle)[2 / 2],
)
