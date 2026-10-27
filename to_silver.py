import pandas as pd

CLAY_PEOPLE_PATH = '/mnt/c/Users/jortega/code/invalid_emails_ideal_persona_flow/bronze/clay_invalid_emails_data.csv'
SFDC_PEOPLE_PATH = '/mnt/c/Users/jortega/code/invalid_emails_ideal_persona_flow/bronze/sfdc_leads_contacts_not_disqualified.csv'
MERGED_DATA_PATH = '/mnt/c/Users/jortega/code/invalid_emails_ideal_persona_flow/silver/clay_augmented_data.csv'

def augment_clay_with_sfdc():

    clay_people = pd.read_csv(CLAY_PEOPLE_PATH, dtype=str)
    sfdc_people = pd.read_csv(SFDC_PEOPLE_PATH, dtype=str)

    # Clay is the base: every Clay row is kept, SFDC columns are added where IDs match
    augmented_clay = pd.merge(
        clay_people,
        sfdc_people,
        on='Related Record ID',
        how='left',
        suffixes=('_clay', '_sfdc'),
    )

    # Prefer the SFDC email, fall back to Clay's when there's no SFDC match
    augmented_clay.to_csv(
        '/mnt/c/Users/jortega/code/invalid_emails_ideal_persona_flow/silver/augmented_caly_data_with_sfdc.csv',
        index=False,
    )

    print(f"Merged complete: {len(augmented_clay)} rows (Clay had {len(clay_people)})")

    return augmented_clay

augment_clay_with_sfdc()



import pandas as pd

INBOUND_DIR = '/mnt/c/Users/jortega/code/invalid_emails_ideal_persona_flow/raw_data/inbound reply'  # adjust to where this folder lives
BRONZE = '/mnt/c/Users/jortega/code/invalid_emails_ideal_persona_flow/bronze'

def concatenate_inbound_reply():

    outlook_all       = pd.read_csv(f'{INBOUND_DIR}/inbound_reply_outlook.csv')
    outreach_contacts = pd.read_csv(f'{INBOUND_DIR}/inbound_reply_outreach_contacts.csv')
    outreach_leads    = pd.read_csv(f'{INBOUND_DIR}/inbound_reply_outreach_leads.csv')

    outlook_all['Source']       = 'outlook leads and contacts'
    outreach_contacts['Source'] = 'outreach contacts'
    outreach_leads['Source']    = 'outreach leads'

    inbound_emails = pd.concat(
        [outreach_leads, outreach_contacts, outlook_all],
        axis=0,
        ignore_index=True,
    )

    print(f"Leads: {len(outreach_leads)} | Contacts: {len(outreach_contacts)} | Outlook: {len(outlook_all)}")
    print(f"Combined: {len(inbound_emails)} rows")

    inbound_emails.to_csv(
        f'{BRONZE}/inbound_reply_activities.csv',
        index=False,
        encoding='utf-8-sig',
    )

    return inbound_emails

# concatenate_inbound_reply()
