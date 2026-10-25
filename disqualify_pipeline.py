"""
Lead + Contact disqualification pipeline.

Combines leads and contacts into one dataset and decides whether each record
should be disqualified.

A record is KEPT if ANY of these is true:
  - Last Response Date is within CUTOFF_DAYS of TODAY
  - Last Meeting Date is within CUTOFF_DAYS of TODAY
  - Its email is the From Address of an incoming Outlook reply (export has no dates)
  - It appears in the Outreach inbound-reply export (export has no dates)
  - It is a contact role on an open opportunity (contacts only; every row in the file is open)

Otherwise Should_Disqualify = "Yes".

Usage: python3 disqualify_pipeline.py
Edit INPUT_DIR / OUTPUT_DIR below if your files live elsewhere.
"""

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
INPUT_DIR = "new_sfdc_data"
OUTPUT_DIR = "."
TODAY = pd.Timestamp("2026-10-23")
CUTOFF_DAYS = 90

OUTPUT_FILE = f"{OUTPUT_DIR}/combined_leads_contacts.csv"

# ---------------------------------------------------------------------------
# Read inputs (values as exported; email columns lowercased)
# ---------------------------------------------------------------------------
contacts = pd.read_csv(f"{INPUT_DIR}/invalid_emails_contacts_mass_updated.csv", dtype=str, keep_default_na=False).replace("", np.nan)
leads = pd.read_csv(f"{INPUT_DIR}/invalid_emails_leads_mass_updated.csv", dtype=str, keep_default_na=False).replace("", np.nan)
contact_roles = pd.read_csv(f"{INPUT_DIR}/contact_roles_opportunities.csv", dtype=str, keep_default_na=False).replace("", np.nan)
outlook = pd.read_csv(f"{INPUT_DIR}/inbound_reply_outlook_leads_contacts.csv", dtype=str, keep_default_na=False).replace("", np.nan)
outreach_leads = pd.read_csv(f"{INPUT_DIR}/inbound_reply_outreach_leads.csv", dtype=str, keep_default_na=False).replace("", np.nan)
outreach_contacts = pd.read_csv(f"{INPUT_DIR}/inbound_reply_outreach_contacts.csv", dtype=str, keep_default_na=False).replace("", np.nan)

contacts["Email"] = contacts["Email"].str.lower()
leads["Email"] = leads["Email"].str.lower()
contact_roles["Email"] = contact_roles["Email"].str.lower()
outlook["From Address"] = outlook["From Address"].str.lower()
outreach_leads["Email"] = outreach_leads["Email"].str.lower()

# ---------------------------------------------------------------------------
# Combine leads and contacts
# ---------------------------------------------------------------------------
c_df = pd.DataFrame({
    "Record_Source": "Contact",
    "Record_ID": contacts["Contact ID"],
    "First Name": contacts["First Name"],
    "Last Name": contacts["Last Name"],
    "Title": contacts["Title"],
    "Email": contacts["Email"],
    "Account": contacts["Account Name"],
    "Status_or_Type": contacts["Type"],
    "Ideal Persona": contacts["Ideal Persona"],
    "Automated Persona Match": contacts["Automated Persona Match"],
    "Last Response Date": contacts["Last Response Date"],
    "Last Meeting Date": contacts["Last Meeting Date"],
})
l_df = pd.DataFrame({
    "Record_Source": "Lead",
    "Record_ID": leads["Lead ID"],
    "First Name": leads["First Name"],
    "Last Name": leads["Last Name"],
    "Title": leads["Title"],
    "Email": leads["Email"],
    "Account": leads["Company / Account"],
    "Status_or_Type": leads["Lead Status"],
    "Ideal Persona": leads["Ideal Persona"],
    "Automated Persona Match": leads["Automated Persona Match"],
    "Last Response Date": leads["Last Response Date"],
    "Last Meeting Date": leads["Last Meeting Date"],
})
df = pd.concat([c_df, l_df], ignore_index=True)
is_lead = df["Record_Source"] == "Lead"

# ---------------------------------------------------------------------------
# Persona flag: True when either persona column is 1
# ---------------------------------------------------------------------------
df["Combined Ideal Persona"] = (
    pd.to_numeric(df["Ideal Persona"], errors="coerce").fillna(0).eq(1)
    | pd.to_numeric(df["Automated Persona Match"], errors="coerce").fillna(0).eq(1)
)

# ---------------------------------------------------------------------------
# Days since last response / meeting (today minus the date)
# ---------------------------------------------------------------------------
df["Days Since Last Response"] = (TODAY - pd.to_datetime(df["Last Response Date"], format="%m/%d/%Y", errors="coerce")).dt.days
df["Days Since Last Meeting"] = (TODAY - pd.to_datetime(df["Last Meeting Date"], format="%m/%d/%Y", errors="coerce")).dt.days
recent_response = df["Days Since Last Response"].between(0, CUTOFF_DAYS)
recent_meeting = df["Days Since Last Meeting"].between(0, CUTOFF_DAYS)

# ---------------------------------------------------------------------------
# Outlook inbound replies (matched on From Address; export has no dates)
# ---------------------------------------------------------------------------
incoming = outlook[outlook["Is Incoming"].astype(str) == "1"]
outlook_counts = incoming["From Address"].value_counts()
df["Outlook Inbound Replies"] = df["Email"].map(outlook_counts).fillna(0).astype(int)
outlook_reply = df["Outlook Inbound Replies"] > 0

# ---------------------------------------------------------------------------
# Outreach inbound replies (leads by Lead ID or Email; contacts by First + Last Name)
# ---------------------------------------------------------------------------
o_lead_ids = set(outreach_leads["Lead ID"].dropna())
o_lead_emails = set(outreach_leads["Email"].dropna())
o_contact_names = set(
    (outreach_contacts["First Name"].fillna("") + " " + outreach_contacts["Last Name"].fillna("")).str.strip()
) - {""}
full_name = (df["First Name"].fillna("") + " " + df["Last Name"].fillna("")).str.strip()
outreach_reply = pd.Series(np.where(
    is_lead,
    df["Record_ID"].isin(o_lead_ids) | df["Email"].isin(o_lead_emails),
    full_name.isin(o_contact_names) & (full_name != ""),
), index=df.index)

# ---------------------------------------------------------------------------
# Contact role on an open opportunity (contacts only; every row in file is open)
# ---------------------------------------------------------------------------
opp_by_contact = (
    contact_roles.dropna(subset=["Contact ID"])
    .groupby("Contact ID")["Opportunity Name"]
    .agg(lambda x: "; ".join(sorted(set(x.dropna()))))
)
open_role = (~is_lead) & df["Record_ID"].isin(opp_by_contact.index)
df["Open Opportunities (contact role)"] = np.where(open_role, df["Record_ID"].map(opp_by_contact), "")

# ---------------------------------------------------------------------------
# Decision and reason
# ---------------------------------------------------------------------------
keep = recent_response | recent_meeting | outlook_reply | outreach_reply | open_role
df["Should_Disqualify"] = np.where(keep, "No", "Yes")

reason = pd.Series("", index=df.index)
for cond, text in [
    (recent_response, "Last response " + df["Days Since Last Response"].fillna(-1).astype(int).astype(str) + " days ago"),
    (recent_meeting, "Last meeting " + df["Days Since Last Meeting"].fillna(-1).astype(int).astype(str) + " days ago"),
    (outlook_reply, "Inbound reply via Outlook (undated)"),
    (outreach_reply, "Inbound reply via Outreach (undated)"),
    (open_role, "Contact role on open opportunity"),
]:
    reason = reason.where(~cond, reason.where(reason == "", reason + "; ") + text)

df["Reason"] = np.where(
    keep,
    reason,
    f"No response or meeting in last {CUTOFF_DAYS} days, no inbound reply, not an open opportunity contact role",
)

# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
out_cols = [
    "Record_Source", "Record_ID", "First Name", "Last Name", "Title", "Email", "Account",
    "Status_or_Type", "Ideal Persona", "Automated Persona Match", "Combined Ideal Persona",
    "Last Response Date", "Days Since Last Response",
    "Last Meeting Date", "Days Since Last Meeting",
    "Outlook Inbound Replies", "Open Opportunities (contact role)",
    "Should_Disqualify", "Reason",
]
df[out_cols].to_csv(OUTPUT_FILE, index=False)

summary = df.groupby("Record_Source")["Should_Disqualify"].value_counts().unstack(fill_value=0)
print(summary.to_string())
print(f"Total records: {len(df)}")
print(f"Written to: {OUTPUT_FILE}")
