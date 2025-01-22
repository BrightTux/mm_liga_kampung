from collections import defaultdict
from pathlib import Path
import sqlite3

import streamlit as st
import altair as alt
import pandas as pd


# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title="Liga Kampung Score Card",
    page_icon=":chicken:",  # This is an emoji shortcode. Could be a URL too.
)


# -----------------------------------------------------------------------------
# Declare some useful functions.


def connect_db():
    """Connects to the sqlite database."""

    DB_FILENAME = Path(__file__).parent / "scorecard.db"
    db_already_exists = DB_FILENAME.exists()

    conn = sqlite3.connect(DB_FILENAME)
    db_was_just_created = not db_already_exists

    return conn, db_was_just_created


def initialize_data(conn):
    """Initializes the score card table with some data."""
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS score_card (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contestant_name TEXT,
            contestant_id INTEGER,
            total_tops INTEGER,
            total_penalty INTEGER,
            description TEXT
        )
        """
    )

    cursor.execute(
        """
        INSERT INTO score_card
            (contestant_name, contestant_id, total_tops, total_penalty, description)
        VALUES
            -- Initial participants
            ('Azrai', 2501, 0, 0, ''),
            ('Fais', 2502, 0, 0, ''),
            ('Avish', 2503, 0, 0, ''),
            ('Clarence', 2504, 0, 0, ''),
            ('Shah', 2505, 0, 0, ''),
            ('Shakel', 2506, 0, 0, ''),
            ('Shaa', 2507, 0, 0, ''),
            ('Joe', 2508, 0, 0, ''),
            ('Meng', 2509, 0, 0, ''),
            ('Jien', 2510, 0, 0, ''),
            ('Paan', 2511, 0, 0, ''),
            ('Fatin', 2512, 0, 0, ''),
            ('Perong', 2513, 0, 0, ''),
            ('Oliver', 2514, 0, 0, '')
        """
    )
    conn.commit()


def load_data(conn):
    """Loads the score card data from the database."""
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM score_card")
        data = cursor.fetchall()
    except:
        return None

    df = pd.DataFrame(
        data,
        columns=[
            "id",
            "contestant_name",
            "contestant_id",
            "total_tops",
            "total_penalty",
            "description",
        ],
    )

    return df


def update_data(conn, df, changes):
    """Updates the score card data in the database."""
    cursor = conn.cursor()

    if changes["edited_rows"]:
        deltas = st.session_state.score_card["edited_rows"]
        rows = []

        for i, delta in deltas.items():
            row_dict = df.iloc[i].to_dict()
            row_dict.update(delta)
            rows.append(row_dict)

        cursor.executemany(
            """
            UPDATE score_card
            SET
                contestant_name = :contestant_name,
                contestant_id = :contestant_id,
                total_tops = :total_tops,
                total_penalty = :total_penalty,
                description = :description
            WHERE id = :id
            """,
            rows,
        )

    if changes["added_rows"]:
        cursor.executemany(
            """
            INSERT INTO score_card
                (id, contestant_name, contestant_id, total_tops, total_penalty, description)
            VALUES
                (:id, :contestant_name, :contestant_id, :total_tops, :total_penalty, :description)
            """,
            (defaultdict(lambda: None, row) for row in changes["added_rows"]),
        )

    if changes["deleted_rows"]:
        cursor.executemany(
            "DELETE FROM score_card WHERE id = :id",
            ({"id": int(df.loc[i, "id"])} for i in changes["deleted_rows"]),
        )

    conn.commit()


# -----------------------------------------------------------------------------
# Draw the actual page, starting with the score card table.

# Set the title that appears at the top of the page.
"""
# :chicken: Madmonkeyz Liga Kampung Score Card

**Welcome to MadMonkeyz Liga Kampung Score Card!**
This page reads and writes directly from/to our score card database.
"""

st.info(
    """
    Use the table below to add, remove, and edit items.
    And don't forget to commit your changes when you're done.
    """
)

# Custom CSS to limit input field width to 10% of the page width
st.markdown(
    """
    <style>
    div[data-testid="stNumberInput"] > div {
        width: 20% !important;
        min-width: 100px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Numeric input field
num = st.number_input("Enter a number:")

st.write("You entered:", num)

# Connect to database and create table if needed
conn, db_was_just_created = connect_db()

# Initialize data.
if db_was_just_created:
    initialize_data(conn)
    st.toast("Database initialized with some sample data.")

# Load data from database
df = load_data(conn)

# Display data with editable table
edited_df = st.data_editor(
    df,
    disabled=["id"],  # Don't allow editing the 'id' column.
    num_rows="dynamic",  # Allow appending/deleting rows.
    column_config={
    },
    key="score_card",
)

has_uncommitted_changes = any(len(v) for v in st.session_state.score_card.values())

st.button(
    "Commit changes",
    type="primary",
    disabled=not has_uncommitted_changes,
    # Update data in database
    on_click=update_data,
    args=(conn, df, st.session_state.score_card),
)


# -----------------------------------------------------------------------------
# Now some cool charts
# -----------------------------------------------------------------------------

st.subheader("Top Scorer", divider="orange")

""
""

st.altair_chart(
    alt.Chart(df)
    .mark_bar(orient="horizontal")
    .encode(
        x="total_tops",
        y=alt.Y("contestant_name").sort("-x"),
    ),
    use_container_width=True,
)


st.subheader("Top Penalties", divider="orange")

""
""

st.altair_chart(
    alt.Chart(df)
    .mark_bar(orient="horizontal")
    .encode(
        x="total_penalty",
        y=alt.Y("contestant_name").sort("-x"),
    ),
    use_container_width=True,
)