// Deep Agent Best Practices — Agency Operations Edition

// === THEME ===
#let primary = rgb("#0066FF")
#let cyan-accent = rgb("#00D4FF")
#let ink = rgb("#0F172A")
#let dark = rgb("#1E293B")
#let mid = rgb("#475569")
#let subtle = rgb("#94A3B8")
#let faint = rgb("#CBD5E1")
#let wash = rgb("#F1F5F9")
#let paper = rgb("#FAFBFC")
#let dark-bg = rgb("#0F172A")
#let dark-surface = rgb("#1E293B")
#let amber = rgb("#F59E0B")
#let amber-wash = rgb("#FFFBEB")
#let amber-dark = rgb("#92400E")
#let success = rgb("#10B981")
#let error = rgb("#EF4444")
#let purple = rgb("#8B5CF6")
#let font-display = "Plus Jakarta Sans"
#let font-body = "Avenir Next"
#let font-code = "JetBrains Mono"
#let pad-x = 56pt
#let pad-y = 48pt
#let section-gap = 28pt
#let compact-gap = 20pt
#let label-gap = 3pt
#let headline-gap = 10pt
#let para-gap = 10pt
#let card-gap = 14pt
// === END THEME ===

// ════════════════════════════════════════════════════════════════
// COMPONENTS
// ════════════════════════════════════════════════════════════════

#let section-label(label, color: primary) = {
  text(font: font-display, size: 7.5pt, fill: color, weight: "semibold", tracking: 2pt)[#upper(label)]
}

#let display-heading(body, size: 22pt) = {
  text(font: font-display, size: size, fill: ink, weight: "light", tracking: -0.3pt, body)
}

#let display-heading-dark(body, size: 22pt) = {
  text(font: font-display, size: size, fill: white, weight: "light", tracking: -0.3pt, body)
}

#let body-text(body) = {
  set par(leading: 8pt, spacing: 10pt)
  text(size: 10pt, fill: mid, body)
}

#let callout-box(body, accent: primary) = {
  block(
    width: 100%,
    inset: (left: 16pt, right: 16pt, top: 12pt, bottom: 12pt),
    radius: (right: 4pt),
    stroke: (left: 3pt + accent),
    fill: wash,
  )[
    #set text(size: 9.5pt, fill: dark)
    #set par(leading: 8pt)
    #body
  ]
}

#let pull-quote(body) = {
  block(width: 100%, inset: (x: 24pt, y: 16pt))[
    #text(font: font-display, size: 14pt, fill: ink, weight: "light", style: "italic", body)
  ]
}

#let page-footer(label: "Deep Agent Best Practices") = {
  context {
    let pg = counter(page).get().first()
    if pg > 1 [
      #set text(size: 7pt, fill: subtle, tracking: 0.5pt)
      #line(length: 100%, stroke: 0.3pt + faint)
      #v(6pt)
      #grid(
        columns: (auto, 1fr, auto),
        gutter: 8pt,
        align: (left + horizon, left + horizon, right + horizon),
        image("/assets/nimblebrain-icon-color.png", height: 8pt),
        [#label],
        [#pg],
      )
    ]
  }
}

// ════════════════════════════════════════════════════════════════
// DOCUMENT SETUP
// ════════════════════════════════════════════════════════════════

#set page(
  paper: "us-letter",
  margin: (top: 48pt, bottom: 56pt, left: pad-x, right: pad-x),
  footer: page-footer(label: [Deep Agent Best Practices — Agency Operations]),
)
#set text(font: font-body, size: 9.5pt, fill: dark, weight: "regular")
#set par(justify: false, leading: 7pt, spacing: 10pt)

// ════════════════════════════════════════════════════════════════
// COVER PAGE
// ════════════════════════════════════════════════════════════════

#page(margin: 0pt, footer: none)[
  #block(width: 100%, height: 100%, fill: dark-bg)[
    #block(width: 100%, height: 4pt, fill: gradient.linear(primary, cyan-accent))

    #block(inset: (x: 56pt, top: 56pt))[
      #image("/assets/nimblebrain-logo-white.png", height: 24pt)
    ]

    #v(1fr)
    #block(inset: (x: 56pt))[
      #text(font: font-display, size: 36pt, fill: white, weight: "light", tracking: -0.8pt)[
        Deep Agent#linebreak()Best Practices
      ]
      #v(12pt)
      #block(width: 48pt, height: 3pt, fill: gradient.linear(primary, cyan-accent))
      #v(16pt)
      #text(font: font-display, size: 14pt, fill: subtle, weight: "regular")[
        How to Turn 15 Tools into One System
      ]
      #v(24pt)
      #text(size: 9.5pt, fill: rgb("#64748B"), weight: "regular")[
        A practical guide for agency operators running outbound#linebreak()
        at scale across too many dashboards
      ]
      #v(12pt)
      #block(
        inset: (x: 12pt, y: 6pt),
        radius: 3pt,
        fill: rgb("#1E293B"),
      )[
        #text(size: 8pt, fill: subtle, weight: "regular")[Agency Operations Edition]
      ]
    ]
    #v(1fr)

    #block(
      width: 100%,
      inset: (x: 56pt, y: 24pt),
      fill: rgb("#0a1220"),
    )[
      #text(size: 8pt, fill: rgb("#475569"))[
        nimblebrain.ai
      ]
    ]
  ]
]

// ════════════════════════════════════════════════════════════════
// IMAGINE THIS
// ════════════════════════════════════════════════════════════════

#section-label("Imagine This", color: cyan-accent)
#v(label-gap)
#display-heading[Your Tuesday Morning]
#v(headline-gap)

#body-text[
  You're running campaigns for 6 clients simultaneously. Each one has its own domain sets, inbox rotation schedules, Clay enrichment tables, and EmailBison sending sequences. You open your laptop. "What's the health of my infrastructure?"
]

#v(section-gap)

#callout-box(accent: cyan-accent)[
  "102 Google inboxes and 304 Outlook inboxes active. Google deliverability at 74% — down from 78%, 3 domains showing warm-up issues. Paused sending and flagged for EmailGuard. Outlook healthy at 96%. Sends yesterday: 3,050. Clay enrichment for NovaTech finished — 1,247 verified contacts pushed to EmailBison. MasterInbox: 23 positive replies across 4 client inboxes need triage. CloseCRM: 8 meetings booked this week."
]

#v(section-gap)

#body-text[
  You didn't log into 6 tools separately. You asked one question and got a unified picture across your entire stack.
]

#v(section-gap)

#block(breakable: false)[
#section-label("Imagine This", color: cyan-accent)
#v(label-gap)
#display-heading[Client Onboarding]
#v(headline-gap)

#body-text[
  New client signed yesterday. Normally 2–3 hours of setup. Today you say: "New client: Apex Growth Partners. B2B SaaS, VP Sales and CRO, 50–500 employees, fintech and healthtech. Standard setup."
]
]

#v(section-gap)

#callout-box(accent: cyan-accent)[
  "8 domains and 16 inboxes provisioned. 50/50 Google/Outlook split. Warm-up initiated — send-ready in 14 days. Clay table built, first batch: 842 contacts. LeadMagic verification running. 3 email sequences drafted from your top templates. RevOps tracking configured. n8n workflows connected. Cal.com booking link created. Ready for your review."
]

#v(section-gap)

#callout-box[
  What used to be half a day of tab-switching is now a conversation. The client is infrastructure-ready before their kick-off call tomorrow. Not everything provisions perfectly the first time. When a domain fails verification or an inbox gets flagged during warm-up, the system catches it and routes it to you before it affects deliverability.
]

// ════════════════════════════════════════════════════════════════
// THE META PROBLEM
// ════════════════════════════════════════════════════════════════

#block(breakable: false)[
#section-label("The Meta Problem")
#v(label-gap)
#display-heading[Your Own Growth Engine]
#v(headline-gap)

#body-text[
  The stack you manage for clients is the same stack you run internally to grow LeadForce. Every efficiency you gain on the client side compounds on yours.
]
]

#v(section-gap)

#callout-box(accent: cyan-accent)[
  "LeadForce internal outbound: 420 emails yesterday. 2.9% positive reply rate. 3 meetings booked — SaaS founder, marketing director, agency owner exploring white-label. Trigify flagged a social signal: VP of Growth at a healthtech company posted about 'scaling outbound without hiring SDRs.' Moved to priority follow-up, personal email drafted referencing his post."
]

#v(section-gap)

#body-text[
  You're not just running client campaigns. You're running your own growth engine through the same system.
]

// ════════════════════════════════════════════════════════════════
// THE SCORECARD
// ════════════════════════════════════════════════════════════════

#block(breakable: false)[
#section-label("The Scorecard")
#v(label-gap)
#display-heading[Your Monday Morning]
#v(headline-gap)
]

#callout-box(accent: cyan-accent)[
  "6 clients. 18,400 sends last week. 3.2% reply rate (up from 2.8%). 14 meetings booked. Top performer: Apex Growth at 4.1%. Underperformer: Meridian SaaS at 1.4% — ICP list too broad, tighter Clay filter drafted. You're approaching 1,530 Google sends/day cap. Recommend adding 10 domains for April onboarding. Cost: ~\$47/month. Total infrastructure: \$2,715/month. ROI per meeting booked: ~\$48."
]

#v(section-gap)

#body-text[
  You used to spend Monday mornings in 6 dashboards pulling numbers into a spreadsheet. Now you walk into client calls with a unified picture and specific recommendations.
]

#v(section-gap)

// ════════════════════════════════════════════════════════════════
// CLOSING
// ════════════════════════════════════════════════════════════════

#pagebreak()

#block(breakable: false)[
#section-label("The Difference")
#v(label-gap)
#display-heading[This Is Deep Agent]
#v(headline-gap)

#body-text[
  It's not the surface-level AI you've been using. It's not ChatGPT. Not a chatbot. It doesn't start from scratch every time you open it. It knows your business, your contacts, your pipeline, your voice, and your history. It works across every channel you already use. Text, email, voice memo, laptop. It never forgets.
]
]

#v(section-gap)

#pull-quote[
  This is what NimbleBrain's Deep Agent™ looks like.
]

#v(section-gap)

#section-label("How This Works")
#v(label-gap)
#display-heading[Your Workflow Becomes Your System]
#v(6pt)
#body-text[
  None of this is hypothetical. It's an illustration of what happens when someone maps your actual workflow, connects your actual systems, and builds AI orchestration around the way you already operate.
]
#v(headline-gap)

#grid(
  columns: (auto, 1fr),
  gutter: 14pt,
  block(width: 28pt, height: 28pt, radius: 4pt, fill: primary)[
    #align(center + horizon)[#text(font: font-display, size: 14pt, fill: white, weight: "bold")[1]]
  ],
  [
    #text(font: font-display, size: 10.5pt, fill: ink, weight: "semibold")[We start with you.]
    #v(4pt)
    #text(size: 9pt, fill: mid)[Not with software. We map how you actually work, where information lives, how it flows, where things fall through cracks, and what you wish happened automatically.]
  ],
)

#v(para-gap)
#line(length: 100%, stroke: 0.3pt + faint)
#v(para-gap)

#grid(
  columns: (auto, 1fr),
  gutter: 14pt,
  block(width: 28pt, height: 28pt, radius: 4pt, fill: cyan-accent)[
    #align(center + horizon)[#text(font: font-display, size: 14pt, fill: white, weight: "bold")[2]]
  ],
  [
    #text(font: font-display, size: 10.5pt, fill: ink, weight: "semibold")[We connect your existing tools.]
    #v(4pt)
    #text(size: 9pt, fill: mid)[We don't replace your email, your systems, or your processes. We connect them so data flows between them without you being the middleware.]
  ],
)

#v(para-gap)
#line(length: 100%, stroke: 0.3pt + faint)
#v(para-gap)

#grid(
  columns: (auto, 1fr),
  gutter: 14pt,
  block(width: 28pt, height: 28pt, radius: 4pt, fill: purple)[
    #align(center + horizon)[#text(font: font-display, size: 14pt, fill: white, weight: "bold")[3]]
  ],
  [
    #text(font: font-display, size: 10.5pt, fill: ink, weight: "semibold")[We build AI agents around your workflow.]
    #v(4pt)
    #text(size: 9pt, fill: mid)[Not a chatbot. Not a dashboard. Agents that do specific jobs: surface what matters, handle the busywork, keep everything coordinated.]
  ],
)

#v(para-gap)
#line(length: 100%, stroke: 0.3pt + faint)
#v(para-gap)

#grid(
  columns: (auto, 1fr),
  gutter: 14pt,
  block(width: 28pt, height: 28pt, radius: 4pt, fill: amber)[
    #align(center + horizon)[#text(font: font-display, size: 14pt, fill: white, weight: "bold")[4]]
  ],
  [
    #text(font: font-display, size: 10.5pt, fill: ink, weight: "semibold")[We meet you where you are.]
    #v(4pt)
    #text(size: 9pt, fill: mid)[Text, email, voice memo, laptop. The interface isn't the point. You talk to your AI the way you'd talk to a trusted chief of staff. It handles the rest.]
  ],
)

// ════════════════════════════════════════════════════════════════
// CTA PAGE
// ════════════════════════════════════════════════════════════════

#page(margin: 0pt, footer: none)[
  #block(width: 100%, height: 100%, fill: dark-bg)[
    #block(width: 100%, height: 4pt, fill: gradient.linear(primary, cyan-accent))

    #v(1fr)
    #block(inset: (x: 56pt))[
      #text(font: font-display, size: 13pt, fill: subtle, weight: "light", style: "italic")[
        Your stack becomes a system. Your clients get better results. Your margins improve. Your systems work for you. Not you working for your systems.
      ]

      #v(28pt)

      #display-heading-dark(size: 26pt)[Interested?]

      #v(20pt)

      #text(size: 10pt, fill: subtle)[
        Let's have a 20-minute conversation about what this looks like for your situation. No pitch deck. No demo. Just a conversation about how you operate and what could be better.
      ]

      #v(28pt)

      #block(
        width: 100%,
        inset: (x: 20pt, y: 14pt),
        radius: 6pt,
        stroke: 1pt + primary,
        fill: rgb("#0a1220"),
      )[
        #text(font: font-display, size: 12pt, fill: white, weight: "semibold")[Let's Talk]
        #v(6pt)
        #text(size: 9pt, fill: subtle)[
          Book a 20-minute call. We'll talk about how you operate and where AI can remove the busywork.
        ]
        #v(10pt)
        #block(
          inset: (x: 16pt, y: 8pt),
          radius: 4pt,
          fill: primary,
        )[
          #link("https://nimblebrain.ai/demo")[#text(size: 9pt, fill: white, weight: "semibold")[Book a call #sym.arrow.r]]
        ]
      ]

      #v(24pt)

      #text(size: 7.5pt, fill: rgb("#64748B"), weight: "semibold", tracking: 1.5pt)[YOUR GUIDES]
      #v(12pt)
      #grid(
        columns: (1fr, 1fr),
        gutter: 24pt,

        grid(
          columns: (auto, 1fr),
          gutter: 12pt,
          block(radius: 50%, clip: true)[
            #image("/assets/mat-headshot.png", width: 40pt)
          ],
          [
            #text(font: font-display, size: 9pt, fill: white, weight: "semibold")[Mat Goldsborough]
            #v(2pt)
            #text(size: 8pt, fill: subtle)[CEO, NimbleBrain. Built agent infrastructure for defense, fintech, and agriculture.]
          ],
        ),

        grid(
          columns: (auto, 1fr),
          gutter: 12pt,
          block(radius: 50%, clip: true)[
            #image("/assets/matt-headshot.jpg", width: 40pt)
          ],
          [
            #text(font: font-display, size: 9pt, fill: white, weight: "semibold")[Matt Gerard]
            #v(2pt)
            #text(size: 8pt, fill: subtle)[Principal, NimbleBrain. Operations leader who turns AI strategy into repeatable systems.]
          ],
        ),
      )
    ]
    #v(1fr)

    #block(
      width: 100%,
      inset: (x: 56pt, y: 24pt),
      fill: rgb("#0a1220"),
    )[
      #grid(
        columns: (auto, 1fr),
        gutter: 12pt,
        image("/assets/nimblebrain-logo-white.png", height: 16pt),
        align(right + horizon)[#text(size: 8pt, fill: rgb("#475569"))[nimblebrain.ai]],
      )
    ]
  ]
]
