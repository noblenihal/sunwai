"""Seed a living constituency: ~400 synthetic submissions pushed through the
REAL pipeline (Gemini structuring, clustering, embeddings), backdated over
6 weeks with scripted trend shapes.

Run inside the api container:
    python -m app.scripts.seed_demo            # adds to existing data
    python -m app.scripts.seed_demo --fresh    # wipes previous seed first

Seeded rows use channel='seed' so they can be wiped independently of real
WhatsApp/demo traffic. Trend shapes: 'flat', 'rising' (skewed to recent
2 weeks), 'spike' (70% in last 7 days), 'sparse' (few, scattered).
"""
import random
import sys
import time
from datetime import datetime, timedelta, timezone

from sqlalchemy import text

from ..db import SessionLocal
from ..services import ranking, structuring

DAYS = 42

# (ward alias used in message, category, count, shape, language mix override)
PLAN = [
    ("Govindpuri",            "drainage",    52, "rising", None),
    ("Govindpuri",            "electricity", 16, "flat",   None),
    ("Govindpuri gali 4",     "water",       18, "flat",   None),
    ("Sangam Vihar",          "water",       45, "spike",  None),
    ("Sangam Vihar",          "school",      22, "flat",   None),
    ("Sangam Vihar",          "road",        24, "flat",   None),
    ("Kalkaji",               "road",        28, "flat",   None),
    ("Tughlakabad Extension", "drainage",    24, "flat",   None),
    ("Khanpur",               "water",       32, "flat",   None),
    ("Deoli",                 "road",        20, "flat",   None),
    ("Deoli",                 "health",      14, "flat",   None),
    ("Tughlakabad",           "health",      18, "rising", None),
    ("Chittaranjan Park",     "electricity", 14, "flat",   "bn"),
    ("Sriniwaspuri",          "school",      12, "flat",   None),
    ("Badarpur",              "road",         5, "sparse", None),
    ("Madangir",              "water",        2, "sparse", None),
    ("Ambedkar Nagar",        "drainage",     3, "sparse", None),
    (None,                    "misc",        20, "flat",   None),  # unlocated
]

T = {
    "drainage": {
        "hi": ["{loc} में नाली जाम है, गंदा पानी सड़क पर बह रहा है",
               "{loc} की नालियां हफ्तों से साफ नहीं हुईं, मच्छर बढ़ गए हैं",
               "{loc} में सीवर ओवरफ्लो हो रहा है, बदबू से जीना मुश्किल है"],
        "rom": ["{loc} me naali jam hai, gandagi phail rahi hai",
                "{loc} ki nali ka pani ghar ke saamne bhar jata hai baarish me",
                "sewer overflow ho raha hai {loc} me, koi sunta nahi"],
        "en": ["The drain in {loc} is blocked and overflowing onto the street",
               "Open drain near {loc} market has not been cleaned for weeks"],
    },
    "water": {
        "hi": ["{loc} में पानी की भारी किल्लत है, टैंकर नहीं आ रहा",
               "{loc} में बोरवेल खराब है, महिलाएं दूर से पानी लाती हैं",
               "{loc} में नल में गंदा पानी आ रहा है"],
        "rom": ["{loc} me paani ki bahut kami hai, tanker hafte me ek baar aata hai",
                "borewell kharab hai {loc} me, do mahine ho gaye",
                "{loc} me paani ka pressure bilkul nahi hai subah"],
        "en": ["Severe water shortage in {loc}, tanker comes once a week",
               "Tap water in {loc} is muddy and smells bad"],
    },
    "road": {
        "hi": ["{loc} की सड़क पर बड़े गड्ढे हैं, रोज दुर्घटना का डर रहता है",
               "{loc} में सड़क टूटी पड़ी है, बारिश में चलना मुश्किल है"],
        "rom": ["{loc} ki road pe gadde hi gadde hain, scooter girte hain log",
                "{loc} me road banni chahiye, mitti ka rasta hai abhi"],
        "en": ["Huge potholes on the {loc} main road, two-wheelers keep falling",
               "The lane in {loc} was dug up months ago and never repaired"],
    },
    "electricity": {
        "hi": ["{loc} में स्ट्रीट लाइट बंद है, रात में अंधेरा रहता है",
               "{loc} में बिजली बार-बार जाती है, ट्रांसफार्मर पुराना है"],
        "rom": ["{loc} me street light kharab hai kai hafte se, raat me dar lagta hai",
                "bijli ka khamba jhuk gaya hai {loc} me, girne wala hai"],
        "en": ["Street lights in {loc} block are dead for weeks, unsafe at night"],
        "bn": ["{loc} এ রাস্তার আলো অনেকদিন ধরে খারাপ, রাতে খুব অন্ধকার থাকে",
               "{loc} এলাকায় বারবার লোডশেডিং হচ্ছে, ট্রান্সফরমার পুরনো"],
    },
    "school": {
        "hi": ["{loc} के सरकारी स्कूल की छत टपकती है, बच्चे परेशान हैं",
               "{loc} के स्कूल में शिक्षक कम हैं, कक्षाएं खाली रहती हैं"],
        "rom": ["{loc} ke school me toilet ki halat bahut kharab hai",
                "{loc} ke sarkari school me benches tooti hain"],
        "en": ["The government school in {loc} needs urgent roof repair before monsoon"],
    },
    "health": {
        "hi": ["{loc} की डिस्पेंसरी में दवाइयां नहीं मिलतीं, डॉक्टर भी कम आते हैं",
               "{loc} में मोहल्ला क्लिनिक की बहुत जरूरत है, बुजुर्ग दूर नहीं जा पाते"],
        "rom": ["{loc} ki dispensary me hamesha lambi line hoti hai, dawai khatam rehti hai",
                "PHC {loc} me machine kharab padi hai mahino se"],
        "en": ["The dispensary near {loc} runs out of basic medicines every month"],
    },
    "misc": {
        "rom": ["hamari gali me safai nahi hoti kai hafte se",
                "park ki halat bahut kharab hai, jhoole toote hain",
                "yahan awara kutton ki bahut samasya hai, bachon ko katne ka dar"],
        "hi": ["हमारे मोहल्ले में कूड़ा नहीं उठता, ढेर लगा रहता है",
               "यहां पार्क में सफाई और रोशनी दोनों की जरूरत है"],
        "en": ["Garbage is not collected regularly in our lane"],
    },
}

LANG_MIX = [("rom", 0.40), ("hi", 0.32), ("en", 0.28)]


def _pick_lang(cat: str, override: str | None) -> str:
    if override and override in T[cat] and random.random() < 0.5:
        return override
    langs = [(l, w) for l, w in LANG_MIX if l in T[cat]]
    r, acc = random.random() * sum(w for _, w in langs), 0.0
    for lang, w in langs:
        acc += w
        if r <= acc:
            return lang
    return langs[0][0]


def _timestamp(shape: str, now: datetime) -> datetime:
    if shape == "rising":
        day = DAYS * (1 - random.random() ** 0.35)
    elif shape == "spike":
        day = DAYS - random.uniform(0, 7) if random.random() < 0.7 else random.uniform(0, DAYS)
    else:  # flat / sparse
        day = random.uniform(0, DAYS)
    ts = now - timedelta(days=DAYS - day)
    return ts - timedelta(minutes=random.uniform(0, 720))


def main(fresh: bool = False):
    db = SessionLocal()
    now = datetime.now(timezone.utc)

    if fresh:
        db.execute(text(
            "DELETE FROM demand_signals WHERE submission_id IN "
            "(SELECT id FROM submissions WHERE channel = 'seed')"))
        db.execute(text("DELETE FROM submissions WHERE channel = 'seed'"))
        db.execute(text("DELETE FROM demands WHERE id NOT IN "
                        "(SELECT DISTINCT demand_id FROM demand_signals "
                        " WHERE demand_id IS NOT NULL)"))
        db.commit()
        print("[seed] previous seed wiped", flush=True)

    jobs = []
    for loc, cat, count, shape, lang_override in PLAN:
        for _ in range(count):
            jobs.append((loc, cat, shape, lang_override))
    random.shuffle(jobs)

    total, ok, failed = len(jobs), 0, 0
    for i, (loc, cat, shape, lang_override) in enumerate(jobs, 1):
        lang = _pick_lang(cat, lang_override)
        template = random.choice(T[cat][lang])
        msg = template.format(loc=loc) if loc else template
        ts = _timestamp(shape, now)
        try:
            sub_id = db.execute(
                text("INSERT INTO submissions (channel, kind, raw_text) "
                     "VALUES ('seed', 'text', :t) RETURNING id"),
                {"t": msg},
            ).scalar_one()
            db.commit()
            result = structuring.process_submission(db, sub_id)
            db.execute(text("UPDATE submissions SET received_at = :ts WHERE id = :id"),
                       {"ts": ts, "id": sub_id})
            if not result.get("rejected"):
                db.execute(
                    text("UPDATE demand_signals SET created_at = :ts "
                         "WHERE submission_id = :id"),
                    {"ts": ts, "id": sub_id},
                )
            db.commit()
            ok += 1
        except Exception as exc:
            db.rollback()
            failed += 1
            print(f"[seed] {i}/{total} FAILED: {exc.__class__.__name__}: {str(exc)[:120]}", flush=True)
            time.sleep(2)
        if i % 25 == 0:
            print(f"[seed] {i}/{total} done ({failed} failed)", flush=True)

    print("[seed] reranking...", flush=True)
    ranking.rerank_all(db)
    db.close()
    print(f"[seed] DONE: {ok} seeded, {failed} failed of {total}", flush=True)


if __name__ == "__main__":
    main(fresh="--fresh" in sys.argv)
