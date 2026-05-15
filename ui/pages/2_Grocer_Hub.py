"""
2_Grocer_Hub.py — Grocer Data Hub
Admin page for loading weekly price data from all configured stores.
Handles: Kroger API pull, PDF upload + parse, per-store status.
"""

import sys, json, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st
import ui.state as state
import ui.style as style

from app.data.flyer_ingestor import FlyerIngestor

st.set_page_config(page_title="Grocer Hub · WhollyFare", page_icon="🏪", layout="wide")
state.init()


# ── Shared helper functions (used throughout this page) ───────────────────────

def _chain_name(g: dict) -> str:
    """Return the display name for a grocer, tolerating both 'chain' and 'name' keys."""
    return g.get("chain") or g.get("name", "?")


def _source(g: dict) -> str:
    """Return the data-source string, tolerating both 'source' and 'source_type' keys."""
    return g.get("source") or g.get("source_type", "manual_pdf")


with st.sidebar:
    style.sidebar_nav()

style.page_header(
    "Grocer Data Hub",
    "Load weekly price data for each store. The engine runs once all the stores you care about are loaded.",
)

# ── Setup progress stepper ────────────────────────────────────────────────────
st.markdown("""
<div style='display:flex;align-items:center;gap:0;margin-bottom:22px;'>
  <div style='background:#D8EDD0;color:#5A7A62;border-radius:50%;width:28px;height:28px;
              display:flex;align-items:center;justify-content:center;font-size:0.8rem;font-weight:700;
              flex-shrink:0;'>✓</div>
  <div style='height:2px;width:40px;background:#3A8C4E;'></div>
  <div style='background:#3A8C4E;color:white;border-radius:50%;width:28px;height:28px;
              display:flex;align-items:center;justify-content:center;font-size:0.8rem;font-weight:700;
              flex-shrink:0;'>2</div>
  <div style='height:2px;width:40px;background:#D8EDD0;'></div>
  <div style='background:#D8EDD0;color:#5A7A62;border-radius:50%;width:28px;height:28px;
              display:flex;align-items:center;justify-content:center;font-size:0.8rem;font-weight:700;
              flex-shrink:0;'>3</div>
  <div style='margin-left:12px;font-size:0.82rem;color:#5A7A62;'>
    Household → <strong style='color:#1E5C32;'>Grocer Prices</strong> → Generate Plan
  </div>
</div>
""", unsafe_allow_html=True)

# ── Demo load banner ──────────────────────────────────────────────────────────
with st.expander("✨ No grocery data yet? Load a sample week of prices to see the full flow →", expanded=False):
    st.caption("Pre-loads realistic Kroger + Food Lion sale prices for the week of May 11, 2026. "
               "Includes chicken, salmon, ground beef, produce, and pantry staples.")
    if st.button("🌿 Load sample week prices", type="primary", key="load_demo_grocers"):
        try:
            from app.data.sample_data import load_all_demo_data
            demo = load_all_demo_data()

            # Normalize grocers to the {chain, source, location, …} format the Hub expects
            raw_grocers = demo["grocers"]
            norm_grocers = []
            for g in raw_grocers:
                src = g.get("source") or ("api" if g.get("source_type") == "api" else "manual_pdf")
                norm_grocers.append({
                    "chain":      g.get("chain") or g.get("name", "?"),
                    "location":   g.get("location", ""),
                    "source":     src,
                    "rewards":    g.get("rewards", False),
                    "delivery":   g.get("delivery", False),
                    "is_primary": g.get("is_primary", False),
                })

            # Normalize flyer_data from {week, stores: {id: {store_name, items}}} to
            # {store_display_name: list_of_item_dicts} for status badges to work
            raw_flyer = demo["flyer_data"]
            if "stores" in raw_flyer:
                norm_flyer = {}
                for _sid, _sdata in raw_flyer["stores"].items():
                    _display = _sdata.get("store_name", _sid)
                    norm_flyer[_display] = _sdata.get("items", [])
            else:
                norm_flyer = raw_flyer

            st.session_state["grocers"]        = norm_grocers
            st.session_state["flyer_data"]     = norm_flyer
            st.session_state["plan"]           = demo["plan"]
            st.session_state["ledger_history"] = demo["ledger_history"]
            st.session_state["active_week"]    = demo["active_week"]
            st.success("Sample prices loaded for Kroger + Food Lion! Scroll down to review, then head to This Week's Plan.")
            st.rerun()
        except Exception as e:
            st.error(f"Could not load demo data: {e}")

# ── Week selector ─────────────────────────────────────────────────────────────
col_w, col_status, col_pull = st.columns([2, 2, 1])
with col_w:
    active_week = st.date_input(
        "Planning week",
        value=__import__('datetime').date.fromisoformat(st.session_state["active_week"]),
        label_visibility="collapsed",
    )
    st.session_state["active_week"] = active_week.isoformat()

loaded  = state.stores_loaded_this_week()
grocers = st.session_state.get("grocers", [])

with col_status:
    if len(loaded) == 0:
        st.markdown('<span class="pill pill-miss">⚠ No stores loaded</span>', unsafe_allow_html=True)
    elif len(loaded) < len(grocers):
        st.markdown(
            f'<span class="pill pill-warn">⚠ {len(loaded)} of {len(grocers)} loaded</span>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<span class="pill pill-ok">✓ All {len(loaded)} stores loaded</span>',
            unsafe_allow_html=True,
        )

with col_pull:
    if st.button("Pull all API stores", use_container_width=True):
        _pull_all_api = True
    else:
        _pull_all_api = False

# ── Summary metrics ───────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("Stores loaded",     len(loaded))
c2.metric("Awaiting data",     max(0, len(grocers) - len(loaded)))
c3.metric("API connected",     sum(1 for g in grocers if _source(g) == "api"))
c4.metric("Items loaded",      state.total_items_loaded())

st.divider()

# ── Add / manage store configuration (sidebar panel) ─────────────────────────
with st.sidebar:
    st.markdown("### Configured stores")
    for i, g in enumerate(grocers):
        chain_display = g.get("chain") or g.get("name", "?")
        src = g.get("source") or g.get("source_type", "")
        icon = "🔗" if src in ("api",) else "📄"
        st.caption(f"{icon} {chain_display}")
    st.divider()

    with st.expander("＋ Add a store"):
        new_chain  = st.text_input("Store name", placeholder="e.g. Food Lion", key="new_chain")
        new_loc    = st.text_input("Location / zip", placeholder="Palmyra, VA 22963", key="new_loc")
        new_source = st.selectbox(
            "Data source",
            options=["manual_pdf", "api", "manual_pdf+api"],
            format_func=lambda x: {
                "manual_pdf":     "PDF upload (manual)",
                "api":            "API (auto-pull)",
                "manual_pdf+api": "PDF + partial API",
            }[x],
            key="new_source",
        )
        new_rewards = st.checkbox("Loyalty/rewards program enrolled", key="new_rewards")
        new_delivery= st.checkbox("Prefer delivery", key="new_delivery")
        new_primary = st.checkbox("Set as primary store", key="new_primary")

        if st.button("Add store", type="primary"):
            if new_chain.strip():
                if new_primary:
                    for g in grocers:
                        g["is_primary"] = False
                grocers.append({
                    "chain":          new_chain.strip(),
                    "location":       new_loc.strip(),
                    "source":         new_source,
                    "rewards":        new_rewards,
                    "delivery":       new_delivery,
                    "is_primary":     new_primary,
                })
                st.session_state["grocers"] = grocers
                st.rerun()

# ── If no stores yet, prompt to add one ──────────────────────────────────────
if not grocers:
    st.info("No stores configured yet. Use the sidebar to add your first store.", icon="🏪")
    st.stop()

# ── Store cards ───────────────────────────────────────────────────────────────
ingestor = FlyerIngestor()

# Separate API-connected and manual stores
api_stores    = [g for g in grocers if _source(g) in ("api", "manual_pdf+api")]
manual_stores = [g for g in grocers if _source(g) == "manual_pdf"]


def _status_badge(chain: str) -> str:
    if chain in loaded:
        raw = st.session_state["flyer_data"].get(chain, [])
        count = len(raw)
        return f'<span class="pill pill-ok">✓ {count} items</span>'
    return '<span class="pill pill-miss">⚠ No data</span>'


def _load_json_flyer(chain: str, json_path: Path):
    """Parse and store a pre-parsed flyer JSON."""
    try:
        candidates = ingestor.from_json(json_path)
        flyer_data = st.session_state.get("flyer_data", {})
        flyer_data[chain] = candidates
        st.session_state["flyer_data"] = flyer_data
        return len(candidates)
    except Exception as e:
        st.error(f"Failed to parse flyer JSON: {e}")
        return 0


def _load_pdf_flyer(chain: str, pdf_bytes: bytes) -> int:
    """Run the appropriate chain parser on an uploaded PDF."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(pdf_bytes)
        tmp_path = Path(tmp.name)

    try:
        if "food lion" in chain.lower():
            from integrations.food_lion.parser import FoodLionParser
            parser = FoodLionParser(flyer_week=st.session_state["active_week"])
            result = parser.parse_pdf(tmp_path)
            # Enrich nutrition if USDA key is available
            import os
            usda_key = os.environ.get("USDA_API_KEY", "")
            if usda_key:
                from integrations.food_lion.usda_enricher import USDAEnricher
                USDAEnricher(api_key=usda_key).enrich(result)
            # Save parsed JSON to flyers directory
            out = Path("app/data/flyers") / f"food_lion_{st.session_state['active_week']}.json"
            parser.save(result, out)
            # Load into session
            candidates = ingestor.from_json(out)
        else:
            # Generic: try the base FlyerIngestor PDF path
            candidates = ingestor.from_pdf(tmp_path)

        flyer_data = st.session_state.get("flyer_data", {})
        flyer_data[chain] = candidates
        st.session_state["flyer_data"] = flyer_data
        return len(candidates)

    except Exception as e:
        st.error(f"PDF parse failed for {chain}: {e}")
        return 0
    finally:
        tmp_path.unlink(missing_ok=True)


def _pull_kroger(chain: str, location_id: str) -> int:
    """Pull sale items from Kroger API."""
    import os
    client_id     = os.environ.get("KROGER_CLIENT_ID", "")
    client_secret = os.environ.get("KROGER_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        st.warning(
            "Kroger API credentials not set. "
            "Set KROGER_CLIENT_ID and KROGER_CLIENT_SECRET environment variables.",
            icon="🔑",
        )
        return 0
    try:
        from integrations.kroger.client import KrogerClient
        client = KrogerClient(
            client_id=client_id,
            client_secret=client_secret,
            location_id=location_id,
        )
        result = client.get_weekly_sales(flyer_week=st.session_state["active_week"])
        # Save JSON
        out = Path("app/data/flyers") / f"kroger_{st.session_state['active_week']}.json"
        client.save(result, out)
        # Load candidates
        candidates = ingestor.from_json(out)
        flyer_data = st.session_state.get("flyer_data", {})
        flyer_data[chain] = candidates
        st.session_state["flyer_data"] = flyer_data
        return len(candidates)
    except Exception as e:
        st.error(f"Kroger pull failed: {e}")
        return 0


# ── Render API stores ─────────────────────────────────────────────────────────
if api_stores:
    st.markdown("**API-connected stores**")
    for g in api_stores:
        chain   = _chain_name(g)
        is_ok   = chain in loaded

        with st.container(border=True):
            col_icon, col_info, col_actions = st.columns([0.5, 3, 2])
            with col_icon:
                st.markdown("🔗" if is_ok else "⚡")
            with col_info:
                st.markdown(
                    f"**{chain}**  {_status_badge(chain)}",
                    unsafe_allow_html=True,
                )
                meta = g.get("location", "")
                if g.get("rewards"):
                    meta += "  · 🎟 Rewards enrolled"
                if g.get("is_primary"):
                    meta += "  · ⭐ Primary store"
                st.caption(meta)
            with col_actions:
                bcol1, bcol2 = st.columns(2)
                with bcol1:
                    lbl = "Re-pull" if is_ok else "Pull from API"
                    if st.button(lbl, key=f"pull_{chain}", use_container_width=True):
                        with st.spinner(f"Pulling {chain}…"):
                            n = _pull_kroger(chain, g.get("location", ""))
                        if n:
                            st.success(f"{n} items loaded.", icon="✅")
                            st.rerun()
                with bcol2:
                    if is_ok:
                        if st.button("View items", key=f"view_{chain}", use_container_width=True):
                            st.session_state["_view_store"] = chain
                            st.rerun()

    # Handle "pull all" button
    if _pull_all_api:
        for g in api_stores:
            with st.spinner(f"Pulling {g['chain']}…"):
                n = _pull_kroger(g["chain"], g.get("location", ""))
            if n:
                st.toast(f"{g['chain']}: {n} items loaded ✓")
        st.rerun()

    st.divider()

# ── Render manual upload stores ───────────────────────────────────────────────
if manual_stores:
    st.markdown("**Manual upload stores** (download PDF → upload here)")
    for g in manual_stores:
        chain  = _chain_name(g)
        is_ok  = chain in loaded

        # Flyer download link hint per chain
        hints = {
            "food lion": "https://stores.foodlion.com",
            "giant":     "https://stores.giantfood.com",
            "wegmans":   "https://www.wegmans.com/weeklyad",
            "walmart":   "https://www.walmart.com/store/finder",
        }
        dl_url = hints.get(chain.lower(), "")

        with st.container(border=True):
            col_icon, col_info, col_upload = st.columns([0.5, 2.5, 2.5])
            with col_icon:
                st.markdown("✅" if is_ok else "📄")
            with col_info:
                st.markdown(
                    f"**{chain}**  {_status_badge(chain)}",
                    unsafe_allow_html=True,
                )
                loc_txt = g.get("location", "")
                if g.get("is_primary"):
                    loc_txt += "  · ⭐ Primary"
                if dl_url:
                    loc_txt += f"  · [Download circular]({dl_url})"
                st.caption(loc_txt, unsafe_allow_html=True)

            with col_upload:
                uploaded = st.file_uploader(
                    f"Upload {chain} circular",
                    type=["pdf", "json"],
                    key=f"upload_{chain}",
                    label_visibility="collapsed",
                )
                if uploaded:
                    ext = Path(uploaded.name).suffix.lower()
                    with st.spinner(f"Parsing {chain} flyer…"):
                        if ext == ".json":
                            with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
                                tmp.write(uploaded.read())
                                n = _load_json_flyer(chain, Path(tmp.name))
                        else:
                            n = _load_pdf_flyer(chain, uploaded.read())
                    if n:
                        st.success(f"✅ {n} items loaded from {uploaded.name}")
                        st.rerun()

# ── Item preview (drill-down) ─────────────────────────────────────────────────
view_store = st.session_state.pop("_view_store", None)
if view_store and view_store in st.session_state.get("flyer_data", {}):
    st.divider()
    st.markdown(f"**{view_store} — items loaded this week**")
    items = st.session_state["flyer_data"][view_store]
    rows = []
    for c in items:
        # Support both IngredientCandidate dataclass objects and plain dicts
        if isinstance(c, dict):
            price = c.get("sale_price") or c.get("sale_price_per_unit", 0)
            unit  = c.get("unit", "")
            rows.append({
                "Name":      c.get("name", "?"),
                "Category":  c.get("category", "—"),
                "Sale price": f"${price:.2f}/{unit}" if price else "—",
                "Regular":   f"${c['regular_price']:.2f}" if c.get("regular_price") else "—",
                "Allergens": ", ".join(c.get("allergens", [])) or "—",
            })
        else:
            rows.append({
                "Name":      c.name,
                "Category":  c.category,
                "Sale price": f"${c.sale_price_per_unit:.2f}/{c.unit}",
                "Regular":   "—",
                "Allergens": ", ".join(c.allergens) or "—",
            })
    st.dataframe(rows, use_container_width=True, height=300)

st.divider()

# ── Run the engine ────────────────────────────────────────────────────────────
all_candidates = [c for v in st.session_state.get("flyer_data", {}).values() for c in v]
can_run = len(all_candidates) > 0 and st.session_state.get("household") is not None

if not can_run:
    reasons = []
    if not st.session_state.get("household"):
        reasons.append("household profile not set up")
    if len(all_candidates) == 0:
        reasons.append("no store data loaded")
    st.warning(f"Can't run yet — {' and '.join(reasons)}.", icon="⚠️")

run_btn = st.button(
    "⚙️ Run the engine →",
    type="primary",
    use_container_width=True,
    disabled=not can_run,
)

if run_btn:
    household = st.session_state["household"]

    with st.spinner("Running constraint engine…"):
        from app.core_logic.constraint_engine import ConstraintEngine
        engine = ConstraintEngine(household)
        result = engine.filter(all_candidates)
        st.session_state["filter_result"] = result

    with st.spinner(f"Optimising budget across {len(result.passed)} safe ingredients…"):
        from app.core_logic.budget_optimizer import BudgetOptimizer
        optimizer = BudgetOptimizer(
            weekly_budget=household.weekly_budget_usd,
            servings_per_meal=household.servings_per_meal,
            meals_per_week=household.meals_per_week,
        )
        scored   = optimizer.score(result.passed)
        selected = optimizer.select_ingredients(scored)

    with st.spinner("Assembling weekly meal plan…"):
        from app.core_logic.meal_planner import MealPlanner
        planner   = MealPlanner(household)
        raw_plan  = planner.assemble_week(
            hero_ingredients=selected,
            flyer_week=st.session_state["active_week"],
        )
        n_meals = len(raw_plan.meals)

        # Convert WeeklyPlan dataclass to the dict format expected by pages 3/4/5
        plan_meals = []
        plan_total = 0.0
        for meal in raw_plan.meals:
            ing_list = []
            meal_cost = 0.0
            for scored in meal.ingredients:
                ing = scored.ingredient
                cost = ing.sale_price_per_unit
                ing_list.append({
                    "item":  ing.name,
                    "qty":   f"1 {ing.unit}",
                    "store": getattr(ing, "source_store", "kroger_palmyra"),
                    "cost":  round(cost, 2),
                })
                meal_cost += cost
            is_gf = all("gluten-free" in getattr(i.ingredient, "tags", []) for i in meal.ingredients)
            plan_meals.append({
                "day":            meal.day,
                "name":           meal.name,
                "gluten_free":    is_gf,
                "allergen_notes": "",
                "best_store":     "kroger_palmyra",
                "ingredients":    ing_list,
                "meal_cost":      round(meal_cost, 2),
            })
            plan_total += meal_cost

        total_servings = n_meals * household.servings_per_meal
        single_est     = round(plan_total * 1.18, 2)
        hf_equiv       = round(total_servings * 9.99, 2)

        plan_dict = {
            "week":     st.session_state["active_week"],
            "servings": household.servings_per_meal,
            "meals":    plan_meals,
            "totals": {
                "whollyfare_plan":   round(plan_total, 2),
                "single_store_best": single_est,
                "hellofresh_equiv":  hf_equiv,
                "found_money":       round(single_est - plan_total, 2),
                "vs_hellofresh":     round(hf_equiv - plan_total, 2),
            },
        }
        st.session_state["plan"] = plan_dict

    n_passed   = len(result.passed)
    n_rejected = len(result.rejected)
    st.success(
        f"✅ Plan generated — {n_meals} dinners · "
        f"{n_passed} ingredients cleared · {n_rejected} rejected for safety.",
        icon="✅",
    )
    st.page_link("pages/3_Plan.py", label="→ Review the plan", icon="🍽️")
    st.page_link("pages/4_Sunday_BuyOff.py", label="→ Go straight to Buy-Off", icon="✅")
