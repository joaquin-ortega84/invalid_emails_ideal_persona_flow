import pandas as pd

CLAY_PEOPLE_PATH = '/mnt/c/Users/jortega/code/invalid_emails_ideal_persona_flow/bronze/clay_invalid_emails_data.csv'
SFDC_PEOPLE_PATH = '/mnt/c/Users/jortega/code/invalid_emails_ideal_persona_flow/bronze/sfdc_leads_contacts_not_disqualified.csv'
MERGED_DATA_PATH = '/mnt/c/Users/jortega/code/invalid_emails_ideal_persona_flow/silver/clay_augmented_data.csv'
ACCOUNTS_DATA_PATH = '/mnt/c/Users/jortega/code/invalid_emails_ideal_persona_flow/raw_data/accounts/all accounts.csv'
OUTPUT_PATH_AUGMENTED_CLAY = '/mnt/c/Users/jortega/code/invalid_emails_ideal_persona_flow/silver/augmented_clay.csv'

def augment_clay_with_sfdc():

    clay_people = pd.read_csv(CLAY_PEOPLE_PATH, dtype=str)
    sfdc_people = pd.read_csv(SFDC_PEOPLE_PATH, dtype=str)
    accounts = pd.read_csv(ACCOUNTS_DATA_PATH, dtype=str)

    accounts['Account_Name'] = accounts['Account Name']

    accounts = accounts.dropna(subset=['Account_Name']).drop_duplicates(subset=['Account_Name'])

    # --- Clay is the base: every Clay row is kept ---
    augmented_with_people_data = pd.merge(
        clay_people,
        sfdc_people,
        on='Related Record ID',
        how='left',
        suffixes=('_clay', '_sfdc'),
    )

    augmented_clay_plus_accounts = pd.merge(
        augmented_with_people_data,
        accounts,
        on='Account_Name',
        how='left',
        suffixes=('', '_account'),
        validate='many_to_one',
    )

    print(f"Merged complete: {len(augmented_clay_plus_accounts)} rows (Clay had {len(clay_people)})")

    augmented_clay_plus_accounts.to_csv(
        OUTPUT_PATH_AUGMENTED_CLAY, index=False, encoding='utf-8-sig'
    )
    print(f"Saved to {OUTPUT_PATH_AUGMENTED_CLAY}")

    return augmented_clay_plus_accounts

augment_clay_with_sfdc()

import pandas as pd

INBOUND_DIR = '/mnt/c/Users/jortega/code/invalid_emails_ideal_persona_flow/raw_data/inbound reply'  # adjust to where this folder lives
BRONZE = '/mnt/c/Users/jortega/code/invalid_emails_ideal_persona_flow/bronze'

def concatenate_inbound_reply():

    outlook_all       = pd.read_csv(f'{INBOUND_DIR}/inbound_reply_outlook.csv')
    outreach_contacts = pd.read_csv(f'{INBOUND_DIR}/inbound_reply_outreach_contacts.csv')
    outreach_leads    = pd.read_csv(f'{INBOUND_DIR}/inbound_reply_outreach_leads.csv')

    outlook_all['Email'] = outlook_all['From Address']

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

concatenate_inbound_reply()
