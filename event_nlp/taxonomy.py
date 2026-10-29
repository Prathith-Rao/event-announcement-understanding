"""Primary-purpose taxonomy. Delivery mode is separate from purpose except explicit webinars."""
DEFINITIONS = {
    "Workshop": "A short, participatory session focused on practical exercises.",
    "Seminar": "A speaker-led lecture, research talk or discussion.",
    "Competition": "A judged contest with ranked entries or winners; excludes explicitly named hackathons and sports fixtures.",
    "Meeting": "An organizational, planning, committee or team discussion.",
    "Cultural event": "An arts performance, concert, dance, theatre or cultural festival.",
    "Conference": "A formal conference, convention, summit or multi-session research gathering.",
    "Webinar": "An explicitly described online presentation or webinar; an online practical workshop remains Workshop.",
    "Hackathon": "A time-bounded collaborative coding or prototype-building contest.",
    "Sports event": "An athletic fixture, race, tournament or organized fitness event.",
    "Exhibition": "A public display, gallery, expo or showcase of objects or work.",
    "Career event": "Recruitment, placement, career fair, networking for jobs or employer interaction.",
    "Community service": "Volunteering, charity, community outreach, donation or environmental service.",
    "Social gathering": "A party, reunion, picnic, informal celebration or social get-together.",
    "Training course": "A structured multi-session course, certification programme or sustained professional training.",
    "Product launch": "The introduction, unveiling or release event of a product or service.",
    "Academic assessment": "An examination, viva, assessment, defense or evaluation session.",
    "Ceremony": "Graduation, inauguration, felicitation, awards presentation or other formal ceremony.",
    "Tour or excursion": "An organized visit, field trip, excursion, guided walk or tour.",
    "Other event": "A specific organized happening whose purpose does not fit the categories above.",
}
NON_EVENT = "Not an event"

KEYWORDS = {
    "Workshop": ["workshop", "hands-on", "practical session", "tutorial"],
    "Seminar": ["seminar", "lecture", "research talk", "colloquium", "guest talk"],
    "Competition": ["competition", "contest", "quiz", "debate", "judges"],
    "Meeting": ["meeting", "committee", "agenda", "boardroom", "council"],
    "Cultural event": ["concert", "festival", "dance", "music", "theatre", "performance", "recital"],
    "Conference": ["conference", "convention", "summit", "symposium", "keynote"],
    "Webinar": ["webinar", "webcast", "online presentation"],
    "Hackathon": ["hackathon", "coding sprint", "prototype challenge", "codeathon"],
    "Sports event": ["football", "cricket", "basketball", "marathon", "match", "race", "badminton", "sports", "tournament"],
    "Exhibition": ["exhibition", "gallery", "expo", "art display", "showcase"],
    "Career event": ["career", "recruitment", "placement", "job fair", "hiring", "employer"],
    "Community service": ["volunteer", "charity", "blood donation", "cleanup", "clean-up", "fundraiser", "outreach"],
    "Social gathering": ["party", "reunion", "picnic", "get-together", "birthday", "social", "potluck"],
    "Training course": ["course", "certification", "bootcamp", "training programme", "training program", "curriculum"],
    "Product launch": ["launch", "unveiling", "product release", "debut"],
    "Academic assessment": ["exam", "examination", "assessment", "viva", "defense", "defence", "test"],
    "Ceremony": ["ceremony", "graduation", "inauguration", "felicitation", "convocation", "awards presentation"],
    "Tour or excursion": ["tour", "excursion", "field trip", "guided walk", "industrial visit", "heritage walk"],
    "Other event": ["event", "gathering", "open day", "session"],
}

EVENT_CUE = r"(?:workshops?|seminars?|competitions?|contests?|hackathons?|meetings?|concerts?|festivals?|lectures?|talks?|colloqui(?:um|a)|tournaments?|conferences?|summits?|symposi(?:um|a)|webinars?|matches?|races?|exhibitions?|expos?|career fairs?|job fairs?|reunions?|parties|party|picnics?|courses?|bootcamps?|launch(?:es)?|exams?|examinations?|assessments?|ceremon(?:y|ies)|graduation|tours?|excursions?|field trips?|blood donation|clean-?up|fundraisers?|events?|gatherings?|sessions?)"
