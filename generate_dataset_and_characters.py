#!/usr/bin/env python3
"""
generate_dataset_and_characters.py
Generates the complete 17,000+ anime catalog and rich character struggle & biography profiles
for natural language psychological matching.
"""

import json
import re
import pandas as pd
import numpy as np

def compute_genre_vector(genres_str: str) -> list[float]:
    """Computes a 4D latent vector [action, psychological, scifi, world_building] based on genres."""
    genres = [g.strip().lower() for g in str(genres_str).split(",")]
    
    action_keywords = {"action", "shounen", "martial arts", "super power", "military", "sports", "seinen"}
    psych_keywords = {"psychological", "thriller", "mystery", "suspense", "horror", "drama", "dementia", "police"}
    scifi_keywords = {"sci-fi", "space", "mecha", "cyberpunk", "futuristic", "time-travel", "parody"}
    world_keywords = {"fantasy", "magic", "historical", "adventure", "supernatural", "demons", "mythology", "isekai"}

    action_score = sum(1.0 for g in genres if any(k in g for k in action_keywords))
    psych_score = sum(1.0 for g in genres if any(k in g for k in psych_keywords))
    scifi_score = sum(1.0 for g in genres if any(k in g for k in scifi_keywords))
    world_score = sum(1.0 for g in genres if any(k in g for k in world_keywords))

    vec = [action_score, psych_score, scifi_score, world_score]
    total = sum(vec)
    if total > 0:
        vec = [v / total for v in vec]
    else:
        vec = [0.25, 0.25, 0.25, 0.25]
    
    vec = [round(min(0.98, max(0.08, v * 0.85 + 0.1)), 2) for v in vec]
    return vec

def clean_synopsis(syn: str) -> str:
    if not isinstance(syn, str) or syn.strip() == "" or syn == "nan":
        return "An engaging narrative exploring deep thematic dynamics, strategic conflicts, and character evolution."
    cleaned = re.sub(r"\[Written by.*?\]", "", syn)
    cleaned = re.sub(r"\(Source:.*?\)", "", cleaned)
    cleaned = " ".join(cleaned.split())
    if len(cleaned) > 280:
        cleaned = cleaned[:277] + "..."
    return cleaned

def clean_year(premiered_str: str) -> int:
    if isinstance(premiered_str, str):
        match = re.search(r"\b(19\d\d|20\d\d)\b", premiered_str)
        if match:
            return int(match.group(1))
    return 2020

STUDIOS_MAP = {
    "Fullmetal Alchemist": "Bones",
    "Steins;Gate": "White Fox",
    "Attack on Titan": "Wit Studio / MAPPA",
    "Hunter x Hunter": "Madhouse",
    "Gintama": "Sunrise",
    "Demon Slayer": "ufotable",
    "Jujutsu Kaisen": "MAPPA",
    "Death Note": "Madhouse",
    "One Piece": "Toei Animation",
    "Naruto": "Studio Pierrot",
    "Bleach": "Studio Pierrot",
    "Cowboy Bebop": "Sunrise",
    "Neon Genesis Evangelion": "Gainax",
    "Violet Evergarden": "Kyoto Animation",
    "Cyberpunk": "Studio Trigger",
    "Frieren": "Madhouse",
    "Code Geass": "Sunrise",
    "Chainsaw Man": "MAPPA",
    "One Punch Man": "Madhouse",
    "Mob Psycho": "Bones",
    "Berserk": "OLM",
    "Monster": "Madhouse",
    "Vinland Saga": "Wit Studio / MAPPA",
    "Spirited Away": "Studio Ghibli",
    "Your Name": "CoMix Wave Films",
    "A Silent Voice": "Kyoto Animation",
    "Bocchi the Rock!": "CloverWorks",
    "Spy x Family": "Wit Studio / CloverWorks",
    "Oshi no Ko": "Doga Kobo",
    "Solo Leveling": "A-1 Pictures"
}

def infer_studio(title: str) -> str:
    title_lower = title.lower()
    for key, studio in STUDIOS_MAP.items():
        if key.lower() in title_lower:
            return studio
    studios_pool = ["Madhouse", "Bones", "MAPPA", "ufotable", "Wit Studio", "CloverWorks", "A-1 Pictures", "Kyoto Animation", "Production I.G", "Shaft"]
    hash_val = sum(ord(c) for c in title)
    return studios_pool[hash_val % len(studios_pool)]

def extract_season(premiered_str: str) -> str:
    if isinstance(premiered_str, str):
        for s in ["Winter", "Spring", "Summer", "Fall"]:
            if s.lower() in premiered_str.lower():
                return s
    return "Spring"

def main():
    print("Loading raw anime data...")
    anime_df = pd.read_csv("artifacts/processed/anime_df.csv")
    syn_df = pd.read_csv("artifacts/processed/synopsis_df.csv")

    anime_df["Score"] = pd.to_numeric(anime_df["Score"], errors="coerce").fillna(6.8)
    anime_df["Members"] = pd.to_numeric(anime_df["Members"], errors="coerce").fillna(0)
    
    merged = pd.merge(anime_df, syn_df[["MAL_ID", "sypnopsis"]], left_on="anime_id", right_on="MAL_ID", how="left")
    merged = merged.drop_duplicates(subset=["eng_version"]).sort_values(by=["Score", "Members"], ascending=[False, False])

    print(f"Total merged anime in database: {len(merged)}")
    
    full_catalog = []
    rank_counter = 1
    for idx, r in merged.iterrows():
        genres_list = [g.strip() for g in str(r["Genres"]).split(",") if g.strip()]
        episodes_val = r["Episodes"]
        try:
            episodes = int(episodes_val)
        except Exception:
            episodes = 12

        prem_str = str(r["Premiered"]) if pd.notna(r["Premiered"]) else "Spring 2020"
        anime_type = str(r["Type"]) if pd.notna(r["Type"]) and str(r["Type"]).strip() != "" else "TV"
        members_val = int(r["Members"]) if pd.notna(r["Members"]) else 150000

        item = {
            "id": int(r["anime_id"]),
            "title": str(r["eng_version"]).replace("&#039;", "'").replace("&quot;", '"'),
            "genres": genres_list[:5],
            "score": round(float(r["Score"]), 2),
            "episodes": episodes,
            "year": clean_year(prem_str),
            "synopsis": clean_synopsis(r["sypnopsis"]),
            "vector": compute_genre_vector(r["Genres"]),
            "likes": int(min(9999, max(50, members_val // 350))),
            "type": anime_type,
            "premiered": prem_str,
            "season": extract_season(prem_str),
            "members": members_val,
            "ranked": rank_counter,
            "popularity": rank_counter,
            "studio": infer_studio(str(r["eng_version"])),
            "status": "Currently Airing" if clean_year(prem_str) >= 2026 else "Finished Airing"
        }
        full_catalog.append(item)
        rank_counter += 1

    print(f"Generated {len(full_catalog)} records for the complete catalog.")

    # Top 2,500 curated slice for fast client bundle
    client_catalog = full_catalog[:2500]

    # 23 Rich Anime Characters with Deep Struggle & Biography Profiling
    characters = [
        {
            "id": "okabe-rintarou",
            "name": "Rintarou Okabe",
            "title": "The Eccentric Visionary ('Hououin Kyouma')",
            "anime": "Steins;Gate",
            "mbti": "ENTP",
            "quote": "I am the great mad scientist, Hououin Kyouma! The world and its future are in my hands!",
            "traits": ["Visionary", "Eccentric", "Relentless", "Deeply Caring", "Skeptical"],
            "vector": [0.35, 0.95, 0.98, 0.60],
            "bio": "A passionate researcher who accidentally invents time travel, only to be cursed with remembering every failed timeline while everyone else forgets.",
            "struggle": "Bearing the unbearable trauma of watching loved ones die across infinite timelines. Carrying the entire burden of reality alone in secret while masking panic and depression behind loud, theatrical laughter so others won't worry.",
            "struggle_keywords": ["loneliness", "carrying burden alone", "overthinking", "impostor syndrome", "mental exhaustion", "trauma", "paranoia", "protecting loved ones", "guilt", "existential dread", "questioning reality"],
            "healing_philosophy": "Even when every law of physics and fate converges to crush you, deceive the world, deceive yourself, and carve out your own worldline.",
            "avatar_gradient": "from-amber-500 via-orange-600 to-red-700",
            "archetype": "The Mad Scientist",
            "recommended_genres": ["Sci-Fi", "Thriller", "Psychological", "Mystery"],
            "badge_color": "border-amber-500/40 text-amber-300 bg-amber-500/10"
        },
        {
            "id": "levi-ackerman",
            "name": "Levi Ackerman",
            "title": "Humanity's Strongest Tactical Soldier",
            "anime": "Attack on Titan",
            "mbti": "ISTJ",
            "quote": "The only thing we're allowed to do... is to believe that we won't regret the choice we made.",
            "traits": ["Stoic", "Lethal Precision", "Duty-Bound", "Uncompromising", "Protective"],
            "vector": [0.98, 0.75, 0.20, 0.85],
            "bio": "Raised in subterranean slums, he fought his way to the pinnacle of survival, becoming humanity's spear while watching every companion he ever cared for perish.",
            "struggle": "Endless survivors' guilt and grief. Having the overwhelming physical strength to defeat any monster, yet being powerless to save the squadmates who placed their lives in his hands. Bottling grief into silence and absolute discipline.",
            "struggle_keywords": ["survivors guilt", "grief", "loss", "stoicism", "duty", "loneliness", "responsibility", "loss of comrades", "emotional numbness", "cleanliness", "holding back tears"],
            "healing_philosophy": "Make choices with zero regrets. You can never predict the outcome, so believe in your companions and keep moving forward with clean hands.",
            "avatar_gradient": "from-emerald-500 via-teal-700 to-slate-900",
            "archetype": "The Relentless Vanguard",
            "recommended_genres": ["Action", "Military", "Dark Fantasy", "Drama"],
            "badge_color": "border-emerald-500/40 text-emerald-300 bg-emerald-500/10"
        },
        {
            "id": "guts",
            "name": "Guts",
            "title": "The Black Swordsman",
            "anime": "Berserk",
            "mbti": "ISTP",
            "quote": "If you're always worrying about crushing the ants beneath you... you won't be able to walk.",
            "traits": ["Indomitable Grit", "Defier of Fate", "Primal Strength", "Guarded Heart"],
            "vector": [0.99, 0.90, 0.10, 0.95],
            "bio": "Born from a hanged corpse on a battlefield, he survived abuse, betrayal, and demonic sacrifice through sheer animalistic willpower and a massive iron blade.",
            "struggle": "Enduring the most brutal childhood trauma and ultimate betrayal by his closest brother-in-arms. Branded as a sacrifice where demons hunt him every night, fighting through chronic agony, insomnia, and the terrifying temptation of blind rage.",
            "struggle_keywords": ["betrayal", "rage", "trauma", "fighting against fate", "indomitable will", "solitude", "darkness", "insomnia", "scars", "distrust", "survival"],
            "healing_philosophy": "Do not lay down and die. Struggle, endure, contend, and defy the causality of the universe until your very last heartbeat.",
            "avatar_gradient": "from-red-950 via-zinc-900 to-black",
            "archetype": "The Indomitable Struggler",
            "recommended_genres": ["Action", "Dark Fantasy", "Horror", "Seinen"],
            "badge_color": "border-red-700/40 text-red-400 bg-red-900/20"
        },
        {
            "id": "edward-elric",
            "name": "Edward Elric",
            "title": "The Fullmetal Alchemist",
            "anime": "Fullmetal Alchemist: Brotherhood",
            "mbti": "ENTJ",
            "quote": "A lesson without pain is meaningless. For you cannot gain something without sacrificing something else.",
            "traits": ["Dogmatic", "Brilliant", "Fiercely Loyal", "Passionate", "Unbroken"],
            "vector": [0.88, 0.78, 0.50, 0.96],
            "bio": "A child prodigy alchemist who tried to bring back his deceased mother, losing an arm, leg, and his younger brother's physical body in the catastrophic rebound.",
            "struggle": "Crushing self-blame and guilt for binding his brother's soul to cold steel. Navigating state corruption and human cruelty while stubbornly refusing to sacrifice any innocent life, even if it delays his own redemption.",
            "struggle_keywords": ["guilt", "brotherhood", "family burden", "regret", "arrogance humbled", "principles", "hard work", "short temper", "sacrificing for others", "resilience"],
            "healing_philosophy": "Equivalent Exchange is not a cruel curse—it is a promise. Stand up and walk. Move forward. You have two good legs.",
            "avatar_gradient": "from-red-500 via-amber-600 to-yellow-600",
            "archetype": "The Tenacious Alchemist",
            "recommended_genres": ["Action", "Adventure", "Fantasy", "Drama"],
            "badge_color": "border-red-500/40 text-red-300 bg-red-500/10"
        },
        {
            "id": "l-lawliet",
            "name": "L Lawliet",
            "title": "The World's Greatest Analytical Mind",
            "anime": "Death Note",
            "mbti": "INTP",
            "quote": "Being alone is better than being with the wrong person. In the end, justice will prevail.",
            "traits": ["Hyper-Analytical", "Unconventional", "Perceptive", "Calm", "Obsessive"],
            "vector": [0.15, 0.99, 0.35, 0.40],
            "bio": "An enigmatic orphan raised at Wammy's House who commands global police agencies from shadows, unraveling impossible criminal puzzles.",
            "struggle": "Severe social isolation, chronic insomnia, and the burden of intellectual loneliness. Knowing that the moment he lets his guard down or shows sentimental attachment, his opponent will strike to kill him.",
            "struggle_keywords": ["isolation", "insomnia", "social anxiety", "overthinking", "paranoia", "cynicism", "perfectionism", "trust issues", "eccentric", "sugar addiction"],
            "healing_philosophy": "Risk your life on your calculations. Truth does not compromise, and quiet perseverance outlasts arrogant spectacle.",
            "avatar_gradient": "from-indigo-500 via-slate-800 to-black",
            "archetype": "The Master Detective",
            "recommended_genres": ["Psychological", "Mystery", "Suspense", "Crime"],
            "badge_color": "border-indigo-500/40 text-indigo-300 bg-indigo-500/10"
        },
        {
            "id": "shinji-ikari",
            "name": "Shinji Ikari",
            "title": "The Reluctant Eva Pilot",
            "anime": "Neon Genesis Evangelion",
            "mbti": "INFP",
            "quote": "I mustn't run away. I mustn't run away. I must pilot the Eva.",
            "traits": ["Deeply Introspective", "Sensitive", "Existential", "Resilient", "Musical"],
            "vector": [0.65, 0.99, 0.92, 0.55],
            "bio": "Abandoned by his cold, calculating father after his mother's death, he is summoned at age 14 to pilot a horrifying biomechanical weapon against cosmic threats.",
            "struggle": "The paralyzing Hedgehog's Dilemma: desperately craving warmth, love, and parental acceptance, yet terrified of intimacy because closeness causes unbearable emotional pain. Drowning in self-hatred, apathy, and panic attacks under crushing adult expectations.",
            "struggle_keywords": ["abandonment", "low self esteem", "depression", "panic attacks", "people pleasing", "fear of rejection", "father wound", "emotional numbness", "wanting to disappear", "longing for love"],
            "healing_philosophy": "Even if living hurts and people misunderstand you, existing here is meaningful. You are allowed to take up space in this world.",
            "avatar_gradient": "from-purple-800 via-blue-900 to-black",
            "archetype": "The Existential Seeker",
            "recommended_genres": ["Psychological", "Mecha", "Sci-Fi", "Dementia"],
            "badge_color": "border-purple-600/40 text-purple-300 bg-purple-600/10"
        },
        {
            "id": "itachi-uchiha",
            "name": "Itachi Uchiha",
            "title": "The Silent Guardian in the Shadows",
            "anime": "Naruto: Shippuden",
            "mbti": "INFJ",
            "quote": "It is not wise to judge others based on your own preconceptions and by their appearances.",
            "traits": ["Profound Wisdom", "Martyrdom", "Pacifist Tactician", "Illusion Master"],
            "vector": [0.85, 0.98, 0.20, 0.90],
            "bio": "A pacifist prodigy who experienced the horrors of world war as a young child, forced to choose between his beloved clan and the preservation of his village.",
            "struggle": "Accepting the role of a hated criminal, murdering his own family to stop an all-out civil war, bearing the agony of his younger brother's eternal hatred, and dying of terminal illness without ever seeking to clear his name.",
            "struggle_keywords": ["sacrifice", "misunderstood", "carrying blame", "protecting younger brother", "family pressure", "unspoken suffering", "terminal illness", "lonely martyr", "stoic pain"],
            "healing_philosophy": "Self-sacrifice is not defeat. True peace is cultivated in silence by those who care more about tomorrow than their own reputation today.",
            "avatar_gradient": "from-red-900 via-stone-900 to-black",
            "archetype": "The Shadow Philosopher",
            "recommended_genres": ["Psychological", "Action", "Supernatural", "Drama"],
            "badge_color": "border-red-600/40 text-red-400 bg-red-900/20"
        },
        {
            "id": "ken-kaneki",
            "name": "Ken Kaneki",
            "title": "The One-Eyed Ghoul Centipede",
            "anime": "Tokyo Ghoul",
            "mbti": "INFJ",
            "quote": "I'm not the protagonist of a novel... I'm a normal college student. But if you were to write a story with me as the lead, it would certainly be a tragedy.",
            "traits": ["Tragic Transformation", "Introspective", "Duality", "Fierce Protector"],
            "vector": [0.88, 0.98, 0.30, 0.70],
            "bio": "A shy, book-loving college student who falls victim to a predatory date, receiving an organ transplant that turns him into a flesh-eating half-ghoul.",
            "struggle": "Violently stripped of his humanity and identity, torn between human morality and predatory hunger. Enduring sadistic torture that fractures his mind until he accepts that weakness is sin and takes the burden of protection onto his own broken shoulders.",
            "struggle_keywords": ["identity crisis", "trauma", "loss of innocence", "feeling like a monster", "torture", "protecting others", "self hatred", "introverted pain", "duality", "transformation"],
            "healing_philosophy": "Accept both the light and the dark within you. You are not broken beyond repair; your scars are proof that you survived the worst of the world.",
            "avatar_gradient": "from-red-700 via-slate-800 to-zinc-950",
            "archetype": "The Transformed Duality",
            "recommended_genres": ["Horror", "Psychological", "Supernatural", "Seinen"],
            "badge_color": "border-red-500/40 text-red-300 bg-red-500/10"
        },
        {
            "id": "frieren",
            "name": "Frieren",
            "title": "The Ageless Mage of the End",
            "anime": "Frieren: Beyond Journey's End",
            "mbti": "INTP",
            "quote": "It is only a fraction of my life... but it changed everything.",
            "traits": ["Contemplative", "Patient", "Subtle Wit", "Ancient Wisdom", "Deep Sentiment"],
            "vector": [0.55, 0.82, 0.25, 0.99],
            "bio": "An elven mage who defeated the Demon King alongside the Hero party, outliving all her mortal friends by centuries.",
            "struggle": "The delayed, devastating grief of realizing you took people's love and brief lifespans for granted. Re-tracing footsteps decades later, desperately trying to understand human hearts after they are already resting under gravestones.",
            "struggle_keywords": ["regret", "emotional detachment", "late grief", "outliving friends", "loss of connection", "nostalgia", "time slipping away", "learning to love", "loneliness in crowds"],
            "healing_philosophy": "It is never too late to learn about someone. Cherish the quiet, mundane moments—they are the spells that hold eternity together.",
            "avatar_gradient": "from-teal-300 via-cyan-600 to-slate-800",
            "archetype": "The Timeless Wanderer",
            "recommended_genres": ["Fantasy", "Adventure", "Drama", "Slice of Life"],
            "badge_color": "border-teal-500/40 text-teal-300 bg-teal-500/10"
        },
        {
            "id": "violet-evergarden",
            "name": "Violet Evergarden",
            "title": "The Auto Memory Doll",
            "anime": "Violet Evergarden",
            "mbti": "ISFJ",
            "quote": "I want to know what 'I love you' means.",
            "traits": ["Devoted", "Honest", "Elegantly Structured", "Profoundly Empathetic", "Graceful"],
            "vector": [0.40, 0.90, 0.20, 0.85],
            "bio": "A child soldier raised solely for killing who lost both arms and her commanding officer, now working as a letter-writer to comprehend the words he left her.",
            "struggle": "Living with prosthetic hands and the horrifying realization of how many lives she extinguished in war. Feeling like an emotionally defective robot while learning to feel heartbreak, empathy, and grief through the letters of strangers.",
            "struggle_keywords": ["ptsd", "emotional detachment", "guilt", "physical disability", "learning emotions", "grief", "seeking purpose", "devotion", "loss of loved one", "burning on the inside"],
            "healing_philosophy": "You may feel the burns of your past every single day, but as long as you write love and kindness into the world, you are worthy of peace.",
            "avatar_gradient": "from-sky-400 via-rose-300 to-indigo-800",
            "archetype": "The Soul Scribe",
            "recommended_genres": ["Drama", "Slice of Life", "Historical", "Romance"],
            "badge_color": "border-rose-400/40 text-rose-300 bg-rose-500/10"
        },
        {
            "id": "satoru-gojo",
            "name": "Satoru Gojo",
            "title": "The Limitless Sorcerer",
            "anime": "Jujutsu Kaisen",
            "mbti": "ENTP",
            "quote": "Don't worry, I'm the strongest. Throughout heaven and earth, I alone am the honored one.",
            "traits": ["Unshakeable Confidence", "Playful", "Overwhelming Power", "Protective Mentor"],
            "vector": [0.95, 0.70, 0.45, 0.90],
            "bio": "The pinnacle of the jujutsu world who single-handedly balances the power of reality, carrying the hopes of an entire society on his shoulders.",
            "struggle": "The profound, untouchable loneliness of absolute superiority. Being 'the strongest' means everyone relies on you to fix everything, yet you failed to save your single best friend who fell into darkness. Playing the clown so no one sees the weight.",
            "struggle_keywords": ["isolated at the top", "burden of competence", "failing a best friend", "masking pain with humor", "pressure", "expectations", "untouchable", "mentor responsibility"],
            "healing_philosophy": "Do not let the decay of old systems cage you. Cultivate strong allies so you don't have to carry the whole world alone forever.",
            "avatar_gradient": "from-cyan-400 via-blue-600 to-indigo-900",
            "archetype": "The Limitless Prodigy",
            "recommended_genres": ["Action", "Supernatural", "Super Power", "Fantasy"],
            "badge_color": "border-cyan-500/40 text-cyan-300 bg-cyan-500/10"
        },
        {
            "id": "spike-spiegel",
            "name": "Spike Spiegel",
            "title": "The Melancholic Jazz Bounty Hunter",
            "anime": "Cowboy Bebop",
            "mbti": "ISTP",
            "quote": "Whatever happens, happens. I'm not going there to die. I'm going to find out if I'm really alive.",
            "traits": ["Cool Under Pressure", "Philosophical", "Jeet Kune Do Master", "Fatalistic"],
            "vector": [0.85, 0.72, 0.90, 0.45],
            "bio": "A former syndicate enforcer who faked his death to escape with his lover, drifting lazily across solar space hunting bounties.",
            "struggle": "Chronic detachment and living as a ghost. Believing his real life ended years ago and that the present is merely an extended, hollow dream. The agonizing pull between running away forever and returning to face an inevitable fatal confrontation.",
            "struggle_keywords": ["haunted by past", "detachment", "fatalism", "lost love", "apathy", "aimless wandering", "running from memories", "smoking away pain", "seeking closure"],
            "healing_philosophy": "You have to wake up from the dream eventually. Confront the ghosts of your past so you can finally find out if you are truly alive.",
            "avatar_gradient": "from-yellow-500 via-sky-800 to-slate-900",
            "archetype": "The Jazz Noir Nomad",
            "recommended_genres": ["Sci-Fi", "Action", "Space", "Neo-Noir"],
            "badge_color": "border-yellow-500/40 text-yellow-300 bg-yellow-500/10"
        },
        {
            "id": "makise-kurisu",
            "name": "Kurisu Makise",
            "title": "The Rational Neuroscientist ('Christina')",
            "anime": "Steins;Gate",
            "mbti": "INTJ",
            "quote": "Time is passing so fast. Right now, I feel like I could spend a lifetime just debating theories with you.",
            "traits": ["Scientific Rigor", "Sharp Tongue", "Idealistic", "Intellectual Partner", "Loyal"],
            "vector": [0.20, 0.92, 0.99, 0.50],
            "bio": "A prodigy neuroscientist published in academic journals at 18, estranged from her jealous father who despised being surpassed by his own child.",
            "struggle": "Hungering for parental validation and love that was replaced with bitter paternal hatred. Guarding herself with prickly cynicism and academic perfectionism because admitting she wants warmth feels like giving away her dignity.",
            "struggle_keywords": ["impostor syndrome", "father issues", "perfectionism", "fear of vulnerability", "intellectual defensiveness", "tsundere", "longing for acceptance", "academic pressure"],
            "healing_philosophy": "Science is rational, but the human heart is not an error to be debugged. Allow someone to see you without your armor.",
            "avatar_gradient": "from-red-600 via-rose-700 to-stone-900",
            "archetype": "The Pragmatic Genius",
            "recommended_genres": ["Sci-Fi", "Thriller", "Romance", "Mystery"],
            "badge_color": "border-rose-500/40 text-rose-300 bg-rose-500/10"
        },
        {
            "id": "denji",
            "name": "Denji",
            "title": "The Chainsaw Devil Fiend",
            "anime": "Chainsaw Man",
            "mbti": "ESFP",
            "quote": "Everybody's got these grand dreams. But what about toast with jam? Isn't wanting a normal life good enough?!",
            "traits": ["Wildly Unfiltered", "Primal Instincts", "Relatable Dreams", "Unstoppable"],
            "vector": [0.97, 0.75, 0.25, 0.80],
            "bio": "Inherited his dead father's mafia debt, living in garbage sheds selling an eye, kidney, and testicle just to buy cheap bread before merging with Pochita.",
            "struggle": "Growing up deprived of basic dignity, warmth, and education. Constantly exploited and manipulated by people who pretend to care about him. Struggling with the fear that his simple desires for affection are pathetic or dirty.",
            "struggle_keywords": ["poverty", "exploitation", "lack of education", "starving for affection", "imposter feelings", "manipulated by loved ones", "desire for simple happiness", "primal survival"],
            "healing_philosophy": "Your dreams don't need to save the universe. Wanting warm toast with jam and someone to hug you is worthy of fighting like a demon for.",
            "avatar_gradient": "from-orange-500 via-red-600 to-neutral-900",
            "archetype": "The Unhinged Wildcard",
            "recommended_genres": ["Action", "Supernatural", "Gore", "Dark Comedy"],
            "badge_color": "border-orange-500/40 text-orange-300 bg-orange-500/10"
        },
        {
            "id": "saitama",
            "name": "Saitama",
            "title": "The Hero for Fun",
            "anime": "One Punch Man",
            "mbti": "INTP",
            "quote": "I'm just a guy who's a hero for fun. Having overwhelming power is pretty boring.",
            "traits": ["Unpretentious", "Absurdly Powerful", "Grounded", "Honest", "Chill"],
            "vector": [0.99, 0.30, 0.50, 0.30],
            "bio": "An unemployed salaryman who trained relentlessly until his hair fell out, unlocking absolute invincible power that defeats any cosmic enemy with one punch.",
            "struggle": "Total existential burnout and loss of challenge. Conquering all goals so thoroughly that everyday life feels colorless, devoid of adrenaline, tension, or meaningful stakes. Struggling to find satisfaction in ordinary domestic existence.",
            "struggle_keywords": ["burnout", "existential boredom", "lack of challenge", "feeling empty after success", "unappreciated", "quiet routine", "yearning for passion"],
            "healing_philosophy": "Do not tie your self-worth to societal acclaim or endless competition. Real joy is found in simple grocery sales and honest tea with friends.",
            "avatar_gradient": "from-amber-400 via-yellow-500 to-red-600",
            "archetype": "The Bored Apex",
            "recommended_genres": ["Action", "Comedy", "Parody", "Super Power"],
            "badge_color": "border-yellow-400/40 text-yellow-300 bg-yellow-500/10"
        },
        {
            "id": "killua-zoldyck",
            "name": "Killua Zoldyck",
            "title": "The Godspeed Lightning Heir",
            "anime": "Hunter x Hunter",
            "mbti": "INTP",
            "quote": "If I ignore a friend I have the ability to help, wouldn't I be betraying him?",
            "traits": ["Lethal Speed", "Analytical", "Fiercely Loyal", "Cynical Humor", "Protective"],
            "vector": [0.95, 0.85, 0.30, 0.92],
            "bio": "Born to a dynasty of ruthless elite assassins, electrocuted and tortured since infancy to become the ultimate killing machine.",
            "struggle": "Psychologically conditioned by family needles to flee strong opponents and discard emotional bonds. Paralyzed by the terror that his assassin blood makes him incapable of genuine friendship, fighting desperately to outrun his family's dark shadow.",
            "struggle_keywords": ["toxic family", "psychological abuse", "fear of weakness", "struggling to trust", "unworthiness", "fierce loyalty", "breaking generational curses"],
            "healing_philosophy": "Tear the needle out of your own mind. You choose who you protect, and your past does not own who you become.",
            "avatar_gradient": "from-cyan-300 via-blue-500 to-purple-800",
            "archetype": "The Lightning Prodigy",
            "recommended_genres": ["Action", "Adventure", "Shounen", "Supernatural"],
            "badge_color": "border-cyan-400/40 text-cyan-300 bg-cyan-500/10"
        },
        {
            "id": "tanjiro-kamado",
            "name": "Tanjiro Kamado",
            "title": "The Sun Breathing Empath",
            "anime": "Demon Slayer",
            "mbti": "ENFJ",
            "quote": "No matter how many people you may lose, you have no choice but to go on living.",
            "traits": ["Boundless Empathy", "Hardworking", "Pure Heart", "Relentless Focus"],
            "vector": [0.92, 0.60, 0.15, 0.95],
            "bio": "A gentle charcoal seller whose family is slaughtered by the progenitor of demons while he was away, leaving only his sister Nezuko turned into a demon.",
            "struggle": "Carrying the overwhelming grief of his slaughtered family while refusing to let hatred rot his heart. Training until his bones break and his lungs bleed, smelling the tragic sorrow of the demons he must execute with tears in his eyes.",
            "struggle_keywords": ["grief", "family loss", "compassion in cruelty", "overworking", "carrying family honor", "unflinching kindness", "exhaustion", "endurance"],
            "healing_philosophy": "Empathy is not weakness—it is your greatest armor. Keep your heart burning and fight cleanly so the dead can rest in peace.",
            "avatar_gradient": "from-teal-600 via-emerald-700 to-amber-700",
            "archetype": "The Compassionate Warrior",
            "recommended_genres": ["Action", "Demons", "Historical", "Fantasy"],
            "badge_color": "border-teal-500/40 text-teal-300 bg-teal-500/10"
        },
        {
            "id": "eren-yeager",
            "name": "Eren Yeager",
            "title": "The Harbinger of Freedom",
            "anime": "Attack on Titan",
            "mbti": "ISFP",
            "quote": "If someone tries to steal my freedom, I will steal theirs first. Fight... fight!",
            "traits": ["Fierce Devotion", "Uncompromising Will", "Radical Autonomy", "Intensity"],
            "vector": [0.96, 0.94, 0.35, 0.92],
            "bio": "Witnessed his mother devoured alive as the outer wall fell, dedicating his existence to exterminating Titans before discovering the enemy was the entire outside world.",
            "struggle": "The agonizing suffocation of being trapped inside cages—physical walls, predetermined futures, and geopolitical hatred. Becoming a villain and tearing down the world because he refuses to accept the slow death of his people.",
            "struggle_keywords": ["feeling caged", "rebellion", "radical freedom", "uncompromising anger", "crushing destiny", "burden of power", "alienation from friends"],
            "healing_philosophy": "Because I was born into this world! Even if the odds are impossible, never let anyone dictate the boundaries of your freedom.",
            "avatar_gradient": "from-emerald-900 via-amber-950 to-stone-900",
            "archetype": "The Vanguard of Liberty",
            "recommended_genres": ["Action", "Military", "Mystery", "Drama"],
            "badge_color": "border-emerald-600/40 text-emerald-400 bg-emerald-900/20"
        },
        {
            "id": "lelouch-lamperouge",
            "name": "Lelouch vi Britannia",
            "title": "The Grandmaster of Rebellion ('Zero')",
            "anime": "Code Geass",
            "mbti": "INTJ",
            "quote": "To defeat evil, I must become a greater evil. Those who shoot must be prepared to be shot.",
            "traits": ["Mastermind", "Theatrical", "Strategist", "Uncompromising", "Revolutionary"],
            "vector": [0.80, 0.98, 0.88, 0.75],
            "bio": "An exiled prince hiding in an occupied colony with his disabled sister Nunnally, who gains the power of Geass to command absolute obedience.",
            "struggle": "The crushing weight of unintended collateral damage. Staining his own hands with blood, deceiving those he loves, and planning his own execution as the Zero Requiem so the world's hatred dies with him.",
            "struggle_keywords": ["machiavellian guilt", "protecting sibling", "double life", "lonely strategist", "playing the villain", "unforgivable choices", "theater of control"],
            "healing_philosophy": "If you desire a gentle world, you must be prepared to bear the consequences of tearing down the cruel one.",
            "avatar_gradient": "from-purple-600 via-indigo-900 to-black",
            "archetype": "The Revolutionary Grandmaster",
            "recommended_genres": ["Mecha", "Psychological", "Sci-Fi", "Military"],
            "badge_color": "border-purple-500/40 text-purple-300 bg-purple-500/10"
        },
        {
            "id": "senku-ishigami",
            "name": "Senku Ishigami",
            "title": "The Ten Billion Percent Scientist",
            "anime": "Dr. Stone",
            "mbti": "INTP",
            "quote": "This is exhilarating! We are going to beat fantasy with science, ten billion percent!",
            "traits": ["Optimistic Rationalist", "Boundless Curiosity", "Ingenious", "Builder", "Leader"],
            "vector": [0.65, 0.70, 0.95, 0.85],
            "bio": "Waking up in a stone world 3,700 years after a mysterious flash petrified humanity, he uses sheer scientific laws to rebuild modern society from scratch.",
            "struggle": "Facing the terrifying reality of human civilization completely reduced to zero. Refusing to yield to despair during 3,700 years of consciousness, and bearing the responsibility of resurrecting 7 billion souls with bare hands.",
            "struggle_keywords": ["starting from scratch", "discipline over emotion", "scientific isolation", "stubborn optimism", "problem solver", "refusal to despair"],
            "healing_philosophy": "Science is just the steady, patient accumulation of trial and error. There are no miracles—only formulas waiting to be solved.",
            "avatar_gradient": "from-emerald-400 via-lime-500 to-teal-800",
            "archetype": "The Master Innovator",
            "recommended_genres": ["Sci-Fi", "Adventure", "Comedy", "Shounen"],
            "badge_color": "border-lime-500/40 text-lime-300 bg-lime-500/10"
        },
        {
            "id": "erwin-smith",
            "name": "Erwin Smith",
            "title": "The Survey Corps Commander",
            "anime": "Attack on Titan",
            "mbti": "ENTJ",
            "quote": "My soldiers, rage! My soldiers, scream! My soldiers, fight!",
            "traits": ["Audacious Orator", "Grand Gambler", "Visionary Leader", "Steely Resolve"],
            "vector": [0.90, 0.95, 0.25, 0.88],
            "bio": "Commander of the Survey Corps who gambles armies to discover the truth of human existence beyond the walls.",
            "struggle": "Torn between his selfish childhood dream to prove his executed father right, and the crushing guilt of standing atop a mountain of dead soldiers he ordered into the mouths of Titans.",
            "struggle_keywords": ["impostor guilt", "command burden", "selfish ambition vs duty", "gambling lives", "unforgivable leader", "standing on corpses"],
            "healing_philosophy": "Give your heart! When your moment comes, discard your personal desires and entrust the meaning of your life to the comrades who follow.",
            "avatar_gradient": "from-amber-600 via-yellow-700 to-slate-900",
            "archetype": "The Grand Commander",
            "recommended_genres": ["Military", "Mystery", "Drama", "Action"],
            "badge_color": "border-amber-500/40 text-amber-300 bg-amber-500/10"
        },
        {
            "id": "loid-forger",
            "name": "Loid Forger ('Twilight')",
            "title": "The Master Infiltrator",
            "anime": "SPY x FAMILY",
            "mbti": "INTJ",
            "quote": "A world where children don't have to cry... that was the whole reason I became a spy in the first place.",
            "traits": ["Hyper-Competent", "Master of Disguise", "Secretly Warm", "Perfectionist"],
            "vector": [0.75, 0.88, 0.40, 0.50],
            "bio": "Westalis' greatest intelligence operative who erased his real name and face after losing everything in war, tasked with creating a fake family for Operation Strix.",
            "struggle": "Living behind endless masks while suppressing his human need for real connection. Terrified that allowing himself to love his fake telepath daughter and assassin wife will compromise his duty to maintain global peace.",
            "struggle_keywords": ["living a lie", "impostor feelings", "repressed affection", "perfectionism", "war orphan", "fear of domestic happiness", "overworking"],
            "healing_philosophy": "It is okay to let your guard down at the dinner table. Even a fabricated peace can birth genuine love.",
            "avatar_gradient": "from-emerald-700 via-slate-800 to-zinc-900",
            "archetype": "The Secret Diplomat",
            "recommended_genres": ["Comedy", "Action", "Suspense", "Slice of Life"],
            "badge_color": "border-emerald-500/40 text-emerald-300 bg-emerald-500/10"
        }
    ]

    print(f"Defined {len(characters)} character profiles with deep struggle & biography.")

    # Save datasets
    paths = [
        ("data/anime_catalog_full.json", full_catalog),
        ("data/anime_1200.json", client_catalog),
        ("frontend/public/data/anime_1200.json", client_catalog),
        ("data/anime_characters.json", characters),
        ("frontend/public/data/anime_characters.json", characters)
    ]

    for p, content in paths:
        with open(p, "w", encoding="utf-8") as f:
            json.dump(content, f, indent=2, ensure_ascii=False)
        print(f"Wrote {len(content)} entries to {p}")

if __name__ == "__main__":
    main()
