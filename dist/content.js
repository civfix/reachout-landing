window.ROLA_CONTENT = {
  about: {
    title: "About",
    blocks: [
      { t: "heading", text: "Who are we?" },
      { t: "spread", paras: [
        "Reach Out LA is a nonprofit built on the belief that when a community identifies a problem, its government should actually fix it. We work to make that happen through technology that empowers residents, research that centers the nation's most vulnerable, and a relentless push to make American civic life work the way it was always supposed to.",
        "We started with high school students going directly to Skid Row, the neighborhood with the highest unhoused density in world. We spoke to unhoused individuals and surveyed their needs to bring their experiences into policy conversations. The systems designed to help people too often have no idea what those people actually need. We want the people receiving the services to have a say in what they are receiving.",
        "Civfix is our answer. The app is a community issue reporting, organizing, and social platform that lets any resident — in any American city or town — report infrastructure problems like excess trash, potholes, broken streetlights, and failing public spaces, and have those reports routed directly to the relevant city department. It is much more than just a reporting tool, Civfix is also a social platform. Neighbors can see what others in their community are flagging, rally around shared concerns, and build the kind of collective visibility that makes it hard for problems to be quietly ignored.",
        "The micro goal is straightforward: fewer potholes, faster responses, less friction between a problem and its fix. The macro goal is bigger. We are building toward a national civic infrastructure where no issue goes unheard, where every resident, regardless of their zip code or their familiarity with bureaucracy, has an equal and effective voice in the condition of their community. Right now, the loudest and most connected neighborhoods get the most attention. Civfix is built to change that math.",
        "Our unhoused research program runs alongside Civfix as a parallel effort. We continue to conduct direct, human-centered research on homelessness across the state of California. These are two distinct programs, but they share the same conviction: that good governance starts with actually knowing what's happening in your community, and that the people closest to a problem are always the most important source of truth."
      ], bios: [
        { label: "Leadership", slot: "about-president", src: "images/about-president.webp", name: "Roman Aytur", role: "President", email: "roman@reachoutla.org", bio: [
          "Roman, the founder and President of Reach Out LA, founded the organization whilst in high school with the mission of combating rampant homelessness in Los Angeles through the use of technology and cooperation with local governments. Additionally, through his internship with Matt Mahan's gubernatorial campaign, volunteer work at the St. Francis Center, involvement with Rewrite LA, and work with the California endowment, he discovered a dire need for a more transparent, efficient method for organizing cleanups and connecting citizens to their municipal governments regarding issues affecting their communities. Roman pitched his idea for Civfix, raising funds and recruiting the engineering team, bringing the project to life."
        ]},
        { label: "Engineering Team", slot: "about-eng-1", src: "images/about-eng-1.webp", name: "Theodore Bong", role: "Founding Engineer", email: "theo@reachoutla.org", bio: [
          "Theo is studying Physics at UC Berkeley. He is an experienced programmer, working on various web and video game projects for over 6 years. Primarily focused on software design and user experience, Theo manages frontend software for the Civfix app and information technology for the Reach Out LA organization."
        ]},
        { slot: "about-eng-2", src: "images/about-eng-2.webp", name: "Rudra Patel", role: "Founding Engineer", email: "rudra@reachoutla.org", bio: [
          "Rudra is a Computer Science student on a full-ride academic scholarship at the University of Kentucky. He is an experienced software engineer of 8+ years, publishing programs downloaded by 40,000+ people and developing for video game communities with millions of unique players. Rudra manages the infrastructure, backend software, and DevOps workflows associated with the Civfix app and information technology for the Reach Out LA organization."
        ]}
      ]}
    ]
  },

  mission: {
    title: "Mission",
    blocks: [
      { t: "heading", text: "Founder's message" },
      { t: "spread", together: true, signed: "— Roman Aytur, President", paras: [
        "“I just need to charge my phone for five minutes so I can call my mother.” The barista replied, “I’m sorry sir, you have to make a purchase to use our amenities.” That conversation led to the founding of Reach Out LA. I decided to buy the man a drink so he could call his mother. As we talked, he described the horrors of living in a nearby Santa Monica shelter, saying, “I can’t go back there, I don’t want to go back there, it’s like hell.”",
        "It had never occurred to me that a shelter could be worse than living on the streets, but his voice carried the kind of fear that completely rewired my assumptions. He spoke about the overcrowding, the constant need to protect his belongings from being stolen, and the anxiety that followed him every day. Finally, he said, “It’s safer out here.” I asked him, “What is something I can do that would help you the most, day-to-day?” His answer was simple: “It’s very difficult to charge my phone in order to get in touch with my loved ones.”",
        "That conversation shaped the philosophy behind Reach Out. I wanted to do two things: provide something that could help people immediately, and ask questions that would help me understand how to support people in the long term. After some research, I found a solar-powered portable charger that perfectly addressed the need he had described. Reach Out officially began when a group of 16-year-olds and I drove to Skid Row with a few hundred solar-powered chargers and a questionnaire in hand. From this point, the mission of Reach Out LA has expanded to connecting all citizens with each other and their local governments to bridge the gap between community concerns and real civic action."
      ], media: [
        { slot: "mission-photo-1", src: "images/mission-photo-1.webp" },
        { slot: "mission-photo-2", src: "images/mission-photo-2.webp" },
        { slot: "mission-photo-3", src: "images/mission-photo-3.webp" }
      ]}
    ]
  },

  civfix: {
    title: "Civfix",
    blocks: [
      { t: "heading", text: "Overview" },
      { t: "spread", together: true, sidecap: true, paras: [
        "Every neighborhood has problems that fall through the cracks: an illegally dumped couch, a graffiti-covered wall, a pothole that's been there for months, a streetlight that never comes back on. Reporting them is harder than it should be: working out which city department is responsible, dig up the right form or phone number, and then you usually never hear back. Most people give up, and the problem lingers. Meanwhile plenty of neighbors would happily pitch in to clean things up; they just have no easy way to find each other or get organized.",
        "Civfix turns all of that into a few taps on a map. See a problem, drop a pin, snap a photo or a quick video, and you're done. We automatically work out which agency is responsible based on exactly where the pin is and forward the report for you, allowing you to easily track and follow-up on the report. The same map shows what neighbors have already reported and which cleanups are happening nearby, so the app is equal parts report the problem and help fix it.",
        "Reporting takes under a minute and doesn't require knowing who to call. You capture a photo or short video, the app tags the exact location automatically, and you pick what kind of issue it is: illegal dumping, graffiti, a pothole or broken sidewalk, a broken streetlight or flooding, overgrown brush, or something else.",
        "Civfix is more than just a complaint box, our platform enables neighbors to organize independent community events. Anyone can host a cleanup, and others can RSVP, see who's going and what to bring, and coordinate in a group chat right inside the app. You can follow organizers and neighbors, message people directly, and keep up with a feed of what's happening in your neighborhood.",
        "With a native iOS/Android app for reporting on the spot, and a web app that does everything the same way in a browser, Civfix meets people wherever they are.<br><br>Download the mobile app or visit our web app today!<br>Web: <a href=\"https://civfix.org/\" target=\"_blank\" rel=\"noopener\">civfix.org</a><br>iOS: <a href=\"https://ios.civfix.org/\" target=\"_blank\" rel=\"noopener\">ios.civfix.org</a><br>Android: <a href=\"https://android.civfix.org\" target=\"_blank\" rel=\"noopener\">android.civfix.org</a>"
      ], media: [
        { slot: "civfix-photo-3", src: "images/civfix-photo-3.webp", cap: "Photo/video + auto-location + typed category, routed to the right agency." },
        { slot: "civfix-report-v2", src: "images/civfix-report-details.webp", cap: "A live status timeline: submitted → forwarded to LA Bureau of Street Services → verified → cleanup scheduled." },
        { slot: "civfix-event-v2", src: "images/civfix-event-details.webp", cap: "Join or host a cleanup: RSVP, who's going, what to bring, and a built-in group chat." }
      ]},
    ]
  },

  help: {
    title: "Help Us",
    blocks: [
      { t: "ctarow", items: [
        { heading: "Donate", paras: [
          "Every dollar donated goes directly into innovation and research working towards beautifying our streets, improving civic infrastructure, and aiding individuals in need. Through the development of our app, Civfix, along with conducting ground-level research, we bring real data and human stories to local governments. Your contribution helps to keep our team innovating!",
          "Reach Out Los Angeles is a 501<span style='font-variant-ligatures:none;font-feature-settings:\"liga\" 0'>(c)</span>(3) nonprofit organization and your donation is 100% tax deductible. Every contribution, regardless of size, is an investment in a future where every community has the tools it needs to thrive."
        ], button: { label: "Donate", href: "https://buy.stripe.com/14A5kC47b7XLa85fvZ9Zm00" } },

        { heading: "Get in touch", paras: [
          "Have a business inquiry or proposition for us? Wanting to volunteer? Send us an email and we'll get back to you as soon as possible!"
        ], button: { label: "Contact us", href: "mailto:roman@reachoutla.org" } }

      ]}
    ]
  }
};
