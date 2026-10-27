import os
import pandas as pd
import numpy as np

RAW_DATA = '/mnt/c/Users/jortega/code/invalid_emails_ideal_persona_flow/raw_data'
BRONZE   = '/mnt/c/Users/jortega/code/invalid_emails_ideal_persona_flow/bronze'
SILVER   = '/mnt/c/Users/jortega/code/invalid_emails_ideal_persona_flow/silver'
GOLD     = '/mnt/c/Users/jortega/code/invalid_emails_ideal_persona_flow/gold'

WINDOW_DAYS = 90


def get_activity_check_data():

    clay_augmented = pd.read_csv(f'{SILVER}/augmented_clay.csv', dtype=str)
    engagements    = pd.read_csv(f'{BRONZE}/grouped_engagements.csv', dtype=str)
    inbound_emails = pd.read_csv(f'{BRONZE}/inbound_reply_activities.csv', dtype=str, encoding='utf-8-sig')
    contact_roles  = pd.read_csv(f'{RAW_DATA}/contact roles/contact_roles.csv', dtype=str)

    # --- Clean keys ---
    clay_augmented['Email'] = clay_augmented['Email'].str.strip().str.lower()
    engagements['Related Record ID'] = engagements['Related Record ID'].str.strip().str[:15]  # 18 -> 15

    # --- Contact roles: just the contact ID, one row each, with a flag ---
    contact_roles = (
        contact_roles[['Contact ID']]
        .rename(columns={'Contact ID': 'Related Record ID'})
        .dropna()
        .drop_duplicates()
    )
    contact_roles['has_contact_role'] = 1

    # --- Inbound replies: one row per email ---
    inbound_emails['Email'] = inbound_emails['From Address'].str.strip().str.lower()
    inbound_emails['Created Date'] = pd.to_datetime(inbound_emails['Created Date'], errors='coerce')

    inbound_summary = (
        inbound_emails
        .dropna(subset=['Email'])
        .sort_values('Created Date')
        .groupby('Email')
        .agg(
            Last_Reply_Date=('Created Date', 'max'),
            Reply_Count=('Email', 'size'),
            Last_Reply_Subject=('Subject', 'last'),
            Reply_Source=('Source', 'last'),
        )
        .reset_index()
    )

    # --- Merge everything onto the Clay base ---
    final_result = (
        clay_augmented
        .merge(engagements, on='Related Record ID', how='left', validate='many_to_one')
        .merge(inbound_summary, on='Email', how='left', validate='many_to_one')
        .merge(contact_roles, on='Related Record ID', how='left', validate='many_to_one')
    )

    assert len(final_result) == len(clay_augmented), "Row count changed during merge"

    final_result['has_contact_role'] = final_result['has_contact_role'].fillna(0).astype(int)

    print(f"Clay rows: {len(clay_augmented)} | final_result: {len(final_result)}")
    print(f"With an engagement: {final_result['Engagement_Date'].notna().sum()}")
    print(f"With an inbound reply: {final_result['Last_Reply_Date'].notna().sum()}")
    print(f"With a contact role: {(final_result['has_contact_role'] == 1).sum()}")

    # --- Day counts ---
    today = pd.Timestamp.today().normalize()

    final_result['Engagement_Date']   = pd.to_datetime(final_result['Engagement_Date'], errors='coerce')
    final_result['Last_Reply_Date']   = pd.to_datetime(final_result['Last_Reply_Date'], errors='coerce')
    final_result['Last Meeting Date'] = pd.to_datetime(final_result['Last Meeting Date'], errors='coerce')

    final_result['days_since_engagement']    = (today - final_result['Engagement_Date']).dt.days
    final_result['days_since_inbound_reply'] = (today - final_result['Last_Reply_Date']).dt.days
    final_result['days_since_last_meeting']  = (today - final_result['Last Meeting Date']).dt.days

    # --- Disqualify logic: first matching condition wins ---
    conditions = [
        final_result['days_since_engagement']    < WINDOW_DAYS,
        final_result['days_since_inbound_reply'] < WINDOW_DAYS,
        final_result['days_since_last_meeting']  < WINDOW_DAYS,
        final_result['has_contact_role'] == 1,
    ]
    reasons = ['engagement', 'inbound reply', 'meeting happened', 'contact role in oppy']

    final_result['Disqualify Reason'] = np.select(conditions, reasons, default='failed activity check')
    final_result['Disqualified'] = final_result['Disqualify Reason'] == 'failed activity check'

    print(final_result['Disqualify Reason'].value_counts())

    os.makedirs(GOLD, exist_ok=True)
    final_result.to_csv(
        f'{GOLD}/clay_augmented_post_activity_check.csv',
        index=False,
        encoding='utf-8-sig',
    )
    print(f"Saved to {GOLD}/clay_augmented_post_activity_check.csv")

    return final_result
