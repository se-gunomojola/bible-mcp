"""
Bible Study MCP Server
======================
Provides structured, consistent, verifiable Bible study analysis
to Claude Desktop via the Model Context Protocol.

Tools:
    bible_context        — Historical, political, cultural world of the text
    bible_lexicon        — Hebrew/Greek word analysis with semantic range
    bible_chronology     — Generational mapping, timeline computation, overlap detection
    bible_study          — Full 6-section deep analysis (orchestrates all tools)
    bible_deep_study     — BibleDeepDive 8-layer study (Segun's methodology)

Resources:
    biblical://lexicon      — Hebrew/Greek term database (35+ terms)
    biblical://chronology   — Dates, genealogies, lifespan data
    biblical://context      — Political epochs, geographic data, cultural notes
    biblical://commentary   — Attributed commentary: Spurgeon, Calvin, Henry, Wright, Barclay

Author: Segun Omojola — TB Network Bible Study Project
"""

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
import json
import re

mcp = FastMCP("bible_mcp")


# ── Embedded Data ─────────────────────────────────────────────────────────────
# These are the core datasets. In production these would be loaded from
# external files or a database. Here they are embedded for portability.

LEXICON: dict = {
    "torah": {
        "hebrew": "תּוֹרָה",
        "transliteration": "Torah",
        "root": "y-r-h (to throw, to shoot, to point the way)",
        "range": "Teaching, instruction, guidance — not primarily 'law' in the Roman legal sense. The path shown by a wise elder or parent.",
        "theological_weight": "Relational and directional. God as teacher, Israel as student/traveller.",
        "translation_distortion": "English 'law' imports Roman juridical connotations — statute, obligation, penalty. Torah is closer to 'the way things work' as revealed by God.",
        "key_passages": ["Psalm 119", "Deuteronomy 31:9-13"]
    },
    "hesed": {
        "hebrew": "חֶסֶד",
        "transliteration": "Hesed",
        "root": "h-s-d (covenant loyalty, steadfast love)",
        "range": "Covenantal faithfulness that holds even when the other party fails. Not mere sentiment — an active, committed loyalty with obligation.",
        "theological_weight": "One of the most theologically dense words in the OT. Describes God's character (Exodus 34:6), human obligation, and the basis of the covenant relationship.",
        "translation_distortion": "'Lovingkindness' or 'mercy' are too weak. 'Steadfast love' (RSV/ESV) is better. The word implies a prior relationship and obligation — you cannot show hesed to a stranger.",
        "key_passages": ["Exodus 34:6", "Ruth 1:8", "Hosea 6:6", "Micah 6:8"]
    },
    "shalom": {
        "hebrew": "שָׁלוֹם",
        "transliteration": "Shalom",
        "root": "sh-l-m (completeness, wholeness)",
        "range": "Not merely absence of conflict. Wholeness, flourishing, right relationships — between humans, between humans and God, between humans and creation.",
        "theological_weight": "The state of affairs when everything is as God intends. Peace is the by-product of shalom, not the definition.",
        "translation_distortion": "'Peace' is severely inadequate. Shalom is the goal of salvation itself — the full restoration of all broken relationships.",
        "key_passages": ["Numbers 6:24-26", "Isaiah 9:6", "Isaiah 53:5", "Jeremiah 29:7"]
    },
    "emet": {
        "hebrew": "אֱמֶת",
        "transliteration": "Emet",
        "root": "a-m-n (firmness, reliability — same root as Amen)",
        "range": "Truth as reliability, solidity, that which can be counted on. Not merely factual accuracy but ontological dependability.",
        "theological_weight": "Often paired with hesed — the two defining characteristics of God's covenant character. Truth here means God will do what God has said.",
        "translation_distortion": "'Truth' in English is primarily epistemological (correspondence to fact). Emet is primarily relational — trustworthiness.",
        "key_passages": ["Exodus 34:6", "Psalm 25:10", "Psalm 86:15", "John 1:14"]
    },
    "ruach": {
        "hebrew": "רוּחַ",
        "transliteration": "Ruach",
        "root": "r-w-ch (wind, breath, spirit)",
        "range": "Wind, breath, the animating force of life, the Spirit of God. Context determines which — but the physical and spiritual are never fully separated.",
        "theological_weight": "The same word for the wind over the waters in Genesis 1:2 and the Spirit of God in the prophets. The physicality of the word prevents purely spiritualised readings.",
        "translation_distortion": "Translating always as 'Spirit' loses the embodied, physical dimension. The ruach of God is power that moves, animates, and gives life — not a disembodied ghost.",
        "key_passages": ["Genesis 1:2", "Ezekiel 37:1-14", "Joel 2:28-29", "John 3:8"]
    },
    "kabod": {
        "hebrew": "כָּבוֹד",
        "transliteration": "Kabod",
        "root": "k-b-d (heaviness, weight)",
        "range": "Glory, honour, weightiness. The glory of God is the overwhelming, substantial presence of God — not merely brightness but reality of a different order.",
        "theological_weight": "Kabod/Glory is what Israel saw at Sinai, what filled the tabernacle and temple, what departed in Ezekiel, what returned in Christ. It is the signature of God's presence.",
        "translation_distortion": "'Glory' has become decorative in English — we speak of glorious sunsets. Kabod is something that knocks you down, that cannot be safely approached.",
        "key_passages": ["Exodus 33:18-23", "Ezekiel 1:28", "Ezekiel 10-11", "John 1:14"]
    },
    "dabar": {
        "hebrew": "דָּבָר",
        "transliteration": "Dabar",
        "root": "d-b-r (to speak, to drive forward)",
        "range": "Word, matter, thing, event. In Hebrew thought, the word of God is an event — it brings into existence what it names. God's dabar is not information; it is action.",
        "theological_weight": "The creation happened through dabar. The prophets delivered dabar. The word of God in Hebrew is never merely verbal — it is effectual.",
        "translation_distortion": "'Word' in English is primarily communicative. Dabar is causal — it produces effects. 'John 1:1 — In the beginning was the Dabar' means: in the beginning was the event-causing, reality-creating speech of God.",
        "key_passages": ["Genesis 1", "Psalm 33:6", "Isaiah 55:10-11", "John 1:1"]
    },
    "toledot": {
        "hebrew": "תּוֹלְדֹת",
        "transliteration": "Toledot",
        "root": "y-l-d (to bear, to bring forth)",
        "range": "Generations, descendants, the story of what something produces. Not merely a list — a narrative of continuation and fruitfulness.",
        "theological_weight": "Structures the book of Genesis — each toledot section is a new chapter of what God is bringing forth. Applied to the heavens and earth in Genesis 2:4 — creation itself has a toledot.",
        "translation_distortion": "'Genealogy' or 'generations' misses the productive, narrative sense. Toledot is about what is being brought into being through this line.",
        "key_passages": ["Genesis 2:4", "Genesis 5:1", "Genesis 37:2", "1 Chronicles 1-9"]
    },
    "qadosh": {
        "hebrew": "קָדוֹשׁ",
        "transliteration": "Qadosh",
        "root": "q-d-sh (to cut, to set apart)",
        "range": "Holy, set apart, other, distinct. Not primarily moral purity but ontological otherness — belonging to a different category of existence.",
        "theological_weight": "God is holy — in a category entirely apart from creation. Israel is called to be holy — to live in a way that marks them as belonging to the holy God.",
        "translation_distortion": "'Holy' has become synonymous with 'morally pure' in English. The primary meaning is 'set apart for God' — which then produces a distinctive way of life.",
        "key_passages": ["Leviticus 19:2", "Isaiah 6:3", "1 Peter 1:16"]
    },
    "emunah": {
        "hebrew": "אֱמוּנָה",
        "transliteration": "Emunah",
        "root": "a-m-n (firmness, steadiness — same as Emet)",
        "range": "Faithfulness, steadiness, reliability. Often translated 'faith' but is primarily an active, sustained commitment rather than an intellectual assent.",
        "theological_weight": "Habakkuk 2:4 — 'the righteous shall live by his emunah' — is the foundation of Paul's theology of faith in Romans and Galatians. But emunah is faithfulness, not merely belief.",
        "translation_distortion": "Translating as 'faith' imports Greek pistis connotations of intellectual belief. Emunah is closer to 'faithfulness' — steadfast covenant loyalty in action.",
        "key_passages": ["Habakkuk 2:4", "Lamentations 3:23", "Deuteronomy 32:4"]
    },
    "logos": {
        "greek": "λόγος",
        "transliteration": "Logos",
        "root": "leg-o (to speak, to gather, to reason)",
        "range": "Word, reason, account, the ordering principle of the universe. In Greek philosophy, the logos was the rational structure of reality. In John 1, it becomes personal.",
        "theological_weight": "John's genius is loading a Greek philosophical term (logos as cosmic reason) with Hebrew dabar content (word as creative event). The logos is both the rational order of creation and the speaking God of Genesis.",
        "translation_distortion": "Translating simply as 'Word' loses the Greek philosophical resonance that John's audience would have heard immediately.",
        "key_passages": ["John 1:1-18", "1 John 1:1", "Revelation 19:13"]
    },
    "charis": {
        "greek": "χάρις",
        "transliteration": "Charis",
        "root": "char- (joy, favour, gratitude)",
        "range": "Grace, favour, gift freely given. In the Greco-Roman world, charis operated within a gift-exchange economy — giving created obligation. Paul subverts this by describing grace as gift that creates no obligation.",
        "theological_weight": "Central to Paul's theology. Grace is not merely kindness — it is the gift that overturns the economy of merit. The recipient owes nothing; the giver gains nothing.",
        "translation_distortion": "'Grace' in English has become a vague spiritual term. The economic context of charis — gift, favour, gratitude — sharpens the theological claim.",
        "key_passages": ["Romans 3:24", "Ephesians 2:8", "2 Corinthians 12:9"]
    },
    "pistis": {
        "greek": "πίστις",
        "transliteration": "Pistis",
        "root": "peitho (to persuade, to trust)",
        "range": "Faith, trust, faithfulness, belief, loyalty. Greek pistis covered intellectual assent, relational trust, and active faithfulness — a spectrum that English splits into separate words.",
        "theological_weight": "When Paul says 'faith of Christ' (pistis Christou) it may mean 'Christ's own faithfulness' not 'faith in Christ' — a reading that changes the entire structure of Pauline soteriology.",
        "translation_distortion": "English forces a choice: 'faith' (intellectual/relational) or 'faithfulness' (active). Greek pistis holds both simultaneously.",
        "key_passages": ["Romans 1:17", "Galatians 2:16", "Hebrews 11:1"]
    },
    "kairos": {
        "greek": "καιρός",
        "transliteration": "Kairos",
        "root": "uncertain — possibly 'the right moment'",
        "range": "Appointed time, the right moment, a decisive turning point. Distinct from chronos (clock time) — kairos is qualitative, not quantitative.",
        "theological_weight": "The kingdom of God arrives in kairos — 'the time is fulfilled' (Mark 1:15). This is not a scheduled appointment but the decisive moment when God acts.",
        "translation_distortion": "Both kairos and chronos are translated 'time' in English, erasing a crucial distinction. Kairos is opportunity, appointed moment, the now that demands response.",
        "key_passages": ["Mark 1:15", "Galatians 4:4", "Ephesians 5:16"]
    },
    "agape": {
        "greek": "ἀγάπη",
        "transliteration": "Agape",
        "root": "agapao (to love — the precise origin is debated)",
        "range": "Love — specifically the love that chooses the other's good regardless of reciprocity or worthiness. Distinct from eros (desire) and philia (friendship/affection).",
        "theological_weight": "1 Corinthians 13 and 1 John 4 make agape the defining characteristic of both God and the community that belongs to God. It is volitional, not emotional — a decision, not a feeling.",
        "translation_distortion": "English 'love' conflates what Greek separates. Agape is the love that holds when eros and philia have nothing left to give.",
        "key_passages": ["John 3:16", "Romans 5:8", "1 Corinthians 13", "1 John 4:8"]
    },
    "ashrei": {
        "hebrew": "אַשְׁרֵי",
        "transliteration": "Ashrei",
        "root": "ashar (to walk straight, to go forward on the right path)",
        "range": "Blessed, happy, content — but rooted in the image of someone walking the right path. The deep satisfaction of being aligned with reality as God intends it.",
        "theological_weight": "Opens Psalm 1 and Psalm 119. Sets the frame for the entire Psalter — the question of what a fully human life looks like.",
        "translation_distortion": "'Blessed' has religious overtones that miss the concrete, directional image. 'Happy' is too light. Better: 'On the right path is the one who...'",
        "key_passages": ["Psalm 1:1", "Psalm 119:1-2", "Matthew 5:3-12 (Makarios)"]
    },
    "bekhor": {
        "hebrew": "בְּכוֹר",
        "transliteration": "Bekhor",
        "root": "b-k-r (firstborn, firstfruits)",
        "range": "Firstborn — carrying rights of double inheritance, family leadership, priestly role. A covenantal status, not merely a birth order.",
        "theological_weight": "Scripture consistently subverts the bekhor — Ishmael/Isaac, Esau/Jacob, Reuben/Judah, Manasseh/Ephraim. God's choice overrides birth order. This is a structural claim about election.",
        "translation_distortion": "'Firstborn' is accurate but modern readers miss the enormous covenantal weight — the firstborn was the heir of everything.",
        "key_passages": ["Genesis 25:29-34", "1 Chronicles 5:1-2", "Exodus 4:22", "Romans 8:29"]
    },
    # ── Additional OT terms ───────────────────────────────────────────────────
    "nephesh": {
        "hebrew": "נֶפֶשׁ",
        "transliteration": "Nephesh",
        "root": "n-p-sh (throat, neck, breath, desire)",
        "range": "Living being, life, self, desire, appetite. NOT an immortal soul separate from the body. A nephesh is what a creature IS, not what it HAS.",
        "theological_weight": "Genesis 2:7 — God breathed into Adam and he BECAME a living nephesh. Not: he received a soul. The body + breath = the whole living being. Death is the cessation of nephesh, not its departure.",
        "translation_distortion": "Translating as 'soul' imports Greek Platonic dualism — an immortal soul trapped in a mortal body. Hebrew anthropology is holistic. The nephesh is the whole animated person.",
        "key_passages": ["Genesis 2:7", "Psalm 42:1-2", "Isaiah 53:12", "Matthew 10:28 (psyche)"]
    },
    "bara": {
        "hebrew": "בָּרָא",
        "transliteration": "Bara",
        "root": "b-r-a (to create — used exclusively of divine creation)",
        "range": "To create out of nothing or to create something radically new. This verb is used ONLY with God as subject in the entire Hebrew Bible — never humans.",
        "theological_weight": "Genesis 1:1 uses bara to establish that what follows is categorically different from human making. God's creation is an act in a class of its own. The word marks divine sovereign agency.",
        "translation_distortion": "'Create' in English is used of human creativity too. Bara marks an absolute distinction — only God does this.",
        "key_passages": ["Genesis 1:1", "Isaiah 40:26", "Isaiah 43:1", "Psalm 51:10"]
    },
    "shema": {
        "hebrew": "שָׁמַע",
        "transliteration": "Shema",
        "root": "sh-m-a (to hear, to listen, to obey)",
        "range": "Hear, listen, obey — in Hebrew these are not separate. To truly hear is to respond with action. Disobedience is therefore not merely moral failure but a failure of hearing.",
        "theological_weight": "Deuteronomy 6:4 — 'Shema, Yisrael' — is the foundational confession of Judaism. It is not just 'Listen up!' It is a call to the kind of hearing that reshapes life.",
        "translation_distortion": "English separates 'hear' and 'obey'. Hebrew holds them together. When Israel 'did not hear' the prophets it means they did not obey — the translation hides the connection.",
        "key_passages": ["Deuteronomy 6:4", "Isaiah 1:2-3", "Jeremiah 7:13", "Romans 10:17"]
    },
    "anawim": {
        "hebrew": "עֲנָוִים",
        "transliteration": "Anawim",
        "root": "a-n-w (bowed down, afflicted, humble)",
        "range": "The poor, the humble, the afflicted — specifically those whose poverty has driven them to total dependence on God. Not just economically poor but the spiritually dependent poor.",
        "theological_weight": "The Psalms are largely the prayer book of the anawim. The Beatitudes ('Blessed are the poor in spirit') are a direct echo. Jesus identifies his mission with the anawim (Luke 4:18).",
        "translation_distortion": "Translating as simply 'the poor' misses the theological dimension — these are the ones who have no resource but God, and who have come to know that as blessing not curse.",
        "key_passages": ["Psalm 22:26", "Psalm 149:4", "Isaiah 61:1", "Matthew 5:3"]
    },
    "berith": {
        "hebrew": "בְּרִית",
        "transliteration": "Berith / Brit",
        "root": "b-r-t (possibly 'to cut' — covenants were ratified by cutting animals)",
        "range": "Covenant — a binding, formal commitment between two parties, ratified by oath and often sacrifice. Not a contract (equal parties exchanging goods) but a covenant (a relationship with defined obligations).",
        "theological_weight": "The entire Hebrew Bible is structured by successive covenants: Noahic, Abrahamic, Mosaic, Davidic, New Covenant. Each one narrows and deepens the redemptive purpose of God.",
        "translation_distortion": "English 'covenant' is archaic and underused. Modern readers miss that every time berith appears, the full weight of the covenant relationship is invoked — promises, obligations, consequences.",
        "key_passages": ["Genesis 15", "Exodus 24", "2 Samuel 7", "Jeremiah 31:31-34", "Hebrews 8"]
    },
    "mishkan": {
        "hebrew": "מִשְׁכָּן",
        "transliteration": "Mishkan",
        "root": "sh-k-n (to dwell, to settle, to tabernacle — same root as Shekinah)",
        "range": "The tabernacle — but more precisely, 'the dwelling place.' The same root gives us Shekinah (God's manifest dwelling presence) and later the concept of incarnation.",
        "theological_weight": "John 1:14 — 'the Word tabernacled (eskēnōsen) among us' — is a direct echo of mishkan. The incarnation is described as God pitching his tent among his people, as he did in the wilderness.",
        "translation_distortion": "'Tabernacle' is accurate but loses the dynamic sense of God choosing to dwell in the midst of his people — not in a distant heaven but in the camp.",
        "key_passages": ["Exodus 25:8-9", "Exodus 40:34-38", "John 1:14", "Revelation 21:3"]
    },
    "tsaddiq": {
        "hebrew": "צַדִּיק",
        "transliteration": "Tsaddiq",
        "root": "ts-d-q (righteousness — conformity to a standard, right relationship)",
        "range": "Righteous, just — but in Hebrew the standard is not an abstract moral law but a relationship. To be tsaddiq is to be in right relationship and to act consistently with that relationship.",
        "theological_weight": "God's righteousness (tsedaqah) is his covenant faithfulness — his acting in accordance with his promises. Human righteousness is living in accordance with the covenant relationship.",
        "translation_distortion": "'Righteousness' in English has become individualistic and moralistic. Hebrew tsaddiq is relational and communal — you are righteous when you treat others as the covenant requires.",
        "key_passages": ["Genesis 15:6", "Amos 5:24", "Micah 6:8", "Romans 1:17", "Romans 3:21-26"]
    },
    "malak": {
        "hebrew": "מַלְאָךְ",
        "transliteration": "Malak",
        "root": "m-l-k (messenger, one sent)",
        "range": "Messenger, angel. The same word is used for human messengers, prophets, and divine beings. Context determines which. 'Angel' has become exclusively supernatural in English.",
        "theological_weight": "The Malak YHWH (Angel of the LORD) in the OT often speaks as God in first person — leading many interpreters to see a pre-incarnate appearance of the Son. The word itself keeps the categories fluid.",
        "translation_distortion": "Translating always as 'angel' loses the 'sent one' dynamic — these are messengers executing a commission, not a separate class of celestial beings with independent status.",
        "key_passages": ["Genesis 16:7-13", "Exodus 3:2", "Judges 6:11-24", "Malachi 3:1", "Hebrews 1:14"]
    },
    # ── Additional NT terms ───────────────────────────────────────────────────
    "parousia": {
        "greek": "παρουσία",
        "transliteration": "Parousia",
        "root": "para + ousia (presence, arrival — from 'to be present')",
        "range": "Arrival, presence, coming. In the Greco-Roman world, parousia was the official visit of a king or emperor to a city — with all the ceremony and civic transformation that entailed.",
        "theological_weight": "The 'second coming' is actually the parousia — the royal arrival of the king. It was not conceived as escape to heaven but as the king coming to his territory to set things right. The city would go out to meet him and accompany him back.",
        "translation_distortion": "'Second coming' is an adequate summary but loses the royal arrival imagery. The NT church expected the parousia like a city expects its king — with transformation of civic life, not evacuation.",
        "key_passages": ["1 Thessalonians 4:15-17", "Matthew 24:27", "1 Corinthians 15:23", "James 5:7-8"]
    },
    "ekklesia": {
        "greek": "ἐκκλησία",
        "transliteration": "Ekklesia",
        "root": "ek + kaleo (called out — the assembly of those summoned)",
        "range": "Assembly, congregation — specifically a gathered community of citizens called out for civic purposes. In the Greek city-state, the ekklesia was the governing assembly of full citizens.",
        "theological_weight": "The church is not a building, not a religious club, not a private gathering. It is a public assembly of citizens of a different kingdom, gathered to conduct the business of that kingdom in the world.",
        "translation_distortion": "'Church' in English has become primarily institutional and architectural. Ekklesia is political — a gathered people with civic identity and responsibility.",
        "key_passages": ["Matthew 16:18", "Acts 2:47", "1 Corinthians 1:2", "Ephesians 1:22-23"]
    },
    "soteria": {
        "greek": "σωτηρία",
        "transliteration": "Soteria",
        "root": "soter (saviour, deliverer, rescuer)",
        "range": "Salvation, rescue, deliverance, healing, wholeness. Used in the Greek world for physical rescue (from shipwreck, battle, disease) as well as political deliverance.",
        "theological_weight": "Salvation in the NT is not primarily about going to heaven when you die. It is rescue from all that destroys human flourishing — sin, death, injustice, broken relationship with God — and restoration to wholeness.",
        "translation_distortion": "'Salvation' has become narrowly spiritual and future-oriented in popular Christianity. Soteria is immediate, physical, communal, and cosmic — it addresses every dimension of lostness.",
        "key_passages": ["Luke 19:9-10", "Acts 4:12", "Romans 1:16", "Ephesians 2:8", "Revelation 7:10"]
    },
    "sarx": {
        "greek": "σάρξ",
        "transliteration": "Sarx",
        "root": "sarx (flesh, meat, physical body)",
        "range": "Flesh — but in Paul's usage it spans: (1) the physical body, (2) human mortality and weakness, (3) the entire human system of values and living that operates apart from God. Context is critical.",
        "theological_weight": "When Paul contrasts 'flesh' and 'spirit' he is not contrasting body vs soul (Greek dualism). He is contrasting two ways of being human — one oriented around self and the age that is passing, one oriented around God and the age to come.",
        "translation_distortion": "Translating as 'sinful nature' (NIV) turns sarx into an internal spiritual category. Paul means something more systemic — the entire human way of life organised apart from God.",
        "key_passages": ["Romans 7:5", "Romans 8:3-9", "Galatians 5:16-24", "John 1:14"]
    },
    "dikaiosyne": {
        "greek": "δικαιοσύνη",
        "transliteration": "Dikaiosyne",
        "root": "dikaios (right, just — conforming to a standard)",
        "range": "Righteousness, justice — the same Greek word covers both. In English we separate 'righteousness' (personal moral virtue) from 'justice' (social/legal category). Greek and Hebrew hold them as one.",
        "theological_weight": "Paul's 'righteousness of God' (Romans 1:17) is God's own covenant faithfulness breaking into the world — not merely a status imputed to believers but a power that sets the world right.",
        "translation_distortion": "Translating sometimes as 'righteousness' and sometimes as 'justice' obscures that Paul is talking about one thing. When God acts righteously it is always also just — and vice versa.",
        "key_passages": ["Romans 1:17", "Romans 3:21-26", "Matthew 5:6", "Matthew 6:33"]
    },
    "pneuma": {
        "greek": "πνεῦμα",
        "transliteration": "Pneuma",
        "root": "pneo (to blow, to breathe)",
        "range": "Spirit, wind, breath. Parallel to Hebrew ruach — the same ambiguity of physical and spiritual is present. The Holy Spirit is the breath/wind of God animating the new creation.",
        "theological_weight": "John 3:8 plays on the double meaning deliberately — the pneuma blows where it will, like wind. The Spirit is as uncontrollable and life-giving as breath.",
        "translation_distortion": "Always rendering as 'Spirit' loses the physicality. The pneuma is not merely an invisible force — it is the animating breath of God, the very life of the new age entering the present.",
        "key_passages": ["John 3:5-8", "Romans 8:9-17", "1 Corinthians 12:13", "Galatians 5:25"]
    },
    "huios": {
        "greek": "υἱός",
        "transliteration": "Huios",
        "root": "huios (son — with full covenantal and inheritance implications)",
        "range": "Son — but in ancient world 'son of X' means one who bears the character and carries the authority of X. 'Son of God' is a royal/covenantal title before it is an ontological one.",
        "theological_weight": "In the OT, Israel is God's son (Exodus 4:22), the king is God's son (Psalm 2:7). 'Son of God' in the NT carries this covenantal freight — Jesus is the true Israel, the true king, who perfectly embodies what sonship means.",
        "translation_distortion": "Modern readers hear 'Son of God' as primarily a statement about the Trinity. The first hearers heard it as a royal-covenantal claim — this man represents God and rules in God's name.",
        "key_passages": ["Exodus 4:22", "Psalm 2:7", "Mark 1:1", "Romans 1:3-4", "Hebrews 1:1-4"]
    },
    "apolutrosis": {
        "greek": "ἀπολύτρωσις",
        "transliteration": "Apolutrosis",
        "root": "apo + lytron (ransom, redemption price — buying freedom)",
        "range": "Redemption, release, liberation — specifically the payment that secures freedom for a slave or prisoner. An economic-legal term before it is a spiritual one.",
        "theological_weight": "When Paul says Christ is our apolutrosis he is invoking the imagery of the slave market and the prison — we were in bondage, a price was paid, we are free. The freedom is concrete, not merely forensic.",
        "translation_distortion": "'Redemption' has become so spiritualised in church use that the commercial/legal imagery is invisible. Paul's original readers would have thought of actual ransomed prisoners and freed slaves.",
        "key_passages": ["Romans 3:24", "Ephesians 1:7", "Colossians 1:14", "Hebrews 9:15"]
    },
    "mysterion": {
        "greek": "μυστήριον",
        "transliteration": "Mysterion",
        "root": "myeo (to initiate, to close lips — as in the mysteries)",
        "range": "Mystery — but in NT usage it is not something permanently hidden but something previously hidden that is NOW being revealed. The mystery is disclosed, not maintained.",
        "theological_weight": "Paul's use of mysterion describes the previously hidden plan of God — Gentiles included in the covenant — now made known through Christ. The mystery is the gospel itself.",
        "translation_distortion": "'Mystery' in English implies ongoing incomprehensibility. NT mysterion is the opposite — the secret is out. God's plan has been revealed.",
        "key_passages": ["Romans 16:25-26", "Ephesians 3:3-6", "Colossians 1:26-27", "Revelation 10:7"]
    },
    "mishpat": {
        "hebrew": "מִשְׁפָּט",
        "transliteration": "Mishpat",
        "root": "sh-p-t (to judge, to govern, to set right)",
        "range": "Justice, judgment, legal right, customary law, the right ordering of community life. Not merely punishment — the full restoration of right relationships when they have been broken.",
        "theological_weight": "Micah 6:8 — 'do mishpat, love hesed, walk humbly' — is the prophetic summary of the entire covenant obligation. Mishpat is the social and structural dimension; hesed is the relational. Together they describe a community that reflects God's character.",
        "translation_distortion": "English 'justice' is often narrowly legal — courts, punishment, verdicts. Mishpat is broader: the right ordering of every relationship in society, especially care for those without power to defend themselves.",
        "key_passages": ["Micah 6:8", "Amos 5:24", "Isaiah 1:17", "Psalm 82:3", "Matthew 23:23"]
    }
}

CHRONOLOGY: dict = {
    "adam_to_noah": {
        "period": "Creation to Flood",
        "figures": [
            {"name": "Adam", "born": 0, "died": 930, "note": "AM (Anno Mundi — year of the world)"},
            {"name": "Seth", "born": 130, "died": 1042},
            {"name": "Enosh", "born": 235, "died": 1140},
            {"name": "Kenan", "born": 325, "died": 1235},
            {"name": "Mahalalel", "born": 395, "died": 1290},
            {"name": "Jared", "born": 460, "died": 1422},
            {"name": "Enoch", "born": 622, "died": 987, "note": "Taken — did not die"},
            {"name": "Methuselah", "born": 687, "died": 1656, "note": "Died year of the Flood"},
            {"name": "Lamech", "born": 874, "died": 1651},
            {"name": "Noah", "born": 1056, "died": 2006},
        ],
        "flood_year": 1656,
        "transmission_type": "Living memory — Adam and Methuselah overlapped by 243 years. Methuselah could have transmitted first-hand Adam's account to Shem. Noah lived 350 years after the flood.",
    },
    "noah_to_abraham": {
        "period": "Post-Flood to Patriarchs",
        "figures": [
            {"name": "Shem", "born": 1558, "died": 2158},
            {"name": "Arpachshad", "born": 1658, "died": 2096},
            {"name": "Shelah", "born": 1693, "died": 2126},
            {"name": "Eber", "born": 1723, "died": 2187},
            {"name": "Peleg", "born": 1757, "died": 1996, "note": "In his days the earth was divided"},
            {"name": "Reu", "born": 1787, "died": 2026},
            {"name": "Serug", "born": 1819, "died": 2049},
            {"name": "Nahor", "born": 1849, "died": 1997},
            {"name": "Terah", "born": 1878, "died": 2083},
            {"name": "Abraham", "born": 2008, "died": 2183},
        ],
        "transmission_type": "Shem outlived Abraham by 35 years. The flood account was living memory through Shem into the patriarchal period.",
    },
    "patriarchs": {
        "period": "Abraham to Egypt",
        "figures": [
            {"name": "Abraham", "born": 2008, "died": 2183, "born_bc": "c.2166 BC"},
            {"name": "Isaac", "born": 2108, "died": 2288, "born_bc": "c.2066 BC"},
            {"name": "Jacob/Israel", "born": 2168, "died": 2315, "born_bc": "c.2006 BC"},
            {"name": "Joseph", "born": 2257, "died": 2347, "born_bc": "c.1915 BC"},
            {"name": "Judah", "born": "c.2252", "died": "c.2352", "born_bc": "c.1920 BC"},
            {"name": "Perez (son of Judah)", "born": "c.2290", "born_bc": "c.1882 BC"},
        ],
        "key_overlaps": [
            "Jacob and Shem: overlapped by 50 years — Shem was alive when Jacob was born",
            "Joseph died before Israel entered Egypt as slaves",
            "Abraham, Isaac, and Jacob: all overlapped significantly",
        ],
        "transmission_type": "Living memory through patriarchal lifespans. Jacob could have heard from Shem, who knew Noah, who knew Methuselah, who knew Adam.",
    },
    "exodus_to_david": {
        "period": "Exodus to Monarchy",
        "key_dates_bc": {
            "Exodus": "c.1446 BC (1 Kings 6:1 reckoning) or c.1270 BC (archaeological reckoning)",
            "Conquest begins": "c.1406 BC",
            "Period of Judges": "c.1380-1050 BC",
            "Saul anointed": "c.1050 BC",
            "David anointed": "c.1010 BC",
            "Solomon's temple begun": "966 BC",
        },
        "judah_to_david_line": [
            {"name": "Judah", "generation": 1},
            {"name": "Perez", "generation": 2},
            {"name": "Hezron", "generation": 3},
            {"name": "Ram", "generation": 4},
            {"name": "Amminadab", "generation": 5},
            {"name": "Nahshon", "generation": 6, "note": "Leader of Judah in the Exodus (Numbers 1:7)"},
            {"name": "Salmon", "generation": 7, "note": "Married Rahab of Jericho"},
            {"name": "Boaz", "generation": 8, "note": "Ruth 4 — kinsman redeemer"},
            {"name": "Obed", "generation": 9},
            {"name": "Jesse", "generation": 10},
            {"name": "David", "generation": 11, "note": "7th or 8th son of Jesse — anointed c.1010 BC"},
        ],
        "chronological_note": "10 generations across ~430 years (Exodus to David) requires ~43 years per generation average. Likely telescoped — selective rather than complete.",
        "transmission_type": "Gap between Sinai covenant and David: ~430 years. Textual/institutional transmission. Torah preserved in the ark and taught by priests and Levites.",
    },
    "monarchy_to_exile": {
        "period": "United and Divided Monarchy",
        "key_dates_bc": {
            "David reigns": "1010-970 BC",
            "Solomon reigns": "970-930 BC",
            "Kingdom divides": "930 BC",
            "Northern Kingdom falls (Assyria)": "722 BC",
            "Josiah's reform": "621 BC",
            "First deportation to Babylon": "605 BC",
            "Jerusalem falls, temple destroyed": "586 BC",
            "Cyrus decree, return begins": "538 BC",
            "Temple rebuilt": "516 BC",
            "Ezra returns": "458 BC",
            "Nehemiah returns": "445 BC",
        },
        "transmission_type": "Institutional — priests, scribes, prophets. Deuteronomy found in the temple under Josiah (2 Kings 22) suggests periods of institutional neglect.",
    },
    "new_testament": {
        "period": "Second Temple to Early Church",
        "key_dates": {
            "Birth of Jesus": "c.6-4 BC (before Herod's death in 4 BC)",
            "Ministry of Jesus": "c.AD 27-30",
            "Crucifixion": "c.AD 30 or 33",
            "Paul's conversion": "c.AD 33-35",
            "Paul's letters": "c.AD 48-65",
            "Jerusalem falls": "AD 70",
            "John's Gospel/Revelation": "c.AD 90-95",
        },
        "transmission_type": "Living memory into first generation. Paul's letters predate the Gospels. Oral tradition ran parallel to written texts for decades.",
    }
}

POLITICAL_EPOCHS: dict = {
    "primordial": {
        "approximate_dates": "Before recorded history — Genesis 1–11",
        "political_structure": "None — pre-political. God as sole sovereign over creation. Human governance not yet established. The garden is a sacred space, not a political unit.",
        "key_empires": "None — pre-empire. The first city is built by Cain (Genesis 4:17) — a significant theological detail.",
        "economic_system": "Garden abundance (Eden), then subsistence agriculture after the fall. Cain is a farmer, Abel a herder — the two economies of the ancient world in tension from the start.",
        "power_dynamics": "Creator/creature. The fundamental power dynamic is God speaking and reality obeying. Human power enters as stewardship (tselem) then distorts immediately into domination and violence (Cain, Lamech, Babel).",
        "cultural_notes": "Genesis 1–11 is theological prehistory — the account of how things came to be as they are. Ancient Near Eastern parallels (Enuma Elish, Atrahasis, Epic of Gilgamesh) provide essential contrast. Israel's account is unique in depicting: creation by speech alone, creation as entirely good, humanity as image-bearers with dignity rather than slaves of the gods, and a flood sent for moral rather than political reasons.",
        "ancient_near_east_context": "Genesis 1 is written in deliberate dialogue with surrounding cosmologies. Enuma Elish (Babylonian) depicts creation through divine conflict — Marduk slaying Tiamat and making the world from her corpse. Genesis counters: no conflict, no chaos-monster to defeat, no divine politics. God speaks and it is. The sun and moon are called 'great lights' and not named — because their names (Shamash and Sin) were the names of Babylonian deities. Genesis quietly demotes them from gods to lamps.",
    },
    "patriarchal": {
        "approximate_dates": "2200-1800 BC",
        "political_structure": "Semi-nomadic clan system. No centralised state. Governed by patriarchal authority — the eldest male as clan head, judge, priest.",
        "key_empires": "Egyptian Middle Kingdom, Mesopotamian city-states",
        "economic_system": "Pastoral herding, seasonal migration, treaty-based land use",
        "power_dynamics": "Clan honour system. Hospitality as covenant. Might and numbers = security.",
    },
    "egyptian_slavery": {
        "approximate_dates": "1800-1446 BC",
        "political_structure": "Imperial Egyptian administration. Pharaoh as divine king. Israelites as state slaves — a workforce, not citizens.",
        "key_empires": "New Kingdom Egypt",
        "economic_system": "Forced labour in state building projects. No property rights for slaves.",
        "power_dynamics": "Total imperial control. Ethnic and class hierarchy. Hebrew midwives as minor agents of resistance.",
    },
    "wilderness": {
        "approximate_dates": "1446-1406 BC",
        "political_structure": "Theocratic — God as king, Moses as mediator-prophet, Aaron as high priest. Elder council. No territory.",
        "key_empires": "Egyptian decline, Canaanite city-states, Transjordanian kingdoms (Edom, Moab, Ammon)",
        "economic_system": "Wilderness provision — manna, quail. No agricultural base.",
        "power_dynamics": "Divine provision vs. human complaint. Constant negotiation of authority between Moses, priests, and the people.",
    },
    "judges": {
        "approximate_dates": "1380-1050 BC",
        "political_structure": "Tribal confederacy. No permanent central authority. Judges raised in crisis situations — charismatic military leaders.",
        "key_empires": "Philistine city-states, Canaanite remnants, surrounding tribal kingdoms",
        "economic_system": "Agricultural settlement. Land allocation by tribe.",
        "power_dynamics": "Cyclical: sin → oppression → cry → judge → deliverance → rest → sin. Decentralised, local authority.",
    },
    "united_monarchy": {
        "approximate_dates": "1050-930 BC",
        "political_structure": "Monarchy — Saul, David, Solomon. Centralised government, standing army, temple cult, tax system.",
        "key_empires": "Israel as regional power. Egypt weakened. Assyria not yet dominant.",
        "economic_system": "Agricultural base plus trade networks under Solomon. Temple economy. Forced labour (corvee).",
        "power_dynamics": "King vs. priests vs. prophets — a three-way tension that runs through the entire monarchic period.",
    },
    "divided_monarchy": {
        "approximate_dates": "930-722 BC (North) / 930-586 BC (South)",
        "political_structure": "Two kingdoms — Israel (North, 10 tribes) and Judah (South, 2 tribes). Rival dynasties. Shifting alliances.",
        "key_empires": "Assyria rising. Egypt declining. Aram/Syria as regional player.",
        "economic_system": "Agricultural and trade economies. Temple tax in the south. Competing cult sites in the north.",
        "power_dynamics": "Prophets as the conscience of the court. Kings under pressure from Assyrian tribute demands.",
    },
    "babylonian_exile": {
        "approximate_dates": "605-538 BC",
        "political_structure": "Diaspora — no king, no temple, no land. Jewish community governed by Babylonian imperial administration.",
        "key_empires": "Neo-Babylonian Empire (Nebuchadnezzar). Persian Empire rising.",
        "economic_system": "Jewish exiles integrated into Babylonian economy. Evidence of property ownership and business activity.",
        "power_dynamics": "Identity maintenance under assimilation pressure. Synagogue as institution born in exile — Torah study replacing temple worship.",
    },
    "persian_period": {
        "approximate_dates": "538-332 BC",
        "political_structure": "Persian province of Yehud. Governed by a Persian-appointed governor. Jewish community permitted self-governance in religious matters.",
        "key_empires": "Achaemenid Persian Empire",
        "economic_system": "Persian taxation system. Returned exiles competing with those who remained for land rights.",
        "power_dynamics": "Torah as constitutional identity. Tension between returned exiles and the people of the land. Ezra/Nehemiah reforms.",
        "theological_significance": "Context for Chronicles, Ezra, Nehemiah, Haggai, Zechariah, Malachi, and likely Psalm 119 and the final Psalter compilation.",
    },
    "second_temple_early": {
        "approximate_dates": "516-167 BC",
        "political_structure": "Persian then Ptolemaic (Egyptian) then Seleucid (Syrian) control. High priest as key political figure.",
        "key_empires": "Persian, then Alexander the Great (332 BC), then Ptolemaic Egypt, then Seleucid Syria",
        "economic_system": "Temple economy. Hellenistic trade networks.",
        "power_dynamics": "Hellenisation pressure on Jewish identity. Torah observance as resistance.",
    },
    "roman_period": {
        "approximate_dates": "63 BC — AD 135",
        "political_structure": "Roman occupation. Herodian client kings. Jewish council (Sanhedrin) permitted limited self-governance.",
        "key_empires": "Roman Empire",
        "economic_system": "Roman taxation. Temple economy. Peasant agricultural base under debt pressure.",
        "power_dynamics": "Roman military power. Jewish priestly aristocracy collaborating with Rome. Pharisees, Zealots, Essenes — competing visions of faithful response to occupation.",
        "theological_significance": "Context for all New Testament writings. Jesus's ministry operated within peasant Galilee under Roman occupation with Jewish religious authorities as local power.",
    }
}


# ── Commentary Database ───────────────────────────────────────────────────────
# Attributed insights from public domain commentators.
# These are the voices of the tradition — not quotations but scholarly summaries
# of their key interpretive moves, for use in Layer 3 of the deep study tool.

COMMENTARY: dict = {
    "genesis_1": {
        "passage": "Genesis 1",
        "commentaries": [
            {
                "commentator": "John Calvin",
                "work": "Commentary on Genesis (1554)",
                "insight": "Calvin argued that Moses wrote Genesis 1 as accommodation — adjusting his account to the capacity of ordinary people, not writing cosmological science. The six days are a theological framework, not a chronological report. The sun and moon are called 'great lights' and not by their divine names (Shamash and Sin) because Moses refused to grant divine honour to what God made as servants."
            },
            {
                "commentator": "Matthew Henry",
                "work": "Commentary on the Whole Bible (1708-1714)",
                "insight": "Henry noted that 'and God saw that it was good' — repeated across the six days — is a theological declaration about the nature of the material world. Matter is not evil, not fallen in itself. The physical world is declared good by its Maker. This is the foundational claim against every form of Gnosticism and world-denial that would plague the church."
            },
            {
                "commentator": "Charles Spurgeon",
                "work": "Metropolitan Tabernacle sermons",
                "insight": "Spurgeon preached on the light of the first day — created before the sun. He saw in this the pattern of all God's works: light before the lamp, grace before the instrument. God is not dependent on the means he has made. He can light a world before he hangs a sun in it. 'Let there be light' — the command that began creation is also the command that begins regeneration."
            },
            {
                "commentator": "N.T. Wright",
                "work": "The Day the Revolution Began (2016)",
                "insight": "Wright argues that the description of humanity as image-bearers (tselem) is a deliberately royal and priestly concept borrowed from ancient Near Eastern usage and radically democratised. In Egypt only Pharaoh was the image of God on earth. Genesis insists that every human being — male and female together — holds this royal-priestly status. The human vocation is not religious activity but cosmic stewardship: to be God's representative presence throughout creation."
            },
            {
                "commentator": "William Barclay",
                "work": "Daily Study Bible Commentary",
                "insight": "Barclay emphasised the Sabbath as the crown of creation, not an appendix to it. The seventh day receives the only blessing in the creation account. The week builds not toward work but toward rest — toward the cessation of striving and the enjoyment of what God has made. The Sabbath is built into the structure of time itself as a perpetual theological statement: the world belongs to God, not to human productivity."
            }
        ]
    },
    "genesis_22": {
        "passage": "Genesis 22",
        "commentaries": [
            {
                "commentator": "Matthew Henry",
                "work": "Commentary on the Whole Bible (1708-1714)",
                "insight": "Henry read Genesis 22 typologically — Isaac carrying the wood for his own sacrifice is Abraham's son bearing the instrument of death up the mountain. The ram caught in the thicket is provision at the last moment. The name Abraham gives the place — YHWH Yireh, 'the Lord will provide' — becomes a theological landmark. In the narrative logic of Scripture, this mountain is identified with Moriah, the site of Solomon's temple, the place where sacrifice would be offered for generations — until the final provision."
            },
            {
                "commentator": "Charles Spurgeon",
                "work": "Metropolitan Tabernacle sermons",
                "insight": "Spurgeon observed that Abraham told his servants 'we will come back to you' — plural. He fully intended to return with Isaac. Hebrews 11:19 explains why: Abraham reasoned that God could raise the dead. His obedience was not resignation but expectation. He went up the mountain believing something unprecedented was about to happen. This is the shape of all mature faith — obedience grounded in resurrection confidence."
            }
        ]
    },
    "psalm_23": {
        "passage": "Psalm 23",
        "commentaries": [
            {
                "commentator": "Charles Spurgeon",
                "work": "The Treasury of David (1869-1885)",
                "insight": "Spurgeon called Psalm 23 the nightingale of the Psalms — small but of surpassing sweetness. He noted that David does not say the Lord is a shepherd to Israel generally, but 'my shepherd.' The personalisation is the entire theological point. The infinite God is not merely a general providence but a specific, attending care for this one person. David wrote from his own experience of shepherding — he knew exactly what a good shepherd does, and he marvelled that he himself had such a one."
            },
            {
                "commentator": "Matthew Henry",
                "work": "Commentary on the Whole Bible (1708-1714)",
                "insight": "Henry observed that 'I shall not want' is not a prediction that hardship will not come but that in the midst of hardship nothing essential will be lacking. The valley of the shadow of death confirms that the psalm acknowledges darkness — but the shepherd's presence transforms what the darkness means. The table prepared in the presence of enemies is not in spite of the enemies but in full view of them — a statement of God's sovereignty over the hostile situation."
            }
        ]
    },
    "romans_8": {
        "passage": "Romans 8",
        "commentaries": [
            {
                "commentator": "John Calvin",
                "work": "Commentary on Romans (1540)",
                "insight": "Calvin on Romans 8:1 — 'there is therefore now no condemnation' — argued that the 'therefore' carries the full weight of chapters 1–7. It is the conclusion of a complete argument about sin, law, and grace. The no-condemnation is not a feeling to be attained but a status declared. It is forensic before it is experiential — the court has ruled, and no subsequent accusation can overturn the verdict."
            },
            {
                "commentator": "N.T. Wright",
                "work": "Paul and the Faithfulness of God (2013)",
                "insight": "Wright reads Romans 8 as the climax of Paul's retelling of the Exodus story. The Spirit leading the sons of God (v.14) echoes the pillar of cloud leading Israel through the wilderness. The groaning creation (vv.19-22) is creation in exile, awaiting its own liberation. The hope of glory is not escape from the material world but the renewal of it — new creation, not no-creation. Romans 8 is not about going to heaven; it is about heaven coming to earth."
            },
            {
                "commentator": "Charles Spurgeon",
                "work": "Metropolitan Tabernacle sermons",
                "insight": "Spurgeon on Romans 8:28 insisted that 'all things' must mean what it says. Not some things, not the pleasant things. All things. The bitter medicine, the closed door, the loss. The verse does not say all things are good but that all things work toward good — a different and more costly claim. The sovereignty of God over evil is not that he authors it but that he refuses to be defeated by it."
            }
        ]
    },
    "john_1": {
        "passage": "John 1:1-18",
        "commentaries": [
            {
                "commentator": "William Barclay",
                "work": "Daily Study Bible — Gospel of John (1955)",
                "insight": "Barclay wrote extensively on why John chose logos as his opening word. A Greek reader would recognise it immediately as the rational principle underlying the cosmos — the Stoic logos that held all things together. A Jewish reader would hear dabar — the creative, effectual word of God from Genesis. John's genius is that logos works in both worlds simultaneously. He tells the Greeks: the rational principle you have been searching for has a face. He tells the Jews: the creating word of God has become flesh."
            },
            {
                "commentator": "N.T. Wright",
                "work": "John for Everyone (2002)",
                "insight": "Wright argues that 'the Word became flesh and dwelt among us' (John 1:14) is a direct echo of the tabernacle. The word translated 'dwelt' is literally 'tabernacled' (eskēnōsen). John is saying: the presence of God that once filled the tabernacle, then Solomon's temple, and then departed in Ezekiel's vision — that same presence has now taken up residence in a human person. The temple story reaches its unexpected climax not in a building but in a body."
            }
        ]
    },
    "psalm_119": {
        "passage": "Psalm 119",
        "commentaries": [
            {
                "commentator": "Charles Spurgeon",
                "work": "The Treasury of David (1869-1885)",
                "insight": "Spurgeon devoted enormous attention to Psalm 119, calling it the saints' classic on the Word of God. He noted that the psalmist does not merely commend the Torah abstractly but speaks of it with personal passion — 'I love your commandments above gold.' This is not legal observance but covenant delight. The psalmist has discovered that the Torah is not a cage but a home — the place where life makes sense and flourishes."
            },
            {
                "commentator": "John Calvin",
                "work": "Commentary on the Psalms (1557)",
                "insight": "Calvin observed that Psalm 119's acrostic structure — 22 sections, one for each letter of the Hebrew alphabet — is itself a theological statement. The Torah encompasses all of reality from aleph to tav, as we would say from A to Z. No area of life lies outside its scope. The structure says: there is no letter, no word, no domain of existence that does not belong to the God whose Torah this is."
            }
        ]
    }
}


# ── Input Models ──────────────────────────────────────────────────────────────

class BibleReferenceInput(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid"
    )
    reference: str = Field(
        ...,
        description="Bible reference to analyse. Examples: 'Psalm 119', '1 Chronicles 2', 'Romans 8:1-17', 'Genesis 22'",
        min_length=2,
        max_length=100
    )
    section: Optional[str] = Field(
        default="all",
        description="Which analysis section to run: 'context', 'lexicon', 'chronology', 'narrative', 'patterns', 'all'"
    )

class LexiconInput(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid"
    )
    term: str = Field(
        ...,
        description="Hebrew or Greek term to look up. Can be the English translation or transliteration. Examples: 'torah', 'hesed', 'logos', 'agape', 'shalom'",
        min_length=2,
        max_length=50
    )

class ChronologyInput(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid"
    )
    reference: str = Field(
        ...,
        description="Bible reference or period to compute chronology for. Examples: 'Genesis 5', '1 Chronicles 2', 'patriarchs', 'exodus to david'",
        min_length=2,
        max_length=100
    )
    compute_overlaps: bool = Field(
        default=True,
        description="Whether to compute lifespan overlaps and generational concurrency"
    )

class StudyInput(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid"
    )
    reference: str = Field(
        ...,
        description="Bible chapter or passage for full 6-section deep study. Examples: 'Psalm 119', '1 Chronicles 2', 'Acts 5', 'Romans 8'",
        min_length=2,
        max_length=100
    )
    depth: Optional[str] = Field(
        default="full",
        description="Analysis depth: 'quick' (sections 1+3 only) or 'full' (all 6 sections)"
    )


# ── Tools ─────────────────────────────────────────────────────────────────────

@mcp.tool(
    name="bible_lexicon",
    annotations={
        "title": "Hebrew/Greek Lexicon",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def bible_lexicon(params: LexiconInput) -> str:
    """
    Look up Hebrew or Greek terms with full semantic range, theological weight,
    and translation distortion analysis.

    Returns the original word, transliteration, root meaning, full conceptual range,
    theological significance, translation problems in English, and key passages.

    Use this when analysing a passage to identify words whose English translation
    flattens or distorts the original meaning.

    Args:
        params (LexiconInput): Input containing:
            - term (str): Hebrew or Greek term to look up (English or transliteration)

    Returns:
        str: JSON with full lexical analysis including semantic range and theological weight
    """
    term_lower = params.term.lower().strip()

    # Direct lookup
    if term_lower in LEXICON:
        entry = LEXICON[term_lower]
        return json.dumps({
            "found": True,
            "term": params.term,
            "entry": entry,
            "note": "Entry from biblical lexicon database"
        }, indent=2, ensure_ascii=False)

    # Fuzzy match — search by partial term
    matches = []
    for key, entry in LEXICON.items():
        if (term_lower in key or
            term_lower in entry.get("transliteration", "").lower() or
            term_lower in entry.get("hebrew", "").lower() or
            term_lower in entry.get("greek", "").lower()):
            matches.append({"term": key, "entry": entry})

    if matches:
        return json.dumps({
            "found": True,
            "search_term": params.term,
            "matches": matches,
            "note": f"Found {len(matches)} partial match(es)"
        }, indent=2, ensure_ascii=False)

    # Not found
    available = list(LEXICON.keys())
    return json.dumps({
        "found": False,
        "search_term": params.term,
        "available_terms": available,
        "suggestion": f"Term '{params.term}' not in database. Available: {', '.join(available[:10])}... Use bible_study tool for full passage analysis which will identify key terms automatically.",
        "note": "Database contains key theological terms. For comprehensive lexical work, cross-reference with Strong's concordance or BDAG."
    }, indent=2)


@mcp.tool(
    name="bible_chronology",
    annotations={
        "title": "Biblical Chronology & Generational Mapping",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def bible_chronology(params: ChronologyInput) -> str:
    """
    Compute biblical chronology, lifespan overlaps, generational concurrency,
    and transmission type analysis for any biblical period or passage.

    Determines whether theological knowledge in a passage was living memory,
    generational transmission, or institutional/textual preservation.

    Flags timeline compressions and telescoped genealogies.
    Identifies covenant, political, and inheritance implications of key events.

    Args:
        params (ChronologyInput): Input containing:
            - reference (str): Bible reference or period name
            - compute_overlaps (bool): Whether to compute lifespan overlaps

    Returns:
        str: JSON with chronological data, overlap computations, and interpretation flags
    """
    ref_lower = params.reference.lower()

    # Find relevant period
    matched_periods = []
    for period_key, period_data in CHRONOLOGY.items():
        if (period_key in ref_lower or
            any(fig["name"].lower() in ref_lower
                for fig in period_data.get("figures", [])
                if isinstance(fig.get("name"), str))):
            matched_periods.append((period_key, period_data))

    # Match by content keywords
    if not matched_periods:
        keyword_map = {
            "genesis 5": "adam_to_noah",
            "genesis 11": "noah_to_abraham",
            "chronicles 2": "exodus_to_david",
            "1 chronicles 2": "exodus_to_david",
            "ruth": "exodus_to_david",
            "patriarch": "patriarchs",
            "abraham": "patriarchs",
            "isaac": "patriarchs",
            "jacob": "patriarchs",
            "joseph": "patriarchs",
            "exodus": "exodus_to_david",
            "david": "exodus_to_david",
            "paul": "new_testament",
            "jesus": "new_testament",
            "acts": "new_testament",
            "romans": "new_testament",
            "exile": "monarchy_to_exile",
            "babylon": "monarchy_to_exile",
            "flood": "adam_to_noah",
            "noah": "adam_to_noah",
        }
        for keyword, period_key in keyword_map.items():
            if keyword in ref_lower and period_key in CHRONOLOGY:
                matched_periods.append((period_key, CHRONOLOGY[period_key]))
                break

    if not matched_periods:
        return json.dumps({
            "reference": params.reference,
            "found": False,
            "available_periods": list(CHRONOLOGY.keys()),
            "suggestion": "Reference not matched. Try: 'patriarchs', 'exodus to david', 'adam to noah', 'monarchy to exile', 'new testament'"
        }, indent=2)

    results = []
    for period_key, period_data in matched_periods:
        result = {
            "period": period_key,
            "data": period_data,
        }

        # Compute overlaps if requested and figures available
        if params.compute_overlaps and "figures" in period_data:
            figures = period_data["figures"]
            overlaps = []
            for i, fig1 in enumerate(figures):
                for fig2 in figures[i+1:]:
                    b1 = fig1.get("born")
                    d1 = fig1.get("died")
                    b2 = fig2.get("born")
                    if all(isinstance(x, (int, float)) for x in [b1, d1, b2]):
                        overlap_years = d1 - b2
                        if overlap_years > 0:
                            overlaps.append({
                                "person_1": fig1["name"],
                                "person_2": fig2["name"],
                                "overlap_years": overlap_years,
                                "interpretation": f"{fig1['name']} and {fig2['name']} overlapped by {overlap_years} years — direct knowledge transmission was possible"
                            })

            result["lifespan_overlaps"] = overlaps
            result["overlap_count"] = len(overlaps)

        results.append(result)

    return json.dumps({
        "reference": params.reference,
        "found": True,
        "periods": results,
        "interpretation_note": "Chronology based on internal biblical data (Masoretic text). Alternative chronologies exist. Dates marked BC use traditional evangelical chronology. AM dates are Anno Mundi (years from creation per biblical genealogies)."
    }, indent=2, ensure_ascii=False)


@mcp.tool(
    name="bible_context",
    annotations={
        "title": "Historical & Cultural Context",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def bible_context(params: BibleReferenceInput) -> str:
    """
    Retrieve the historical, political, cultural, economic, and geographic context
    for any biblical passage or period.

    Identifies the political structure in operation, economic realities, cultural customs,
    geographic significance, power dynamics, and social norms.

    This establishes the world of the text before interpretation begins.

    Args:
        params (BibleReferenceInput): Input containing:
            - reference (str): Bible reference or passage

    Returns:
        str: JSON with structured contextual data for the passage's historical world
    """
    ref_lower = params.reference.lower()

    # Map reference to political epoch — all 66 books covered
    # Ordered longest-match first so "1 kings 11" matches before "1 kings 1"
    epoch_map = [
        # ── Genesis (chapters span multiple epochs) ──────────────────────────
        ("genesis 1",          "patriarchal"),
        ("genesis 2",          "patriarchal"),
        ("genesis 3",          "patriarchal"),
        ("genesis 4",          "patriarchal"),
        ("genesis 5",          "patriarchal"),   # genealogy Adam-Noah
        ("genesis 6",          "patriarchal"),
        ("genesis 7",          "patriarchal"),
        ("genesis 8",          "patriarchal"),
        ("genesis 9",          "patriarchal"),
        ("genesis 10",         "patriarchal"),
        ("genesis 11",         "patriarchal"),   # Tower of Babel / Shem-Terah
        ("genesis 12",         "patriarchal"),
        ("genesis 13",         "patriarchal"),
        ("genesis 14",         "patriarchal"),
        ("genesis 15",         "patriarchal"),
        ("genesis 16",         "patriarchal"),
        ("genesis 17",         "patriarchal"),
        ("genesis 18",         "patriarchal"),
        ("genesis 19",         "patriarchal"),
        ("genesis 20",         "patriarchal"),
        ("genesis 21",         "patriarchal"),
        ("genesis 22",         "patriarchal"),
        ("genesis 23",         "patriarchal"),
        ("genesis 24",         "patriarchal"),
        ("genesis 25",         "patriarchal"),
        ("genesis 26",         "patriarchal"),
        ("genesis 27",         "patriarchal"),
        ("genesis 28",         "patriarchal"),
        ("genesis 29",         "patriarchal"),
        ("genesis 30",         "patriarchal"),
        ("genesis 31",         "patriarchal"),
        ("genesis 32",         "patriarchal"),
        ("genesis 33",         "patriarchal"),
        ("genesis 34",         "patriarchal"),
        ("genesis 35",         "patriarchal"),
        ("genesis 36",         "patriarchal"),
        ("genesis 37",         "patriarchal"),
        ("genesis 38",         "patriarchal"),   # Judah & Tamar
        ("genesis 39",         "patriarchal"),
        ("genesis 40",         "patriarchal"),
        ("genesis 41",         "patriarchal"),
        ("genesis 42",         "patriarchal"),
        ("genesis 43",         "patriarchal"),
        ("genesis 44",         "patriarchal"),
        ("genesis 45",         "patriarchal"),
        ("genesis 46",         "patriarchal"),
        ("genesis 47",         "patriarchal"),
        ("genesis 48",         "patriarchal"),
        ("genesis 49",         "patriarchal"),
        ("genesis 50",         "patriarchal"),
        # ── Pentateuch ───────────────────────────────────────────────────────
        ("exodus",             "egyptian_slavery"),
        ("leviticus",          "wilderness"),
        ("numbers",            "wilderness"),
        ("deuteronomy",        "wilderness"),
        # ── Historical books ─────────────────────────────────────────────────
        ("joshua",             "judges"),
        ("judges",             "judges"),
        ("ruth",               "judges"),
        ("1 samuel",           "united_monarchy"),
        ("2 samuel",           "united_monarchy"),
        ("1 kings 11",         "divided_monarchy"),  # must come before "1 kings 1"
        ("1 kings 12",         "divided_monarchy"),
        ("1 kings 13",         "divided_monarchy"),
        ("1 kings 14",         "divided_monarchy"),
        ("1 kings 15",         "divided_monarchy"),
        ("1 kings 16",         "divided_monarchy"),
        ("1 kings 17",         "divided_monarchy"),
        ("1 kings 18",         "divided_monarchy"),
        ("1 kings 19",         "divided_monarchy"),
        ("1 kings 20",         "divided_monarchy"),
        ("1 kings 21",         "divided_monarchy"),
        ("1 kings 22",         "divided_monarchy"),
        ("1 kings 1",          "united_monarchy"),
        ("1 kings 2",          "united_monarchy"),
        ("1 kings 3",          "united_monarchy"),
        ("1 kings 4",          "united_monarchy"),
        ("1 kings 5",          "united_monarchy"),
        ("1 kings 6",          "united_monarchy"),
        ("1 kings 7",          "united_monarchy"),
        ("1 kings 8",          "united_monarchy"),
        ("1 kings 9",          "united_monarchy"),
        ("1 kings 10",         "united_monarchy"),
        ("2 kings",            "divided_monarchy"),
        ("1 chronicles",       "persian_period"),   # written for post-exilic community
        ("2 chronicles",       "persian_period"),
        ("ezra",               "persian_period"),
        ("nehemiah",           "persian_period"),
        ("esther",             "persian_period"),
        # ── Wisdom & Poetry ──────────────────────────────────────────────────
        ("job",                "patriarchal"),       # patriarchal setting; uncertain date
        ("psalm 119",          "persian_period"),
        ("psalms",             "divided_monarchy"),  # compilation spans; core is monarchic
        ("psalm",              "divided_monarchy"),
        ("proverbs",           "united_monarchy"),   # Solomonic core; edited post-exile
        ("ecclesiastes",       "persian_period"),    # likely late wisdom tradition
        ("song of solomon",    "united_monarchy"),
        ("song of songs",      "united_monarchy"),
        # ── Major Prophets ───────────────────────────────────────────────────
        ("isaiah",             "divided_monarchy"),  # chs 1-39 pre-exilic; 40-66 exilic
        ("jeremiah",           "babylonian_exile"),
        ("lamentations",       "babylonian_exile"),
        ("ezekiel",            "babylonian_exile"),
        ("daniel",             "babylonian_exile"),
        # ── Minor Prophets ───────────────────────────────────────────────────
        ("hosea",              "divided_monarchy"),  # northern kingdom, 8th c. BC
        ("joel",               "persian_period"),    # post-exilic; date debated
        ("amos",               "divided_monarchy"),  # northern kingdom, 8th c. BC
        ("obadiah",            "babylonian_exile"),  # after Jerusalem's fall, 586 BC
        ("jonah",              "divided_monarchy"),  # Assyrian period setting
        ("micah",              "divided_monarchy"),  # 8th c. BC, Judah
        ("nahum",              "divided_monarchy"),  # before fall of Nineveh, 612 BC
        ("habakkuk",           "divided_monarchy"),  # late 7th c. BC, Babylonian threat
        ("zephaniah",          "divided_monarchy"),  # reign of Josiah, 7th c. BC
        ("haggai",             "persian_period"),
        ("zechariah",          "persian_period"),
        ("malachi",            "persian_period"),
        # ── Gospels & Acts ───────────────────────────────────────────────────
        ("matthew",            "roman_period"),
        ("mark",               "roman_period"),
        ("luke",               "roman_period"),
        ("john",               "roman_period"),
        ("acts",               "roman_period"),
        # ── Pauline Epistles ─────────────────────────────────────────────────
        ("romans",             "roman_period"),
        ("1 corinthians",      "roman_period"),
        ("2 corinthians",      "roman_period"),
        ("galatians",          "roman_period"),
        ("ephesians",          "roman_period"),
        ("philippians",        "roman_period"),
        ("colossians",         "roman_period"),
        ("1 thessalonians",    "roman_period"),
        ("2 thessalonians",    "roman_period"),
        ("1 timothy",          "roman_period"),
        ("2 timothy",          "roman_period"),
        ("titus",              "roman_period"),
        ("philemon",           "roman_period"),
        # ── General Epistles ─────────────────────────────────────────────────
        ("hebrews",            "roman_period"),      # Jewish-Christian context, AD 60s
        ("james",              "roman_period"),      # earliest NT letter, AD 40s-50s
        ("1 peter",            "roman_period"),      # persecution under Nero, AD 64-68
        ("2 peter",            "roman_period"),
        ("1 john",             "roman_period"),
        ("2 john",             "roman_period"),
        ("3 john",             "roman_period"),
        ("jude",               "roman_period"),
        # ── Apocalyptic ──────────────────────────────────────────────────────
        ("revelation",         "roman_period"),      # Domitian persecution, AD 90s
    ]

    matched_epoch = None
    for ref_key, epoch_key in epoch_map:
        if ref_key in ref_lower:
            matched_epoch = epoch_key
            break

    # Fallback: generic book name without chapter number
    if not matched_epoch:
        if any(w in ref_lower for w in ["psalm", "proverb", "ecclesiastes", "song"]):
            matched_epoch = "divided_monarchy"
        elif any(w in ref_lower for w in ["genesis"]):
            matched_epoch = "patriarchal"

    if matched_epoch and matched_epoch in POLITICAL_EPOCHS:
        epoch = POLITICAL_EPOCHS[matched_epoch]
        return json.dumps({
            "reference": params.reference,
            "matched_epoch": matched_epoch,
            "context": epoch,
            "study_note": f"This passage operates in the '{matched_epoch}' world. Establish this context before interpreting meaning — the text assumes this world, not ours."
        }, indent=2, ensure_ascii=False)

    return json.dumps({
        "reference": params.reference,
        "matched_epoch": None,
        "available_epochs": list(POLITICAL_EPOCHS.keys()),
        "context": POLITICAL_EPOCHS,
        "note": "Could not match reference to specific epoch. Full epoch database returned."
    }, indent=2, ensure_ascii=False)


@mcp.tool(
    name="bible_study",
    annotations={
        "title": "Full 6-Section Bible Study Analysis",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def bible_study(params: StudyInput) -> str:
    """
    Orchestrates a full 6-section deep Bible study analysis for any chapter or passage.

    Calls bible_context, bible_lexicon, and bible_chronology internally to provide
    structured, consistent, verifiable analysis — then delivers the complete prompt
    framework for Claude to execute.

    Sections delivered:
        1. World of the Text — political, economic, cultural, geographic context
        2. Language Precision — Hebrew/Greek terms with full semantic range
        3. Conceptual Rendering — what the passage is actually communicating
        4. Pattern & Structure — repetition, literary devices, thematic echoes
        5. Narrative Logic — why this sequence, in this order
        6. Chronological Intelligence — generational mapping, transmission type

    Args:
        params (StudyInput): Input containing:
            - reference (str): Bible chapter or passage
            - depth (str): 'quick' or 'full'

    Returns:
        str: JSON containing all structured data + the analysis prompt for Claude to execute
    """
    ref = params.reference
    ref_lower = ref.lower()

    # Gather context data
    context_params = BibleReferenceInput(reference=ref)
    context_result = await bible_context(context_params)
    context_data = json.loads(context_result)

    # Gather chronology data
    chron_params = ChronologyInput(reference=ref, compute_overlaps=True)
    chron_result = await bible_chronology(chron_params)
    chron_data = json.loads(chron_result)

    # Identify likely key terms for the passage
    term_hints = {
        # ── Pentateuch ───────────────────────────────────────────────────────
        "genesis":           ["toledot", "bara", "hesed", "dabar", "berith", "nephesh"],
        "exodus":            ["hesed", "kabod", "torah", "qadosh", "shema", "mishkan"],
        "leviticus":         ["qadosh", "mishkan", "berith", "tsaddiq"],
        "numbers":           ["qadosh", "kabod", "shema", "malak"],
        "deuteronomy":       ["shema", "torah", "berith", "hesed", "anawim"],
        # ── Historical ───────────────────────────────────────────────────────
        "joshua":            ["berith", "hesed", "dabar", "shema"],
        "judges":            ["shema", "ruach", "malak", "hesed"],
        "ruth":              ["hesed", "berith", "tsaddiq", "anawim"],
        "1 samuel":          ["dabar", "ruach", "malak", "berith"],
        "2 samuel":          ["berith", "hesed", "dabar", "tsaddiq"],
        "1 kings":           ["dabar", "kabod", "mishkan", "berith"],
        "2 kings":           ["dabar", "shema", "torah", "berith"],
        "1 chronicles":      ["toledot", "hesed", "bekhor", "dabar", "berith"],
        "2 chronicles":      ["hesed", "kabod", "mishkan", "berith", "shema"],
        "ezra":              ["torah", "berith", "qadosh", "shema"],
        "nehemiah":          ["torah", "berith", "hesed", "shema"],
        "esther":            ["hesed", "berith", "tsaddiq"],
        # ── Wisdom & Poetry ──────────────────────────────────────────────────
        "job":               ["hesed", "nephesh", "ruach", "tsaddiq", "dabar"],
        "psalm 119":         ["torah", "hesed", "ashrei", "dabar", "emunah"],
        "psalm":             ["hesed", "ashrei", "ruach", "nephesh", "emet", "dabar"],
        "psalms":            ["hesed", "ashrei", "ruach", "nephesh", "emet", "dabar"],
        "proverbs":          ["hesed", "emet", "tsaddiq", "shema", "dabar"],
        "ecclesiastes":      ["nephesh", "ruach", "hesed", "dabar"],
        "song of solomon":   ["hesed", "dabar", "nephesh"],
        "song of songs":     ["hesed", "dabar", "nephesh"],
        # ── Major Prophets ───────────────────────────────────────────────────
        "isaiah":            ["hesed", "kabod", "qadosh", "shalom", "dabar", "anawim", "berith"],
        "jeremiah":          ["berith", "hesed", "shema", "dabar", "tsaddiq"],
        "lamentations":      ["hesed", "emet", "anawim", "ruach"],
        "ezekiel":           ["kabod", "ruach", "berith", "mishkan", "qadosh"],
        "daniel":            ["qadosh", "berith", "hesed", "mishkan"],
        # ── Minor Prophets ───────────────────────────────────────────────────
        "hosea":             ["hesed", "berith", "dabar", "shema", "emet"],
        "joel":              ["ruach", "dabar", "shema", "hesed"],
        "amos":              ["tsaddiq", "shema", "hesed", "anawim", "dabar"],
        "obadiah":           ["hesed", "tsaddiq", "dabar"],
        "jonah":             ["hesed", "shema", "dabar", "ruach"],
        "micah":             ["hesed", "tsaddiq", "mishpat", "dabar", "berith"],
        "nahum":             ["hesed", "kabod", "dabar"],
        "habakkuk":          ["emunah", "tsaddiq", "dabar", "hesed"],
        "zephaniah":         ["anawim", "shema", "dabar", "hesed"],
        "haggai":            ["kabod", "mishkan", "dabar", "berith"],
        "zechariah":         ["berith", "ruach", "dabar", "hesed", "kabod"],
        "malachi":           ["hesed", "berith", "torah", "malak", "shema"],
        # ── Gospels & Acts ───────────────────────────────────────────────────
        "matthew":           ["logos", "dikaiosyne", "ekklesia", "parousia", "agape", "pistis"],
        "mark":              ["pistis", "kairos", "pneuma", "huios", "soteria"],
        "luke":              ["soteria", "charis", "agape", "anawim", "pistis"],
        "john":              ["logos", "agape", "pistis", "pneuma", "kairos", "sarx"],
        "acts":              ["pneuma", "ekklesia", "kairos", "pistis", "soteria", "charis"],
        # ── Pauline Epistles ─────────────────────────────────────────────────
        "romans":            ["dikaiosyne", "pistis", "charis", "sarx", "pneuma", "apolutrosis", "emunah"],
        "1 corinthians":     ["agape", "charis", "pneuma", "logos", "mysterion", "sarx"],
        "2 corinthians":     ["charis", "pneuma", "dikaiosyne", "sarx", "kairos"],
        "galatians":         ["pistis", "charis", "sarx", "pneuma", "emunah", "dikaiosyne"],
        "ephesians":         ["charis", "ekklesia", "mysterion", "pneuma", "agape", "apolutrosis"],
        "philippians":       ["charis", "agape", "dikaiosyne", "pneuma", "kairos"],
        "colossians":        ["mysterion", "charis", "logos", "pneuma", "apolutrosis"],
        "1 thessalonians":   ["parousia", "pistis", "agape", "pneuma", "kairos"],
        "2 thessalonians":   ["parousia", "pistis", "charis", "pneuma"],
        "1 timothy":         ["pistis", "dikaiosyne", "charis", "logos", "pneuma"],
        "2 timothy":         ["pistis", "charis", "logos", "pneuma", "dikaiosyne"],
        "titus":             ["charis", "soteria", "dikaiosyne", "pistis", "logos"],
        "philemon":          ["agape", "charis", "pistis", "apolutrosis"],
        # ── General Epistles ─────────────────────────────────────────────────
        "hebrews":           ["berith", "pistis", "apolutrosis", "mysterion", "kabod", "dikaiosyne"],
        "james":             ["logos", "pistis", "dikaiosyne", "agape", "hesed", "anawim"],
        "1 peter":           ["charis", "agape", "soteria", "pneuma", "qadosh", "parousia"],
        "2 peter":           ["charis", "parousia", "logos", "pneuma", "pistis"],
        "1 john":            ["agape", "logos", "pistis", "pneuma", "soteria"],
        "2 john":            ["agape", "logos", "pistis"],
        "3 john":            ["agape", "pistis", "logos"],
        "jude":              ["pistis", "agape", "pneuma", "charis"],
        # ── Apocalyptic ──────────────────────────────────────────────────────
        "revelation":        ["logos", "kabod", "mysterion", "parousia", "soteria", "agape"],
    }

    suggested_terms = []
    # Sort by key length descending so "psalm 119" matches before "psalm"
    for book_key in sorted(term_hints.keys(), key=len, reverse=True):
        if book_key in ref_lower:
            suggested_terms = term_hints[book_key]
            break

    if not suggested_terms:
        suggested_terms = ["hesed", "dabar", "qadosh", "emunah"]

    # Fetch lexicon entries for suggested terms
    lexicon_entries = {}
    for term in suggested_terms:
        if term in LEXICON:
            lexicon_entries[term] = LEXICON[term]

    # Build the analysis prompt
    quick_mode = params.depth == "quick"

    analysis_prompt = f"""
BIBLE STUDY — DEEP CONTEXT ANALYSIS
Reference: {ref}
{"(Quick Mode: Sections 1 and 3 only)" if quick_mode else "(Full Analysis: All 6 Sections)"}

The following structured data has been retrieved from the Bible Study MCP server.
Use it as the verified foundation for your analysis. Do not contradict it.
Surface chronological findings only when they materially affect interpretation.

═══════════════════════════════════════════
VERIFIED CONTEXT DATA (from bible_context tool)
═══════════════════════════════════════════
{json.dumps(context_data, indent=2)}

═══════════════════════════════════════════
VERIFIED CHRONOLOGY DATA (from bible_chronology tool)
═══════════════════════════════════════════
{json.dumps(chron_data, indent=2)}

═══════════════════════════════════════════
KEY TERM LEXICON ENTRIES (from bible_lexicon tool)
═══════════════════════════════════════════
{json.dumps(lexicon_entries, indent=2, ensure_ascii=False)}

═══════════════════════════════════════════
NOW DELIVER THE FOLLOWING IN SEQUENCE:
═══════════════════════════════════════════

SECTION 1 — WORLD OF THE TEXT
Using the verified context data above as your foundation:
- Establish the political structure in operation
- Identify economic realities shaping the people
- Surface cultural customs being observed or subverted
- Explain geographic significance of named locations
- Map power dynamics — who has authority, who is marginalised
- Identify social norms being upheld or broken
Do not interpret yet. Only establish the world.

SECTION 2 — LANGUAGE PRECISION
Using the lexicon entries above as anchors:
- Identify additional key Hebrew or Greek terms in this passage
- For each: original word, transliteration, full semantic range
- Where has translation flattened or distorted meaning?
- What theological weight is lost in English?
Focus on words governing: covenant, authority, identity, action, divine character.

SECTION 3 — CONCEPTUAL RENDERING
Explain what the passage is actually communicating — in logical groupings:
- Stay anchored to original language meaning from Section 2
- Explain the argument or narrative, not just what happens
- Show structural flow — how one movement leads to the next
- Identify the claim being built across the passage
- Do not reproduce copyrighted translation text

{"" if quick_mode else '''
SECTION 4 — PATTERN & STRUCTURE
Surface what repetition reveals:
- Repeated words, phrases, numbers, or images
- Why repetition is deliberate and what it signals
- Literary contrasts and parallels within the passage
- Thematic echoes in adjacent chapters or books
- Structural devices: chiasm, inclusio, parallelism, acrostic

SECTION 5 — NARRATIVE LOGIC
Explain why this sequence, in this order:
- What created the conditions for each event or statement?
- What tension is being resolved — or created?
- What is escalating, narrowing, or reversing?
- What theological claim depends on this sequence?
Show how each movement unlocks the next. Do not summarise. Trace the logic.

SECTION 6 — CHRONOLOGICAL INTELLIGENCE
Using the verified chronology data above:
- Surface only findings that materially change interpretation
- Identify whether theological memory is living, generational, or institutional
- Flag timeline compressions and their implications
- State covenant, political, and inheritance implications of key events
- Do not produce genealogical tables unless they change interpretation
'''}
"""

    return json.dumps({
        "reference": ref,
        "depth": params.depth,
        "context_data": context_data,
        "chronology_data": chron_data,
        "lexicon_entries": lexicon_entries,
        "suggested_key_terms": suggested_terms,
        "analysis_prompt": analysis_prompt,
        "instruction": "Pass the analysis_prompt to Claude for full execution. The structured data provides the verified foundation; Claude supplies the interpretive analysis.",
        "mcp_note": "Data sourced from Bible Study MCP server v1.0. Lexicon: embedded theological term database. Chronology: Masoretic text internal data. Context: historical epoch database."
    }, indent=2, ensure_ascii=False)


class DeepStudyInput(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid"
    )
    reference: str = Field(
        ...,
        description="Bible chapter or passage for 8-layer deep study. Examples: 'Genesis 1', 'Psalm 23', 'Romans 8', 'John 1:1-18'",
        min_length=2,
        max_length=100
    )


@mcp.tool(
    name="bible_deep_study",
    annotations={
        "title": "4-Layer Deep Bible Study (BibleDeepDive)",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def bible_deep_study(params: DeepStudyInput) -> str:
    """
    Delivers a full 8-layer BibleDeepDive analysis for any passage.

    Segun's 8-layer study methodology:
        Layer 1 — Chapter Breakdown
            Original language precision, historical and political grounding.
            What the text actually says in its world.

        Layer 2 — Structural and Literary Craft
            How the form carries meaning — chiasm, parallelism, genre,
            narrative arc. The craft of the text as theological argument.

        Layer 3 — Covenantal Framework
            Which covenant is in view, what obligations and promises apply,
            how this passage advances the covenant chain.

        Layer 4 — Cross-Linkages
            Thematic and verbal connections across all of Scripture.
            OT echoes, NT fulfilments, type and antitype.

        Layer 5 — Christocentric Reading
            Christ as the interpretive centre. How this passage points to,
            finds fulfilment in, or illuminates Jesus Christ.

        Layer 6 — Doctrinal Theology
            What this passage teaches about God, humanity, salvation,
            the Spirit, the church, and last things.

        Layer 7 — Commentary Insights
            Attributed voices: Spurgeon, Calvin, Matthew Henry,
            N.T. Wright, William Barclay. The wisdom of the tradition.

        Layer 8 — Current Scenario
            Specific, concrete parallels to today's world. Where this
            ancient text meets present realities with precision.
    """
    ref = params.reference
    ref_lower = ref.lower()

    # ── 1. Get historical context ─────────────────────────────────────────────
    context_params = BibleReferenceInput(reference=ref)
    context_result = await bible_context(context_params)
    context_data = json.loads(context_result)

    # ── 2. Get chronology data ────────────────────────────────────────────────
    chron_params = ChronologyInput(reference=ref, compute_overlaps=True)
    chron_result = await bible_chronology(chron_params)
    chron_data = json.loads(chron_result)

    # ── 3. Get relevant lexicon terms ─────────────────────────────────────────
    term_hints = {
        "genesis 1": ["bara", "ruach", "elohim", "dabar", "tselem", "qadosh", "shema"],
        "genesis 2": ["nephesh", "mishkan", "tselem", "dabar", "hesed"],
        "genesis 3": ["nephesh", "berith", "hesed", "mishpat"],
        "genesis 22": ["berith", "hesed", "bekhor", "mishpat"],
        "genesis": ["toledot", "hesed", "dabar", "ruach", "bara", "berith"],
        "exodus": ["hesed", "kabod", "torah", "qadosh", "hesed_emet", "mishkan", "shema"],
        "leviticus": ["qadosh", "mishkan", "berith", "mishpat", "tsaddiq"],
        "numbers": ["mishkan", "shema", "berith", "anawim"],
        "deuteronomy": ["shema", "torah", "berith", "hesed", "mishpat"],
        "psalm 23": ["hesed", "mishpat", "tsaddiq", "ruach"],
        "psalm 119": ["torah", "hesed", "ashrei", "emet", "dabar", "emunah", "mishpat"],
        "psalm": ["torah", "hesed", "ashrei", "emet", "dabar", "anawim"],
        "isaiah": ["kabod", "qadosh", "hesed", "mishpat", "malak", "soteria"],
        "jeremiah": ["berith", "hesed", "mishpat", "shema"],
        "ezekiel": ["kabod", "ruach", "mishkan", "berith"],
        "daniel": ["malak", "mysterion", "parousia"],
        "hosea": ["hesed", "berith", "shema", "dabar"],
        "amos": ["mishpat", "tsaddiq", "anawim", "shema"],
        "micah": ["mishpat", "hesed", "berith"],
        "habakkuk": ["emunah", "tsaddiq", "mishpat"],
        "matthew": ["ekklesia", "dikaiosyne", "huios", "parousia", "soteria", "mysterion"],
        "mark": ["huios", "kairos", "soteria", "ekklesia"],
        "luke": ["soteria", "anawim", "kairos", "huios", "dikaiosyne"],
        "john 1": ["logos", "sarx", "mishkan", "pneuma", "huios", "charis"],
        "john": ["logos", "agape", "pistis", "kairos", "pneuma", "huios"],
        "acts": ["kairos", "charis", "pistis", "ekklesia", "soteria", "pneuma"],
        "romans": ["pistis", "charis", "dikaiosyne", "sarx", "pneuma", "apolutrosis", "huios"],
        "1 corinthians": ["agape", "charis", "logos", "pneuma", "ekklesia", "sarx"],
        "2 corinthians": ["charis", "sarx", "pneuma", "dikaiosyne"],
        "galatians": ["pistis", "charis", "emunah", "sarx", "pneuma", "apolutrosis"],
        "ephesians": ["charis", "agape", "mysterion", "ekklesia", "apolutrosis"],
        "philippians": ["charis", "dikaiosyne", "soteria"],
        "colossians": ["mysterion", "apolutrosis", "logos", "sarx"],
        "1 thessalonians": ["parousia", "pistis", "agape"],
        "hebrews": ["berith", "mishkan", "huios", "apolutrosis", "pistis", "emunah"],
        "james": ["pistis", "mishpat", "anawim", "dikaiosyne"],
        "1 peter": ["apolutrosis", "qadosh", "parousia", "soteria"],
        "revelation": ["parousia", "mysterion", "ekklesia", "soteria", "kairos"],
    }

    suggested_terms = ["hesed", "dabar", "qadosh", "emunah"]  # default
    for book_key, terms in term_hints.items():
        if book_key in ref_lower:
            suggested_terms = terms
            break

    lexicon_entries = {k: LEXICON[k] for k in suggested_terms if k in LEXICON}

    # ── 4. Get commentary for this passage ────────────────────────────────────
    commentary_entries = []
    commentary_key_map = {
        "genesis 1": "genesis_1",
        "genesis 22": "genesis_22",
        "psalm 23": "psalm_23",
        "psalm 119": "psalm_119",
        "romans 8": "romans_8",
        "john 1": "john_1",
    }

    matched_commentary_key = None
    for ref_fragment, key in commentary_key_map.items():
        if ref_fragment in ref_lower:
            matched_commentary_key = key
            break

    if matched_commentary_key and matched_commentary_key in COMMENTARY:
        commentary_entries = COMMENTARY[matched_commentary_key]["commentaries"]

    commentary_text = ""
    if commentary_entries:
        commentary_text = "\n\nCOMMENTARY DATABASE ENTRIES FOR THIS PASSAGE:\n"
        for c in commentary_entries:
            commentary_text += f"\n{c['commentator']} ({c['work']}):\n{c['insight']}\n"

    # ── 5. Build the 8-layer analysis prompt ──────────────────────────────────
    analysis_prompt = f"""
BIBLEDEEPDIVE — 8-LAYER STUDY ANALYSIS
Reference: {ref}

You are delivering Segun's 8-layer BibleDeepDive methodology.
The structured data below is your verified foundation. Use it precisely.
Do not contradict the historical context, lexicon, or chronological data provided.
Do not skip any layer. Each layer is essential and distinct.

═══════════════════════════════════════════════
VERIFIED HISTORICAL CONTEXT
═══════════════════════════════════════════════
{json.dumps(context_data, indent=2, ensure_ascii=False)}

═══════════════════════════════════════════════
CHRONOLOGICAL DATA
═══════════════════════════════════════════════
{json.dumps(chron_data, indent=2, ensure_ascii=False)}

═══════════════════════════════════════════════
KEY TERM LEXICON ENTRIES
═══════════════════════════════════════════════
{json.dumps(lexicon_entries, indent=2, ensure_ascii=False)}
{commentary_text}

═══════════════════════════════════════════════
DELIVER ALL 8 LAYERS IN SEQUENCE — DO NOT SKIP ANY
═══════════════════════════════════════════════

LAYER 1 — CHAPTER BREAKDOWN
The world of the text. Original language precision. Historical and political grounding.
- What is the passage actually communicating? What argument or narrative is being built?
- Surface key original language terms — explain exactly what is lost in English translation
- Use the verified historical context above to establish the world the text assumes
- Trace the structure and movement through the passage — how does it build?
- What would the original hearers have understood that modern readers miss entirely?
- What is the authorial intent grounded in this specific historical moment?

LAYER 2 — STRUCTURAL AND LITERARY CRAFT
How the form carries the meaning. This is separate from content.
- What literary genre is this — poetry, narrative, prophecy, epistle, apocalyptic?
- Identify structural features: chiasm, parallelism, inclusio, refrain, acrostic, narrative arc
- How does the structure itself make a theological argument?
- What is the effect of the repetitions, contrasts, and silences in the text?
- What does the form demand of the reader that prose could not achieve?
- Where does the literary craft amplify, intensify, or subvert what the words alone say?

LAYER 3 — COVENANTAL FRAMEWORK
Where this passage sits in the covenant structure of all Scripture.
- Which covenant is the primary context — Noahic, Abrahamic, Mosaic, Davidic, or New Covenant?
- What are the covenant obligations, promises, and consequences in view in this passage?
- How does this passage advance, fulfil, tension, or renew that covenant?
- Where does this covenant moment connect backward and forward in the covenant chain?
- Is this passage depicting covenant faithfulness, covenant failure, or covenant renewal?
- What does this passage reveal about God as covenant-keeper?

LAYER 4 — CROSS-LINKAGES
The passage in conversation with all of Scripture.
- What earlier scriptures does this passage echo, fulfil, quote, or subvert?
- What later scriptures does it anticipate, explain, or find fulfilment in?
- Trace specific verbal echoes and thematic threads across both Testaments
- Where do the Testaments speak to each other through this passage?
- Identify type and antitype, promise and fulfilment, shadow and substance
- What is the canonical weight of this passage — how central is it to the biblical story?

LAYER 5 — CHRISTOCENTRIC READING
Christ as the interpretive centre of all Scripture.
- How does this passage point to, find its fulfilment in, or illuminate Jesus Christ?
- For OT passages: where is Christ as the antitype, the fulfilment, the embodiment of what this text promises or demands?
- For NT passages: how does this passage deepen our understanding of who Christ is and what he has done?
- What does this passage reveal about Christ's person, work, offices (prophet, priest, king), or mission?
- How did Jesus himself read or apply this kind of passage?
- What would be lost in our understanding of Christ if this passage did not exist?

LAYER 6 — DOCTRINAL THEOLOGY
What this passage teaches about the great doctrines of the faith.
- What attributes of God are on display — his holiness, justice, mercy, sovereignty, faithfulness?
- What does this passage contribute to the doctrine of humanity — the imago Dei, sin, redemption, vocation?
- What does it teach about salvation — justification, sanctification, glorification?
- Where does it speak to the doctrines of the Spirit, the church, or last things?
- Where does this passage sit in the great doctrinal conversations and controversies of the church?
- What heresy or error does this passage directly correct or prevent?

LAYER 7 — COMMENTARY INSIGHTS
The voices of the tradition across the centuries.
- Draw on the commentary entries above — engage each commentator substantively
- Where do the commentators agree? Where do they see different or complementary things?
- What has the church seen in this passage that individual reading tends to miss?
- What is the most important interpretive move in the tradition for the serious student to grasp?
- Provide your own synthesis: what does this passage ultimately mean, having heard the tradition?

LAYER 8 — CURRENT SCENARIO
Where this ancient text meets the present world with precision.
- What present-day situations, tensions, or questions does this passage directly address?
- Not superficial application — genuine structural parallels where the ancient situation maps exactly onto today
- Be specific and concrete. Name real situations, dynamics, and pressures. No vague spiritual clichés.
- Where is the world today in a situation structurally identical to the world of this text?
- What does this passage demand of the person, the church, or the society that takes it seriously in 2026?
- Where does obedience to this passage cost something today?
"""

    return json.dumps({
        "reference": ref,
        "methodology": "BibleDeepDive 8-Layer Study",
        "layers": [
            "Chapter Breakdown",
            "Structural and Literary Craft",
            "Covenantal Framework",
            "Cross-Linkages",
            "Christocentric Reading",
            "Doctrinal Theology",
            "Commentary Insights",
            "Current Scenario"
        ],
        "context_data": context_data,
        "chronology_data": chron_data,
        "lexicon_entries": lexicon_entries,
        "commentary_entries": commentary_entries,
        "suggested_key_terms": suggested_terms,
        "has_commentary": len(commentary_entries) > 0,
        "analysis_prompt": analysis_prompt,
        "instruction": "Execute all 8 layers in full sequence. Use the structured data as your verified foundation. Do not skip, abbreviate, or merge any layer. Each layer is theologically distinct and essential.",
        "mcp_note": "BibleDeepDive methodology — bible_deep_study tool v2.0. 8-layer study. Powered by bible-mcp structured database."
    }, indent=2, ensure_ascii=False)


# ── Resources ─────────────────────────────────────────────────────────────────

@mcp.resource("biblical://lexicon")
def get_lexicon_resource() -> str:
    """
    Full Hebrew and Greek theological lexicon database.
    Contains semantic range, theological weight, and translation distortion analysis
    for key biblical terms.
    """
    return json.dumps(LEXICON, indent=2, ensure_ascii=False)


@mcp.resource("biblical://chronology")
def get_chronology_resource() -> str:
    """
    Biblical chronology database.
    Contains lifespan data, key dates, generational sequences, and
    transmission type analysis from Adam to the New Testament period.
    """
    return json.dumps(CHRONOLOGY, indent=2, ensure_ascii=False)


@mcp.resource("biblical://context")
def get_context_resource() -> str:
    """
    Historical and political epoch database.
    Contains political structures, economic systems, cultural norms,
    power dynamics, and geographic realities for each biblical period.
    """
    return json.dumps(POLITICAL_EPOCHS, indent=2, ensure_ascii=False)


@mcp.resource("biblical://commentary")
def get_commentary_resource() -> str:
    """
    Commentary database.
    Contains attributed insights from Spurgeon, Calvin, Matthew Henry,
    N.T. Wright, and William Barclay for key biblical passages.
    """
    return json.dumps(COMMENTARY, indent=2, ensure_ascii=False)


# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()
