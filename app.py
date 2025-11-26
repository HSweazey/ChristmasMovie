import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import random

st.set_page_config(page_title="🎄 Christmas Movie Picker", page_icon="🎅")

# 1. ESTABLISH CONNECTION
# This connects to the Google Sheet defined in your secrets
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. FETCH DATA
# We use ttl=0 so it doesn't cache; we want instant updates if Mom adds a movie
df = conn.read(worksheet="Movies", ttl=0)

# Clean up dataframe (ensure columns exist even if empty)
required_columns = ["Title", "Platform", "Watched"]
for col in required_columns:
    if col not in df.columns:
        df[col] = ""

# --- HEADER ---
st.title("🎅 Christmas Movie Picker")
st.markdown("### *For You & Mom*")

# --- TAB LAYOUT ---
tab1, tab2, tab3 = st.tabs(["🍿 Pick a Movie", "➕ Add Movie", "📋 View List"])

# ==========================================
# TAB 1: PICK A MOVIE
# ==========================================
with tab1:
    # FILTER: Create the "Pool" of movies to pick from
    # We only want movies where 'Watched' is NOT 'Yes'
    unwatched_df = df[df["Watched"] != "Yes"]
    
    # OPTIONAL FILTER: By Platform
    all_platforms = unwatched_df["Platform"].unique().tolist()
    # Clean up nan/empty platforms
    all_platforms = [p for p in all_platforms if pd.notna(p) and p != ""]
    
    use_filter = st.checkbox("Filter by Streaming Service?")
    if use_filter:
        selected_platform = st.selectbox("Which service?", all_platforms)
        pool = unwatched_df[unwatched_df["Platform"] == selected_platform]
    else:
        pool = unwatched_df

    st.divider()

    # THE "SPIN" BUTTON
    if "selected_movie" not in st.session_state:
        st.session_state.selected_movie = None

    col1, col2 = st.columns([1, 2])
    
    with col1:
        if st.button("🎁 PICK A MOVIE", type="primary"):
            if not pool.empty:
                # Randomly sample 1 row
                st.session_state.selected_movie = pool.sample(1).iloc[0]
            else:
                st.error("No movies left to watch in this category! Time to add more.")

    # DRAW AGAIN (Just clears the selection so you can click Pick again)
    with col2:
        if st.button("🔄 Draw Again"):
            st.session_state.selected_movie = None
            st.rerun()

    # DISPLAY SELECTION
    if st.session_state.selected_movie is not None:
        movie = st.session_state.selected_movie
        st.success(f"### Tonight's Movie: **{movie['Title']}**")
        st.info(f"📺 Watch it on: **{movie['Platform']}**")

        # MARK AS WATCHED
        st.markdown("---")
        st.write("Finished watching?")
        if st.button(f"✅ Mark '{movie['Title']}' as Watched"):
            # Update the original dataframe
            # We find the index of the selected movie and update 'Watched' column
            # Note: We match by Title to be safe
            df.loc[df["Title"] == movie["Title"], "Watched"] = "Yes"
            
            # Write back to Google Sheets
            conn.update(worksheet="Movies", data=df)
            
            st.balloons()
            st.session_state.selected_movie = None
            st.toast("Movie marked as watched! Refreshing...")
            st.rerun()

# ==========================================
# TAB 2: ADD MOVIE
# ==========================================
with tab2:
    with st.form("add_movie_form"):
        new_title = st.text_input("Movie Title")
        new_platform = st.selectbox("Platform", ["Netflix", "Hulu", "Disney+", "Max", "Prime Video", "DVD/BluRay", "Other"])
        submitted = st.form_submit_button("Add to Database")
        
        if submitted and new_title:
            # Create a new row
            new_row = pd.DataFrame([{"Title": new_title, "Platform": new_platform, "Watched": ""}])
            # Append to current dataframe
            updated_df = pd.concat([df, new_row], ignore_index=True)
            # Update Google Sheet
            conn.update(worksheet="Movies", data=updated_df)
            st.success(f"Added '{new_title}' to the list!")
            st.rerun()

# ==========================================
# TAB 3: VIEW LIST
# ==========================================
with tab3:
    st.write("### All Movies")
    st.dataframe(df)
    st.caption("You can edit this data directly in the Google Sheet if you need to fix a typo.")