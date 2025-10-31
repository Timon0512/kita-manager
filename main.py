import os.path

import streamlit as st
import pandas as pd
import json

KIDS_PATH = "kinder.xlsx"
EVENTS_PATH = "events.json"

def load_json(path):
    if os.path.exists(path):
        with open(path) as f:
            d = json.load(f)
        return d
    else:
        return {}

def load_excel(path):
    return pd.read_excel(path)

def rotate_kids(kids: pd.DataFrame) -> pd.DataFrame:
    """
    Verschiebt die Kinder mit den angegebenen Vor- und Nachnamen ans Ende der Liste.

    Parameter:
    -----------
    kids : pd.DataFrame
        DataFrame mit den Spalten 'Vorname' und 'Nachname'.

    Rückgabe:
    ----------
    pd.DataFrame: neu sortierter DataFrame
    """

    # Aufteilen
    oben = kids[~kids["Bleibt zuhause"]]
    unten = kids[kids["Bleibt zuhause"]]



    # Neu zusammensetzen
    neue_liste = pd.concat([oben, unten]).reset_index(drop=True)

    # Hilfsspalte wieder entfernen
    neue_liste = neue_liste.drop(columns=["Bleibt zuhause"])
    return neue_liste

def delete_event(event_id):
    # Kids-Liste vom letzten gültigen Event
    current_kids = st.session_state["kids"].copy()
    event = st.session_state["events"][event_id]
    zuhause = event.get("zuhause", [])

    for kid in reversed(zuhause):  # rückwärts, damit Reihenfolge erhalten bleibt
        mask = (
                (current_kids["Vorname"] == kid["Vorname"])
                & (current_kids["Nachname"] == kid["Nachname"])
        )
        idx = current_kids.index[mask][0]
        row = current_kids.loc[[idx]]

        # Entfernen + nach oben setzen
        current_kids = current_kids.drop(idx)
        current_kids = pd.concat([row, current_kids]).reset_index(drop=True)

    del st.session_state["events"][event_id]
    save_json(EVENTS_PATH, st.session_state["events"])
    st.session_state["kids"] = current_kids

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f)


if 'kids' not in st.session_state:
    st.session_state['kids'] = load_excel(KIDS_PATH)
if "events" not in st.session_state:
    st.session_state["events"] = load_json(EVENTS_PATH)


@st.dialog("Neues Event anlegen")
def select_kids(kids):
    anzahl = st.number_input("Wie viele Kinder müssen zuhause bleiben?", min_value=1, step=1)
    datum = st.date_input("Datum der Notbetreuung", format="DD.MM.YYYY")

    kids["Bleibt zuhause"] = False
    kids.loc[kids.head(anzahl).index, "Bleibt zuhause"] = True
    nom_kids = st.data_editor(kids, hide_index=True)
    event_anlegen = st.button("Event anlegen")

    kids_dict = (
        nom_kids[nom_kids["Bleibt zuhause"]]
        .drop("Bleibt zuhause", axis=1)
        .to_dict(orient="index")
    )

    event = {
        "datum": str(datum),
        "zuhause": list(kids_dict.values())
    }

    max_id = max(st.session_state["events"].keys(), default=0) + 1

    if event_anlegen:
        st.session_state["kids"] = rotate_kids(nom_kids)
        st.session_state["kids"].to_excel(KIDS_PATH, index=False)
        st.session_state["events"][max_id] = event
        save_json(EVENTS_PATH, st.session_state["events"])

        st.rerun()

@st.dialog("Event bearbeiten")
def edit_event():
    options = list(st.session_state["events"].keys())
    event_id = st.selectbox("Wähle das Event aus:",
                 options=options,
                 format_func=lambda eid: st.session_state["events"][eid]["datum"])

    default_date = st.session_state["events"].get(event_id).get("datum")
    st.write(default_date)
    new_date = st.date_input(
        "Neues Datum", pd.to_datetime(default_date, format="ISO8601"))
    #
    # # aktuelle Kinder anzeigen und ggf. neu wählen
    kids_df = st.session_state["kids"].copy()
    kids_df["Bleibt zuhause"] = False
    for kid in st.session_state["events"].get(event_id)["zuhause"]:
        mask = (
            (kids_df["Vorname"] == kid["Vorname"])
            & (kids_df["Nachname"] == kid["Nachname"])
        )
        kids_df.loc[mask, "Bleibt zuhause"] = True

    updated_df = st.data_editor(kids_df, hide_index=True)

    col1, col2 = st.columns(2)
    with col1:
        speichern = st.button("Änderungen speichern")
    with col2:
        löschen = st.button("Event löschen")


    if speichern:
        kids_dict = (
            updated_df[updated_df["Bleibt zuhause"]]
            .drop("Bleibt zuhause", axis=1)
            .to_dict(orient="records")
        )

        # Event im Session-State aktualisieren
        st.session_state["events"][event_id] = {
            "datum": str(new_date),
            "zuhause": kids_dict,
        }
        save_json(EVENTS_PATH, st.session_state["events"])
        st.session_state["kids"].to_excel(KIDS_PATH, index=False)
        st.rerun()

    if löschen:
        delete_event(event_id)
        st.rerun()


# --- Custom CSS ---
st.markdown("""
<style>
.header-card {
    background-color: white;
    border-radius: 12px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    padding: 1.2rem 1.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
}
.header-text h2 {
    margin: 0;
    font-size: 1.3rem;
    font-weight: 700;
    color: #1b1f3b;
}
.header-text p {
    margin: 0;
    color: #666;
    font-size: 0.9rem;
}
.create-btn {
    background-color: #4a4ff7;
    color: white !important;
    border: none;
    border-radius: 8px;
    padding: 0.6rem 1.2rem;
    font-weight: 600;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 0.4rem;
    text-decoration: none;
    transition: all 0.15s ease-in-out;
}
.create-btn:hover {
    background-color: #373bd3;
}
.card {
    background-color: #f8f9fe;
    border-radius: 16px;
    padding: 1rem 1.5rem;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    width: 90% 
}
.badge {
    background-color: #e5e9ff;
    color: #4a4ff7;
    border-radius: 50%;
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
    margin-right: 1rem;
}
.card h4 {
    margin: 0;
    font-size: 1.1rem;
}
.event-card {
  background: #f8f9fe;
  border-radius: 14px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  padding: 1.5rem;
  margin-bottom: 1.2rem;
  border: 1px solid rgba(0,0,0,0.05);
  text-align: center;
  width: 45%
}

.event-date {
  background: #e9edff;
  color: #4044f2;
  font-weight: 700;
  border-radius: 999px;
  display: inline-block;
  padding: 0.4rem 1rem;
  font-size: 1rem;
  margin-bottom: 1rem;
  width: 90%
}

.kid-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.kid-item {
  background: #f8f9fe;
  border-radius: 10px;
  padding: 8px 10px;
  margin-bottom: 6px;
  font-weight: 600;
  color: #333;
  display: flex;
  align-items: center;
  justify-content: left;
  gap: .5rem;
}

.kid-item::before {
  content: "";
  font-size: 1rem;
}
</style>
""", unsafe_allow_html=True)

# --- Layout ---

st.markdown("### Willkommen!")
st.write("Verwalten Sie hier die Notbetreuungs-Events!")

if len(st.session_state["events"]) == 0:
    st.success("Aktuell gibt es keine Notbetreuung.")

else:
    st.markdown(f"##### Aktuell geplante Notbetreuungen ({len(st.session_state['events'])})")
    # Event Cards rendern
    for event_id, event in st.session_state["events"].items():
        date = event.get("datum", "–")
        zuhause = event.get("zuhause", [])

        # HTML für Kinderliste ohne \n bauen
        kids_html = "".join(
            f"<li class='kid-item'>{k['Vorname']} {k['Nachname']}</li>"
            for k in zuhause
        )

        html = f"""
    <div class="event-card">
      <div class="event-date">{date}</div>
      <ul class="kid-list">{kids_html}</ul>
    </div>
    """
        st.markdown(html, unsafe_allow_html=True)

if len(st.session_state["events"]) == 0:

    st.markdown('</div>', unsafe_allow_html=True)
    new_event = st.button("Neues Event erstellen")
    st.markdown('</div>', unsafe_allow_html=True)

else:
    col1, col2, col3= st.columns(3)
    with col1:
        st.markdown('</div>', unsafe_allow_html=True)
        new_event = st.button("Neues Event erstellen")
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('</div>', unsafe_allow_html=True)
        edit_event_button = st.button("Event bearbeiten")
        st.markdown('</div>', unsafe_allow_html=True)

    if edit_event_button:
        edit_event()
        #recalc_following_events(2)


st.markdown("""
<div class="section-title">👥 Kinder-Warteliste</div>
<div class="section-desc">Die Kinder an der Spitze der Liste werden bei der nächsten Notbetreuung zuerst ausgewählt.</div>
""", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- Cards rendern ---
for i, row in enumerate(st.session_state['kids'].itertuples(index=False), start=1):
    vorname = row.Vorname
    nachname = row.Nachname
    st.markdown(f"""
    <div class="card">
        <div class="badge">{i}</div>
        <h4>{vorname} {nachname}</h4>
    </div>
    """, unsafe_allow_html=True)


if new_event:
    select_kids(st.session_state['kids'])


