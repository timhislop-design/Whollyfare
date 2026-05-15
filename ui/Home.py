"""
Home.py — WhollyFare Dashboard + Landing Page
Run with:  streamlit run ui/Home.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st
import ui.state as state
import ui.style as style

st.set_page_config(
    page_title="WhollyFare — Smart Grocery Planning",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

state.init()

# ── Sidebar brand mark ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <style>
      /* Hide Streamlit's auto-generated page nav so our custom nav is the only one */
      [data-testid="stSidebarNav"] { display: none !important; }
    </style>

    <!-- Leaf mark — sits above Home / all nav items -->
    <div style='padding: 18px 0 6px 4px;'>
      <svg width="52" height="52" viewBox="0 0 52 52" xmlns="http://www.w3.org/2000/svg">
        <!-- Fork handle -->
        <line x1="14" y1="46" x2="14" y2="10" stroke="#9FD9A8" stroke-width="2.8" stroke-linecap="round"/>
        <!-- Fork tines -->
        <line x1="9"  y1="10" x2="9"  y2="24" stroke="#9FD9A8" stroke-width="2"   stroke-linecap="round"/>
        <line x1="14" y1="10" x2="14" y2="24" stroke="#9FD9A8" stroke-width="2"   stroke-linecap="round"/>
        <line x1="19" y1="10" x2="19" y2="24" stroke="#9FD9A8" stroke-width="2"   stroke-linecap="round"/>
        <!-- Leaf body -->
        <ellipse cx="36" cy="26" rx="13" ry="8.5" fill="#5DAA6A" transform="rotate(-28 36 26)"/>
        <!-- Leaf midrib -->
        <line x1="24" y1="35" x2="46" y2="18" stroke="#9FD9A8" stroke-width="1.3" stroke-linecap="round"/>
      </svg>
    </div>
    <!-- Wordmark under the leaf -->
    <div style='font-size:15px;font-weight:700;color:white;letter-spacing:0.02em;
                padding:0 0 4px 4px;'>WhollyFare</div>
    <div style='font-size:10px;color:#9FD9A8;padding:0 0 18px 4px;'>Eat well. Spend less.</div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("<div style='color:#9FD9A8;font-size:11px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:8px;'>Get started</div>", unsafe_allow_html=True)
    st.page_link("pages/1_Household.py",    label="👨‍👩‍👧 Household Setup",   help="Set up your family profile, allergies, and budget")
    st.page_link("pages/2_Grocer_Hub.py",   label="🏪 Grocer Hub",           help="Connect your stores and load weekly prices")

    st.markdown("<div style='color:#9FD9A8;font-size:11px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;margin-top:14px;margin-bottom:8px;'>Weekly plan</div>", unsafe_allow_html=True)
    st.page_link("pages/3_Plan.py",         label="🍽️ This Week's Plan",     help="View your generated meal plan and ingredient picks")
    st.page_link("pages/4_Sunday_BuyOff.py",label="✅ Sunday Buy-Off",        help="Review, approve, and send your shopping list")
    st.page_link("pages/5_Shopping_List.py",label="🛒 Shopping List",         help="Your organised list by store and category")

    st.markdown("<div style='color:#9FD9A8;font-size:11px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;margin-top:14px;margin-bottom:8px;'>History & info</div>", unsafe_allow_html=True)
    st.page_link("pages/6_Ledger.py",       label="💰 Found Money Ledger",    help="Your running savings record week over week")
    st.page_link("pages/7_Investor.py",     label="📈 Investor Brief",        help="Who we are, why we matter, the opportunity")

style.inject()

household   = st.session_state.get("household")
approved    = state.week_approved()
plan        = st.session_state.get("plan")
grocers     = st.session_state.get("grocers", [])
loaded      = state.stores_loaded_this_week()
history     = st.session_state.get("ledger_history", [])
total_saved = sum(e.get("found_money", 0) for e in history)

# ════════════════════════════════════════════════════════════════════════════════
# LANDING VIEW — new visitors who haven't set up yet
# ════════════════════════════════════════════════════════════════════════════════
if not state.is_setup_complete():

    # ── CSS + page treatment ──────────────────────────────────────────────────
    st.markdown("""
    <style>
      .block-container { padding-top: 0.5rem !important; }

      [data-testid="stAppViewContainer"] > .main {
        background:
          radial-gradient(ellipse at 12% 6%,  rgba(93,170,106,0.12) 0%, transparent 48%),
          radial-gradient(ellipse at 88% 4%,  rgba(30,92,50,0.08)  0%, transparent 42%),
          radial-gradient(ellipse at 50% 90%, rgba(93,170,106,0.08) 0%, transparent 50%),
          radial-gradient(ellipse at 92% 65%, rgba(242,139,48,0.06) 0%, transparent 38%),
          #FAFAF7;
      }

      [data-testid="stSidebarNav"] { display: none !important; }

      /* Smooth lift on hover for any wf-card class */
      .wf-card {
        transition: transform 0.18s ease, box-shadow 0.18s ease !important;
      }
      .wf-card:hover {
        transform: translateY(-5px) !important;
        box-shadow: 0 16px 48px rgba(30,92,50,0.16) !important;
      }

      /* Tier detail expand panel */
      .wf-detail {
        animation: slideDown 0.22s ease;
      }
      @keyframes slideDown {
        from { opacity: 0; transform: translateY(-8px); }
        to   { opacity: 1; transform: translateY(0); }
      }
    </style>
    """, unsafe_allow_html=True)

    # ── Brand header ──────────────────────────────────────────────────────────
    st.markdown("""
    <div style='display:flex;align-items:center;gap:10px;margin-bottom:16px;
                padding:10px 18px;background:rgba(255,255,255,0.55);
                backdrop-filter:blur(6px);border-radius:10px;
                border:1px solid rgba(93,170,106,0.22);'>
      <svg width="26" height="26" viewBox="0 0 52 52" xmlns="http://www.w3.org/2000/svg">
        <line x1="14" y1="46" x2="14" y2="10" stroke="#3A8C4E" stroke-width="2.8" stroke-linecap="round"/>
        <line x1="9"  y1="10" x2="9"  y2="24" stroke="#3A8C4E" stroke-width="2"   stroke-linecap="round"/>
        <line x1="14" y1="10" x2="14" y2="24" stroke="#3A8C4E" stroke-width="2"   stroke-linecap="round"/>
        <line x1="19" y1="10" x2="19" y2="24" stroke="#3A8C4E" stroke-width="2"   stroke-linecap="round"/>
        <ellipse cx="36" cy="26" rx="13" ry="8.5" fill="#5DAA6A" transform="rotate(-28 36 26)"/>
        <line x1="24" y1="35" x2="46" y2="18" stroke="#9FD9A8" stroke-width="1.3" stroke-linecap="round"/>
      </svg>
      <span style='font-size:1.05rem;font-weight:700;color:#1E5C32;'>WhollyFare</span>
      <span style='color:#C8DFC8;margin:0 4px;'>·</span>
      <span style='font-size:0.82rem;color:#666;'>a <a href="https://sentir-solutions.com" target="_blank"
           style="color:#3A8C4E;font-weight:600;text-decoration:none;">Sentir Solutions</a>&#174; Company</span>
    </div>
    """, unsafe_allow_html=True)

    # ── Hero ──────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style='position:relative;overflow:hidden;
                background:linear-gradient(140deg,#142B1C 0%,#1E5C32 55%,#2D7A45 100%);
                border-radius:18px;padding:54px 52px 50px;margin-bottom:10px;'>

      <!-- Decorative leaf watermark (bottom-right) -->
      <svg style='position:absolute;right:-60px;bottom:-60px;opacity:0.06;pointer-events:none;'
           width="420" height="420" viewBox="0 0 420 420" xmlns="http://www.w3.org/2000/svg">
        <ellipse cx="210" cy="210" rx="180" ry="120" fill="white" transform="rotate(-28 210 210)"/>
        <line x1="80"  y1="310" x2="330" y2="120" stroke="white" stroke-width="5"/>
        <line x1="110" y1="340" x2="240" y2="155" stroke="white" stroke-width="2.5" opacity="0.7"/>
        <line x1="200" y1="290" x2="330" y2="155" stroke="white" stroke-width="2.5" opacity="0.7"/>
      </svg>

      <!-- Small top badge -->
      <div style='display:inline-flex;align-items:center;gap:7px;
                  background:rgba(255,255,255,0.1);border:1px solid rgba(255,255,255,0.18);
                  border-radius:20px;padding:5px 14px;margin-bottom:20px;'>
        <span style='width:7px;height:7px;background:#5DAA6A;border-radius:50%;display:inline-block;'></span>
        <span style='font-size:0.72rem;font-weight:600;letter-spacing:0.1em;
                     text-transform:uppercase;color:rgba(255,255,255,0.85);'>
          Smart meal planning &nbsp;·&nbsp; Sincere savings
        </span>
      </div>

      <!-- Headline -->
      <div style='font-size:3.1rem;font-weight:800;color:white;line-height:1.08;
                  letter-spacing:-0.025em;margin-bottom:16px;'>
        The meal plan<br>that pays you back.
      </div>

      <!-- Subhead -->
      <div style='font-size:1.05rem;color:rgba(255,255,255,0.75);
                  max-width:500px;line-height:1.65;margin-bottom:38px;'>
        Built from this week's actual sale prices at your local grocery stores —
        no subscriptions, no ads, no one getting paid to put food on your plate.
      </div>

      <!-- Stats row -->
      <div style='display:flex;gap:14px;flex-wrap:wrap;'>
        <div style='background:rgba(255,255,255,0.1);backdrop-filter:blur(8px);
                    border:1px solid rgba(255,255,255,0.14);border-radius:12px;
                    padding:16px 24px;min-width:130px;'>
          <div style='font-size:2.1rem;font-weight:800;color:white;line-height:1;'>15–25%</div>
          <div style='font-size:0.74rem;color:rgba(255,255,255,0.6);margin-top:5px;letter-spacing:0.02em;'>
            avg. grocery savings
          </div>
        </div>
        <div style='background:rgba(255,255,255,0.1);backdrop-filter:blur(8px);
                    border:1px solid rgba(255,255,255,0.14);border-radius:12px;
                    padding:16px 24px;min-width:130px;'>
          <div style='font-size:2.1rem;font-weight:800;color:#F28B30;line-height:1;'>~$2–4</div>
          <div style='font-size:0.74rem;color:rgba(255,255,255,0.6);margin-top:5px;letter-spacing:0.02em;'>
            per serving vs. $9.99 meal kits
          </div>
        </div>
        <div style='background:rgba(255,255,255,0.1);backdrop-filter:blur(8px);
                    border:1px solid rgba(255,255,255,0.14);border-radius:12px;
                    padding:16px 24px;min-width:130px;'>
          <div style='font-size:2.1rem;font-weight:800;color:white;line-height:1;'>$0</div>
          <div style='font-size:0.74rem;color:rgba(255,255,255,0.6);margin-top:5px;letter-spacing:0.02em;'>
            paid placements. Ever.
          </div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # CTA buttons sit flush below the hero
    h1, h2, h3 = st.columns([2, 2, 3])
    with h1:
        if st.button("🌿 Get started free", type="primary", use_container_width=True):
            st.switch_page("pages/1_Household.py")
    with h2:
        if st.button("📈 Investor brief", use_container_width=True):
            st.switch_page("pages/7_Investor.py")

    st.markdown("<div style='height:36px;'></div>", unsafe_allow_html=True)

    # ── How it works ──────────────────────────────────────────────────────────
    st.markdown("""
    <div style='text-align:center;margin-bottom:22px;'>
      <div style='font-size:0.7rem;font-weight:700;letter-spacing:0.13em;text-transform:uppercase;
                  color:#5DAA6A;margin-bottom:6px;'>How it works</div>
      <div style='font-size:1.55rem;font-weight:700;color:#1A2E1D;letter-spacing:-0.01em;'>
        Three steps. Every Sunday.
      </div>
    </div>
    """, unsafe_allow_html=True)

    s1, s2, s3 = st.columns(3)
    for col, icon, num, title, desc in zip(
        [s1, s2, s3],
        ["🏪", "🛡️", "✅"],
        ["01", "02", "03"],
        ["Load your stores", "We build your plan", "One tap to approve"],
        [
            "Pull this week's prices from Kroger live or PDF upload. We read the deals, not the ads.",
            "Safe, affordable meals from this week's best-priced ingredients — filtered for your family.",
            "Review dinners + Found Money on the Sunday Buy-Off screen. One tap sends the shopping list.",
        ],
    ):
        with col:
            st.markdown(f"""
            <div class='wf-card' style='background:white;border-radius:14px;padding:28px 22px 24px;
                        box-shadow:0 2px 20px rgba(30,92,50,0.07);text-align:center;'>
              <div style='width:48px;height:48px;background:linear-gradient(135deg,#E8F5EC,#D0EDD8);
                          border-radius:50%;display:flex;align-items:center;justify-content:center;
                          margin:0 auto 14px;font-size:1.4rem;'>{icon}</div>
              <div style='font-size:0.62rem;font-weight:700;letter-spacing:0.14em;text-transform:uppercase;
                          color:#5DAA6A;margin-bottom:6px;'>Step {num}</div>
              <div style='font-weight:700;font-size:1rem;color:#1A2E1D;margin-bottom:9px;'>{title}</div>
              <div style='font-size:0.84rem;color:#5A6B5E;line-height:1.6;'>{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:40px;'></div>", unsafe_allow_html=True)

    # ── Pricing tiers ─────────────────────────────────────────────────────────
    st.markdown("""
    <div style='text-align:center;margin-bottom:22px;'>
      <div style='font-size:0.7rem;font-weight:700;letter-spacing:0.13em;text-transform:uppercase;
                  color:#5DAA6A;margin-bottom:6px;'>Plans & pricing</div>
      <div style='font-size:1.55rem;font-weight:700;color:#1A2E1D;letter-spacing:-0.01em;'>
        Start free. Add what your family needs.
      </div>
    </div>
    """, unsafe_allow_html=True)

    tiers = [
        {
            "id": 1, "color": "#3A8C4E", "price": "Free", "price_sub": "forever",
            "name": "Price Finder", "badge": "",
            "tagline": "See where the savings are before you ever shop.",
            "features": [
                "Compare prices across all your local stores",
                "Digital coupon matching, automated",
                "Weekly savings report",
                "No credit card needed",
            ],
            "cta": "Get started",
        },
        {
            "id": 2, "color": "#5DAA6A", "price": "$7", "price_sub": "/ month",
            "name": "Meal Planner", "badge": "Most popular",
            "tagline": "Five dinners planned around this week's best prices.",
            "features": [
                "Everything in Price Finder",
                "Weekly 5-dinner meal plan",
                "Flavor Plugins — same ingredients, different cuisines",
                "Sunday Buy-Off approval screen",
                "Shopping list by store & category",
            ],
            "cta": "Start planning",
        },
        {
            "id": 3, "color": "#F28B30", "price": "$19", "price_sub": "/ month",
            "name": "Health Guard", "badge": "",
            "tagline": "Every ingredient checked against your family's health profile.",
            "features": [
                "Everything in Meal Planner",
                "Top-14 allergen hard filtering",
                "Celiac, MCAS, diabetes, CKD, IBS support",
                "Per-member household profiles",
                "Every rejection logged & explained",
            ],
            "cta": "Protect my family",
        },
        {
            "id": 4, "color": "#1E5C32", "price": "$29", "price_sub": "/ month",
            "name": "Full Table", "badge": "",
            "tagline": "Full recipes, cuisine learning, the complete experience.",
            "features": [
                "Everything in Health Guard",
                "Full recipes with prep times & quantities",
                "Cuisine preference memory",
                "Meal history & family favourites",
                "Priority support",
            ],
            "cta": "Get the full experience",
        },
    ]

    # Render tier cards
    t1, t2, t3, t4 = st.columns(4)
    for col, tier in zip([t1, t2, t3, t4], tiers):
        badge_html = (
            f"<div style='display:inline-block;background:{tier['color']};color:white;"
            f"font-size:0.65rem;font-weight:700;letter-spacing:0.07em;text-transform:uppercase;"
            f"border-radius:20px;padding:3px 10px;margin-bottom:12px;'>{tier['badge']}</div>"
            if tier["badge"] else "<div style='height:24px;'></div>"
        )
        feats = "".join(
            f"<div style='display:flex;gap:8px;align-items:flex-start;margin-bottom:8px;'>"
            f"<span style='color:{tier['color']};font-size:0.85rem;margin-top:1px;flex-shrink:0;'>✓</span>"
            f"<span style='font-size:0.8rem;color:#4A5568;line-height:1.45;'>{f}</span></div>"
            for f in tier["features"]
        )
        with col:
            st.markdown(f"""
            <div class='wf-card' style='background:white;border-radius:14px;
                        border-top:4px solid {tier["color"]};
                        box-shadow:0 2px 22px rgba(30,92,50,0.08);
                        padding:22px 18px 14px;min-height:340px;'>
              {badge_html}
              <div style='font-size:0.68rem;font-weight:700;letter-spacing:0.1em;
                          text-transform:uppercase;color:{tier["color"]};margin-bottom:6px;'>
                {tier["name"]}
              </div>
              <div style='margin-bottom:10px;line-height:1;'>
                <span style='font-size:2rem;font-weight:800;color:#1A2E1D;'>{tier["price"]}</span>
                <span style='font-size:0.76rem;color:#9AA8A0;margin-left:3px;'>{tier["price_sub"]}</span>
              </div>
              <div style='font-size:0.82rem;color:#5A6B5E;line-height:1.5;margin-bottom:14px;
                          min-height:36px;'>{tier["tagline"]}</div>
              <div style='border-top:1px solid #F0F4F1;padding-top:14px;'>
                {feats}
              </div>
            </div>
            """, unsafe_allow_html=True)

            if st.button(f"{tier['cta']} →", key=f"tier_{tier['id']}", use_container_width=True):
                current = st.session_state.get("tier_detail")
                st.session_state["tier_detail"] = tier["id"] if current != tier["id"] else None
                st.rerun()

    # ── Tier detail expand panel ───────────────────────────────────────────────
    active_id = st.session_state.get("tier_detail")
    if active_id:
        active = next((t for t in tiers if t["id"] == active_id), None)
        if active:
            feats_grid = "".join(
                f"<div style='display:flex;gap:8px;align-items:flex-start;'>"
                f"<span style='color:{active['color']};font-size:0.9rem;flex-shrink:0;'>✓</span>"
                f"<span style='font-size:0.85rem;color:#333;line-height:1.5;'>{f}</span></div>"
                for f in active["features"]
            )
            st.markdown(f"""
            <div class='wf-detail' style='background:white;border-radius:14px;
                        border-left:5px solid {active["color"]};
                        box-shadow:0 6px 36px rgba(30,92,50,0.12);
                        padding:28px 32px;margin-top:16px;'>
              <div style='display:flex;align-items:baseline;gap:10px;margin-bottom:6px;'>
                <span style='font-size:1.2rem;font-weight:800;color:#1A2E1D;'>{active["name"]}</span>
                <span style='font-size:1.4rem;font-weight:800;color:{active["color"]};'>{active["price"]}</span>
                <span style='font-size:0.8rem;color:#9AA8A0;'>{active["price_sub"]}</span>
              </div>
              <div style='font-size:0.9rem;color:#5A6B5E;margin-bottom:20px;'>{active["tagline"]}</div>
              <div style='display:grid;grid-template-columns:1fr 1fr;gap:10px 24px;'>
                {feats_grid}
              </div>
            </div>
            """, unsafe_allow_html=True)

            dc1, dc2, dc3 = st.columns([1, 2, 4])
            with dc1:
                if st.button("✕ Close", key="close_tier"):
                    st.session_state["tier_detail"] = None
                    st.rerun()
            with dc2:
                if st.button(f"🌿 Start with {active['name']}", type="primary", key="tier_cta"):
                    st.switch_page("pages/1_Household.py")

    st.markdown("<div style='height:32px;'></div>", unsafe_allow_html=True)

    # ── Trust bar ────────────────────────────────────────────────────────────
    st.markdown("""
    <div style='text-align:center;padding:15px 20px;
                background:rgba(255,255,255,0.6);backdrop-filter:blur(4px);
                border-radius:10px;border:1px solid rgba(93,170,106,0.18);'>
      <span style='font-size:0.85rem;color:#3A6645;font-weight:500;'>
        🚫 No paid placements &nbsp;·&nbsp; 🛡️ Health rules are absolute &nbsp;·&nbsp;
        🔍 Every pick shows its reason &nbsp;·&nbsp; 🔐 Your data is yours
      </span>
    </div>
    """, unsafe_allow_html=True)

    st.stop()


# ════════════════════════════════════════════════════════════════════════════════
# DASHBOARD VIEW — returning users with household set up
# ════════════════════════════════════════════════════════════════════════════════
hh_name = household.household_name if household else "your household"
week    = st.session_state["active_week"]

if approved and plan:
    st.markdown(f"""<div style='background:#E3F4E8;border:1px solid #A8D5B0;border-radius:10px;
                    padding:16px 20px;margin-bottom:16px;'>
      <span style='font-size:1rem;font-weight:600;color:#1E5C32;'>✅ Week of {week} is approved.</span>
      <span style='color:#3A8C4E;font-size:0.9rem;margin-left:8px;'>Your shopping list is ready.</span>
    </div>""", unsafe_allow_html=True)
elif plan:
    st.markdown(f"""<div style='background:#FFF8E1;border:1px solid #FFD54F;border-radius:10px;
                    padding:16px 20px;margin-bottom:16px;'>
      <span style='font-size:1rem;font-weight:600;color:#8C4A00;'>📋 Plan ready for {hh_name}.</span>
      <span style='color:#8C4A00;font-size:0.9rem;margin-left:8px;'>Head to Sunday Buy-Off to approve.</span>
    </div>""", unsafe_allow_html=True)
elif loaded:
    st.markdown(f"""<div style='background:#E3F4E8;border:1px solid #A8D5B0;border-radius:10px;
                    padding:16px 20px;margin-bottom:16px;'>
      <span style='font-size:1rem;font-weight:600;color:#1E5C32;'>📦 {len(loaded)} store(s) loaded.</span>
      <span style='color:#3A8C4E;font-size:0.9rem;margin-left:8px;'>Head to Grocer Hub to run the engine.</span>
    </div>""", unsafe_allow_html=True)
else:
    st.markdown("""<div style='background:#FFF3E0;border:1px solid #FFCC80;border-radius:10px;
                   padding:16px 20px;margin-bottom:16px;'>
      <span style='font-size:1rem;font-weight:600;color:#8C4A00;'>📄 No store data loaded yet for this week.</span>
      <span style='color:#8C4A00;font-size:0.9rem;margin-left:8px;'>Upload circulars or pull from Kroger in the Grocer Hub.</span>
    </div>""", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Household members", len(household.members) if household else 0)
with col2:
    st.metric("Stores configured", len(grocers))
with col3:
    st.metric("Weeks planned", len(history))
with col4:
    st.metric("Total Found Money 💚", f"${total_saved:,.2f}" if total_saved else "$0.00")

st.divider()
st.markdown(f"<div style='font-size:1rem;font-weight:600;color:#1E5C32;margin-bottom:12px;'>This week — {week}</div>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    if st.button(f"🏪 Grocer Hub  ({len(loaded)}/{len(grocers)} loaded)", use_container_width=True):
        st.switch_page("pages/2_Grocer_Hub.py")
with col2:
    if st.button("🍽️ View Plan" if plan else "⚙️ Generate Plan", use_container_width=True):
        st.switch_page("pages/3_Plan.py")
with col3:
    label = "✅ Sunday Buy-Off" + (" — done" if approved else "")
    if st.button(label, use_container_width=True, type="secondary" if approved else "primary"):
        st.switch_page("pages/4_Sunday_BuyOff.py")

if history:
    st.divider()
    st.markdown("<div style='font-size:1rem;font-weight:600;color:#1E5C32;margin-bottom:10px;'>Recent weeks</div>", unsafe_allow_html=True)
    for entry in reversed(history[-5:]):
        c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
        with c1:
            st.caption(f"**Week of {entry.get('week','—')}**  ·  {entry.get('meals',0)} dinners")
        with c2:
            st.caption(f"${entry.get('plan_cost',0):.2f} spent")
        with c3:
            st.caption(f"${entry.get('found_money',0):.2f} found")
        with c4:
            st.caption(f"📍 {entry.get('primary_grocer','—')}")
