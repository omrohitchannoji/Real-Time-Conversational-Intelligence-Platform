import os
import csv
import random
from datetime import datetime, timedelta

REDDIT_RSS_CSV_PATH = os.path.join("datasets", "reddit_rss.csv")

# Authentic Cohesive Dialogue Threads across 10 Subreddits
CONVERSATION_THREADS = {
    "technology": [
        {
            "topic": "AI Hardware & GPUs",
            "messages": [
                ("tech_guru_99", "NVIDIA just announced their new Blackwell GPU architecture for LLM training clusters."),
                ("hardware_dev", "The 8TB/s memory bandwidth is insane compared to the H100!"),
                ("cloud_architect", "True, but the power consumption per node is going to be massive at 1200W."),
                ("tech_guru_99", "Agreed, cloud providers will need liquid cooling for these new server racks."),
                ("sys_admin", "Does AWS or Azure have preview instances available yet?")
            ]
        },
        {
            "topic": "Python Free-Threading",
            "messages": [
                ("pythonista", "Python 3.13 introduces experimental free-threading without the GIL!"),
                ("data_coder", "Finally! This means true multi-core CPU parallelism for Python scripts."),
                ("backend_dev", "Will C-extensions like NumPy and Pandas work without modifications?"),
                ("pythonista", "Most major libraries are actively adding support for the no-GIL build right now.")
            ]
        },
        {
            "topic": "Cybersecurity Zero-Day",
            "messages": [
                ("security_pro", "Cybersecurity researchers discovered a critical zero-day vulnerability in Linux kernel network drivers."),
                ("sys_admin", "Is there a patch available on Ubuntu and Debian security repositories?"),
                ("security_pro", "Yes, kernel update 6.8.12 resolves the buffer overflow issue. Patch immediately!")
            ]
        }
    ],
    "science": [
        {
            "topic": "Gene Editing",
            "messages": [
                ("gene_scientist", "CRISPR gene editing therapy has received landmark FDA approval for sickle cell disease treatment."),
                ("bio_student", "This is huge! Is it a one-time treatment for patients?"),
                ("gene_scientist", "Yes, bone marrow stem cells are extracted, edited in the lab, and re-infused.")
            ]
        },
        {
            "topic": "James Webb Space Telescope",
            "messages": [
                ("astro_researcher", "James Webb Space Telescope observed water vapor in a terrestrial planet-forming disk!"),
                ("space_fan", "That means the building blocks for oceans might exist in early star systems!"),
                ("astro_researcher", "Exactly, it suggests rocky planets could form with water already present.")
            ]
        }
    ],
    "AskReddit": [
        {
            "topic": "Career Advice",
            "messages": [
                ("curious_user", "What is the best career advice you've ever received from a mentor?"),
                ("career_coach", "Never stay in a job where you are neither earning nor learning."),
                ("wise_senior", "Always document your wins weekly—it makes performance reviews and resume updates trivial.")
            ]
        },
        {
            "topic": "Life Productivity Habits",
            "messages": [
                ("productivity_geek", "What small daily habit completely transformed your productivity?"),
                ("early_riser", "Writing down my top 3 non-negotiable tasks the night before."),
                ("focus_master", "Turning off all phone notifications except phone calls during deep work hours.")
            ]
        }
    ],
    "sports": [
        {
            "topic": "Champions League Final",
            "messages": [
                ("football_fanatic", "The UEFA Champions League final delivered an absolute tactical masterclass!"),
                ("tactics_guru", "The high-pressing defense completely suffocated their counter-attacks in the second half."),
                ("stadium_goer", "That winning goal in the 88th minute had the entire stadium roaring!")
            ]
        },
        {
            "topic": "Formula 1 Regulations",
            "messages": [
                ("f1_analyst", "Formula 1 new engine regulations promise closer wheel-to-wheel racing next season."),
                ("race_fan", "Will active aerodynamics actually help secondary teams overtake on straights?"),
                ("f1_analyst", "Simulations show reduced dirty air turbulence behind leading cars, so yes!")
            ]
        }
    ],
    "gaming": [
        {
            "topic": "Unreal Engine 5.4",
            "messages": [
                ("game_dev", "Unreal Engine 5.4 features massive Nanite performance boosts for open-world games!"),
                ("indie_creator", "Does it reduce shader compilation stuttering on PC hardware?"),
                ("game_dev", "Yes, background PSO pre-compilation has been completely overhauled.")
            ]
        },
        {
            "topic": "GTA VI Expectations",
            "messages": [
                ("gamer_alex", "Grand Theft Auto VI trailer hit 200 million views on YouTube!"),
                ("console_gamer", "The NPC density in Vice City looks next-level compared to GTA V."),
                ("pixel_hero", "I just hope the PC port doesn't get delayed too long after the console launch.")
            ]
        }
    ],
    "space": [
        {
            "topic": "Artemis Moon Landing",
            "messages": [
                ("lunar_observer", "NASA Artemis III mission targets human landing near the lunar South Pole."),
                ("space_engineer", "Permanently shadowed craters at the South Pole contain water ice reserves."),
                ("lunar_observer", "That water will be crucial for rocket propellant production on future Mars missions!")
            ]
        }
    ],
    "movies": [
        {
            "topic": "Oppenheimer & Oscars",
            "messages": [
                ("film_buff", "Christopher Nolan's Oppenheimer won 7 Academy Awards including Best Picture!"),
                ("cinema_lover", "The sound design in the Trinity test scene gave me chills in the IMAX theater."),
                ("film_buff", "Ludwig Göransson's musical score held the entire 3-hour runtime together beautifully.")
            ]
        }
    ],
    "news": [
        {
            "topic": "Infrastructure Investment",
            "messages": [
                ("policy_observer", "New infrastructure bill allocates funds for high-speed rail network expansion."),
                ("urban_planner", "Connecting major metropolitan corridors will reduce regional highway traffic significantly."),
                ("transit_advocate", "Electric high-speed trains are also far cleaner than short-haul domestic flights.")
            ]
        }
    ],
    "worldnews": [
        {
            "topic": "EU AI Act",
            "messages": [
                ("eu_watcher", "European Union parliament voted on the comprehensive Artificial Intelligence Regulation Act."),
                ("legal_tech", "High-risk AI models will now require strict transparency and risk assessment audits."),
                ("eu_watcher", "It sets a global benchmark similar to how GDPR reshaped data privacy worldwide.")
            ]
        }
    ],
    "geopolitics": [
        {
            "topic": "Semiconductor Supply Chains",
            "messages": [
                ("geopol_analyst", "Semiconductor supply chain sovereignty has become a central focus of national industrial policy."),
                ("macro_econ", "Building domestic fabrication plants takes 3-5 years, but it secures critical tech supply."),
                ("geopol_analyst", "Indeed, chip manufacturing relies on complex global lithography equipment dependencies.")
            ]
        }
    ]
}


def generate_cohesive_conversation_dataset(target_count: int = 12000):
    """
    Generates 12,000 authentic, cohesive multi-person conversation thread records.
    Saves ONLY to datasets/reddit_rss.csv for user review.
    Does NOT touch any database.
    """
    print("=" * 60)
    print(f"[START] Generating {target_count:,} Cohesive Multi-Person Dialogue Records")
    print(f"[OUTPUT FILE] '{REDDIT_RSS_CSV_PATH}'")
    print("=" * 60)

    subreddits = list(CONVERSATION_THREADS.keys())
    records = []
    fieldnames = ["comment_id", "parent_id", "author", "created_utc", "message", "subreddit"]

    base_time = datetime(2026, 1, 1, 10, 0, 0)
    comment_id_counter = 10000

    while len(records) < target_count:
        for sub in subreddits:
            threads = CONVERSATION_THREADS[sub]
            thread = random.choice(threads)
            thread_messages = thread["messages"]

            # Thread root comment
            comment_id_counter += 1
            root_id = f"c_{comment_id_counter}"
            root_author, root_text = thread_messages[0]
            
            base_time += timedelta(minutes=random.randint(1, 5))
            
            records.append({
                "comment_id": root_id,
                "parent_id": "t3_none",  # Top-level post
                "author": root_author,
                "created_utc": base_time.strftime("%Y-%m-%d %H:%M:%S"),
                "message": root_text,
                "subreddit": sub
            })

            # Subsequent replies in this thread (pointing to previous messages)
            previous_comment_id = root_id
            for msg_idx in range(1, len(thread_messages)):
                if len(records) >= target_count:
                    break

                comment_id_counter += 1
                reply_id = f"c_{comment_id_counter}"
                reply_author, reply_text = thread_messages[msg_idx]

                base_time += timedelta(seconds=random.randint(30, 180))

                records.append({
                    "comment_id": reply_id,
                    "parent_id": previous_comment_id,  # Direct parent ID link!
                    "author": reply_author,
                    "created_utc": base_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "message": reply_text,
                    "subreddit": sub
                })

                # 50% chance next reply targets this reply, 50% targets root
                if random.random() > 0.5:
                    previous_comment_id = reply_id

            if len(records) >= target_count:
                break

    os.makedirs("datasets", exist_ok=True)
    
    try:
        with open(REDDIT_RSS_CSV_PATH, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(records)
        print(f"\n[SUCCESS] Generated {len(records):,} cohesive conversation records saved to '{REDDIT_RSS_CSV_PATH}'!")
        print("[NOTE] Zero data was written to any database. You can now open and inspect 'datasets/reddit_rss.csv'!")
        return True
    except PermissionError:
        print(f"\n[ERROR] Could not write to '{REDDIT_RSS_CSV_PATH}' because Excel has the file open!")
        print("[ACTION REQUIRED] Please close 'datasets/reddit_rss.csv' in Excel so Python can write the updated cohesive threads!")
        return False
    except Exception as e:
        print(f"[ERROR] Failed to save CSV file: {e}")
        return False


if __name__ == "__main__":
    generate_cohesive_conversation_dataset(target_count=12000)
