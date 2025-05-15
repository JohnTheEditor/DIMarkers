import streamlit as st
import pandas as pd
from statistics import median
import io

FPS = 24

def timecode_to_frames(tc):
    h, m, s, f = map(int, tc.split(':'))
    return ((h * 3600 + m * 60 + s) * FPS) + f

def frames_to_timecode(frames):
    h = frames // (3600 * FPS)
    frames %= 3600 * FPS
    m = frames // (60 * FPS)
    frames %= 60 * FPS
    s = frames // FPS
    f = frames % FPS
    return f"{h:02}:{m:02}:{s:02}:{f:02}"

def process_sequence_report_from_df(df):
    markers = []
    previous_med_TC = ''

    for _, row in df.iterrows():
        try:
            start_tc = timecode_to_frames(row['Start Timecode'])
            end_tc = timecode_to_frames(row['End Timecode'])
            median_frame = median([start_tc, end_tc])
            median_tc = frames_to_timecode(int(median_frame))
            track = row['Track']
            effects = row['Effect Name'].replace("Timewarp", "Respeed").replace("3DWarp", "Repo/Resize").replace("Motion Effect", "Respeed")
            effects = effects.strip()

            if any(skip in effects for skip in ["Matte Key", "3D MatteKey", "Audio Pan/Volume", "Submaster", "Avid Titler+"]):
                continue

            comment = f"DI - {effects}"
            if median_tc == previous_med_TC:
                markers[-1] = markers[-1].replace('\t1', ', ' + effects + '\t1')
                continue

            markers.append(f"OPTICAL\t{median_tc}\t{track}\tblack\t{comment}\t1")
            previous_med_TC = median_tc
        except Exception as e:
            st.warning(f"Skipping a row due to error: {e}")
            continue

    return "\n".join(markers)

st.set_page_config(
    page_title="DI Marker List Tool",        # 🏷️ This is the tab title
    page_icon="🎬",                          # 📌 Emoji or URL to an icon image
    layout="centered",                       # or "wide"
    initial_sidebar_state="collapsed"
)

st.title("Sequence Report to Marker List")
st.markdown("""
No more manually typing out all your opticals for your DI Turnovers!

Create a CSV from the Media Composer Sequence Report tool, drop it here, and convert it into a `.txt` file to import back to Avid.

**Best Practices:**  
- Dupe your sequence, delete all audio tracks  
- Only select *Effects Location List* on your Sequence Report  
- Choose CSV (or this won't work!)

It will skip effects like Submasters & Matte Keys that you typically wouldn't want to be included anyways.

Your files will never be stored/uploaded/used to train advanced AI Assistant Editors.

---
Wanna give it a try?
""")

with open("SAMPLE_EFFECT_LOCATION.csv", "rb") as f:
    st.download_button(
        label="Download Sample CSV",
        data=f,
        file_name="SAMPLE_EFFECT_LOCATION.csv",
        mime="text/csv"
    )


uploaded_file = st.file_uploader("Add your CSV here.", type=["csv"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file, encoding='utf-16')
        result_text = process_sequence_report_from_df(df)

        st.text_area("Preview of Marker List", result_text, height=300)

        # Prepare for download
        result_bytes = io.BytesIO(result_text.encode('utf-8'))
        st.download_button("Download Marker List", result_bytes, file_name="marker_list.txt")

    except Exception as e:
        st.error(f"Failed to read or process file: {e}")

st.markdown("""
---


If anything is weird, feel free to say so!
📩 **JohnJGrenham@gmail.com**
""")
