from datetime import date
from itertools import cycle
import random
import time

import pandas as pd
import pydeck
import streamlit as st


@st.cache()
def get_data():
    """Get and parse the bicycle counts data"""

    counter_locations_url = "http://donnees.ville.montreal.qc.ca/dataset/f170fecc-18db-44bc-b4fe-5b0b6d2c7297/resource/c7d0546a-a218-479e-bc9f-ce8f13ca972c/download/localisationcompteursvelo2015.csv"
    bicycle_counts_urls = {
        2018: "http://donnees.ville.montreal.qc.ca/dataset/f170fecc-18db-44bc-b4fe-5b0b6d2c7297/resource/eea2434f-32b3-4dc5-9035-f1642509f0e7/download/comptage_velo_2018.csv",
        2017: "http://donnees.ville.montreal.qc.ca/dataset/f170fecc-18db-44bc-b4fe-5b0b6d2c7297/resource/83063700-8fe7-4e6f-8c4b-ed55f4602514/download/comptagevelo2017.csv",
        2016: "http://donnees.ville.montreal.qc.ca/dataset/f170fecc-18db-44bc-b4fe-5b0b6d2c7297/resource/6caecdd0-e5ac-48c1-a0cc-5b537936d5f6/download/comptagevelo20162.csv",
        2015: "http://donnees.ville.montreal.qc.ca/dataset/f170fecc-18db-44bc-b4fe-5b0b6d2c7297/resource/64c26fd3-0bdf-45f8-92c6-715a9c852a7b/download/comptagevelo20152.csv",
        # 2014: "http://donnees.ville.montreal.qc.ca/dataset/f170fecc-18db-44bc-b4fe-5b0b6d2c7297/resource/868b4bc8-ff55-4c48-ab3b-d80615445595/download/comptagevelo2014.csv",
        # 2013: "http://donnees.ville.montreal.qc.ca/dataset/f170fecc-18db-44bc-b4fe-5b0b6d2c7297/resource/ec12447d-6b2a-45d0-b0e7-fd69c382e368/download/comptagevelo2013.csv",
        # 2012: "http://donnees.ville.montreal.qc.ca/dataset/f170fecc-18db-44bc-b4fe-5b0b6d2c7297/resource/d54cec49-349e-47af-b152-7740056d7311/download/comptagevelo2012.csv",
        # 2011: "http://donnees.ville.montreal.qc.ca/dataset/f170fecc-18db-44bc-b4fe-5b0b6d2c7297/resource/f2e43419-ebb2-4e38-80b6-0644c8344338/download/comptagevelo2011.csv",
        # 2010: "http://donnees.ville.montreal.qc.ca/dataset/f170fecc-18db-44bc-b4fe-5b0b6d2c7297/resource/f23e1c88-cd04-467f-a64a-48f5eb1b6c9e/download/comptagevelo2010.csv",
        # 2009: "http://donnees.ville.montreal.qc.ca/dataset/f170fecc-18db-44bc-b4fe-5b0b6d2c7297/resource/ee1e9541-939d-429e-919a-8ab94527773c/download/comptagevelo2009.csv",
    }

    counter_locations = pd.read_csv(counter_locations_url, encoding="latin1")
    counter_locations = counter_locations.rename(
        columns={"coord_X": "lon", "coord_Y": "lat"}
    )
    bicycle_counts = pd.concat(
        [
            pd.read_csv(url, encoding="utf8", parse_dates=["Date"], index_col=0)
            for url in bicycle_counts_urls.values()
        ],
        sort=True,
    ).sort_index()

    # drop unnamed columns
    bicycle_counts = bicycle_counts.loc[
        :, ~bicycle_counts.columns.str.contains("^Unnamed")
    ]

    counter_locations = (
        counter_locations.drop("id", axis=1)
        .sort_values(by=["nom_comptage"])
        .reset_index(drop=True)
    )

    renames = {
        "Brebeuf": "Brébeuf",
        "CSC": "CSC (Côte Sainte-Catherine)",
        "Parc U-Zelt Test": "Parc",
        "Pont_Jacques-Cartier": "Pont Jacques-Cartier",
        "Rachel/Hôtel de Ville": "Rachel / Hôtel de Ville",
        "Rachel/Papineau": "Rachel / Papineau",
        "Saint-Laurent U-Zelt Test": "Saint-Laurent/Bellechasse",
        "Totem_Laurier": "Eco-Totem - Métro Laurier",
    }

    counts_df = pd.DataFrame(
        {
            "lat": counter_locations.lat,
            "lon": counter_locations.lon,
            "name": counter_locations.nom_comptage.map(
                lambda name: renames.get(name, name)
            ),
            "nom": counter_locations.nom,
        }
    )

    return counts_df, bicycle_counts


counts_df, bicycle_counts = get_data()

counts_df = counts_df.copy()  # don't modify output from a cached streamlit function

bicycle_counts = bicycle_counts.resample("M").mean().sort_index()

years_months_values = [(d.year, d.month) for d in bicycle_counts.index]
year, month = years_months_values[0]

st.header("Visualization of bicycle counts in Montreal, Qc")
date_value = st.empty()
month_slider = st.empty()
st.subheader("Animation")
animations = {"None": None, "Slow": 0.4, "Medium": 0.2, "Fast": 0.05}
animate = st.radio("", options=list(animations.keys()), index=2)
animation_speed = animations[animate]
deck_map = st.empty()


def render_slider(year, month):
    key = random.random() if animation_speed else None

    month_value = month_slider.slider(
        "",
        min_value=0,
        max_value=len(years_months_values),
        value=years_months_values.index((year, month)),
        format="",
        key=key,
    )
    year, month = years_months_values[month_value]
    d = date(year, month, 1)
    date_value.subheader(f"Month: {d:%Y}-{d:%m}")
    return year, month


def render_map(year, month):
    mask = (bicycle_counts.index.year == year) & (bicycle_counts.index.month == month)
    month_counts = bicycle_counts[mask].transpose().reset_index()
    month_counts.rename(
        columns={
            month_counts.columns[0]: "name",
            month_counts.columns[1]: "month_counts",
        },
        inplace=True,
    )

    counts_df["counts"] = counts_df.merge(
        month_counts, left_on="name", right_on="name"
    )["month_counts"]

    display_counts = counts_df[~pd.isna(counts_df["counts"])]
    deck_map.pydeck_chart(
        pydeck.Deck(
            map_style="mapbox://styles/mapbox/light-v9",
            initial_view_state=pydeck.ViewState(
                latitude=display_counts.lat.mean(),
                longitude=display_counts.lon.mean(),
                zoom=11.5,
                pitch=50,
            ),
            layers=[
                pydeck.Layer(
                    "ColumnLayer",
                    data=display_counts,
                    disk_resolution=12,
                    radius=130,
                    elevation_scale=1,
                    get_position="[lon, lat]",
                    get_color="[40, counts / 5000 * 255, 40, 150]",
                    get_elevation="[counts]",
                ),
            ],
        )
    )


if animation_speed:
    for year, month in cycle(years_months_values):
        time.sleep(animation_speed)
        render_slider(year, month)
        render_map(year, month)
else:
    year, month = render_slider(year, month)
    render_map(year, month)

