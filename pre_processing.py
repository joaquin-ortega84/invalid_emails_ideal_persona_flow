import pandas as pd
import numpy as np


def to_bool(series):
    """Convert 0/1 (or 0.0/1.0) to booleans. Blanks and non-numeric values become False."""
    return pd.to_numeric(series, errors='coerce').fillna(0).astype(bool)



CLAY_INPUT_LEADS_PATH = '/mnt/c/Users/jortega/code/invalid_emails_ideal_persona_flow/raw_data/clay/validated_leads_list_clay.csv'
CLAY_INPUT_CONTACTS_PATH = '/mnt/c/Users/jortega/code/invalid_emails_ideal_persona_flow/raw_data/clay/validated_contacts_list_clay.csv'
CLAY_OUTPUT_PATH = '/mnt/c/Users/jortega/code/invalid_emails_ideal_persona_flow/bronze/clay_invalid_emails_data.csv'


CLAY_LEAD_ID_COL = 'Lead ID'
CLAY_CONTACT_ID_COL = 'Contact ID'


def get_clay_invalid_emails_concatenated():

    print('Started getting Clay invalid emails')
    leads_df = pd.read_csv(CLAY_INPUT_LEADS_PATH)
    contacts_df = pd.read_csv(CLAY_INPUT_CONTACTS_PATH)
    print('Leads df', leads_df.shape)
    print('Contacts df', contacts_df.shape)

    leads_df['lead or contact'] = 'lead'
    contacts_df['lead or contact'] = 'contact'

    clay_people = pd.concat([leads_df, contacts_df], axis=0, ignore_index=True)
    print('clay people', clay_people.shape)

    clay_people['Related Record ID'] = np.where(
        clay_people['lead or contact'] == 'lead',
        clay_people[CLAY_LEAD_ID_COL],
        clay_people[CLAY_CONTACT_ID_COL],
    )

    clay_invalid_emails = clay_people[clay_people['Invalid Email (Output)'] == True]
    print('clay invalid emails', clay_invalid_emails.shape)

    clay_invalid_emails = clay_invalid_emails[[
        'Related Record ID', 'Email', 'Status (Zerobounce)', 'Sub Status (Zerobounce)',
        'Invalid Email (Output)', 'Description (Output)', 'lead or contact',
    ]]

    clay_invalid_emails.to_csv(CLAY_OUTPUT_PATH, index=False, encoding='utf-8-sig')
    print(f"  Saved {len(clay_invalid_emails)} invalid emails to {CLAY_OUTPUT_PATH}")

    return clay_invalid_emails





# LOAD SFDC OUTPUTS

SFDC_INPUT_CONTACTS_PATH = '/mnt/c/Users/jortega/code/invalid_emails_ideal_persona_flow/raw_data/leads and contacts/contacts not disqualified.csv'
SFDC_INPUT_LEADS_PATH = '/mnt/c/Users/jortega/code/invalid_emails_ideal_persona_flow/raw_data/leads and contacts/leads_not_disqualified.csv'
SFDC_OUTPUT_PATH = '/mnt/c/Users/jortega/code/invalid_emails_ideal_persona_flow/bronze/sfdc_leads_contacts_not_disqualified.csv'


def get_sfdc_people_concatenated_not_disqualified():
    print("Loading SFDC files...")
    leads_df = pd.read_csv(SFDC_INPUT_LEADS_PATH)
    contacts_df = pd.read_csv(SFDC_INPUT_CONTACTS_PATH)

    leads_df['lead or contact'] = "lead"
    contacts_df['lead or contact'] = "contact"

    leads_df.rename(columns={'Account': 'Account Name', 'Company / Account': 'Company', 'Lead Status': 'Status', 'Create Date': 'Created Date'}, inplace=True)
    contacts_df.rename(columns={'Type': 'Account Type'}, inplace=True)

    sfdc_people = pd.concat([leads_df, contacts_df], axis=0, ignore_index=True)

    sfdc_people["Related Record ID"] = sfdc_people["Lead ID"].combine_first(sfdc_people["Contact ID"])

    sfdc_people['Ideal_Persona'] = np.where(
        to_bool(sfdc_people['Automated Persona Match']) | to_bool(sfdc_people['Ideal Persona']),
        'TRUE', 'FALSE',
    )

    # Use Company when Account Name is null or blank
    sfdc_people['Account_Name'] = (
        sfdc_people['Account Name']
        .replace(r'^\s*$', np.nan, regex=True)   # treat empty/whitespace strings as null
        .fillna(sfdc_people['Company'])
    )

    sfdc_people['Full Name'] = sfdc_people['First Name'].fillna('') + " " + sfdc_people['Last Name'].fillna('')

    # print('leads_df columns', leads_df.columns)
    # print('contacts__df columns', contacts_df.columns)
    print(sfdc_people.columns)

    sfdc_people = sfdc_people[['Full Name', 'Title', 'Job Level', 'Email', 'Last Response Date', 'Last Meeting Date', \
                'Ideal Persona', 'Automated Persona Match', 'Account Type', 'Ideal_Persona', 'Invalid Email'  ,'lead or contact', \
                'Status', 'Account_Name', 'Account Name', 'Company', 'Converted', 'Related Record ID']]

    sfdc_people.to_csv(SFDC_OUTPUT_PATH, index=False, encoding='utf-8-sig')
    print(f"  Saved {len(sfdc_people)} leads and contacts not disqualified to {SFDC_OUTPUT_PATH}")


    return sfdc_people


CLAY_PEOPLE_PATH = '/mnt/c/Users/jortega/code/invalid_emails_ideal_persona_flow/bronze/clay_invalid_emails_data.csv'
SFDC_PEOPLE_PATH = '/mnt/c/Users/jortega/code/invalid_emails_ideal_persona_flow/bronze/sfdc_leads_contacts_not_disqualified.csv'

def merge_clay_sfdc_eople_not_disqualified():

    clay_people = pd.read_csv(CLAY_PEOPLE_PATH, dtype=str)
    sfdc_people = pd.read_csv(SFDC_PEOPLE_PATH, dtype=str)


    # Clay is the base: every Clay row is kept, SFDC columns are added where IDs match
    merged_data = pd.merge(
        clay_people,
        sfdc_people,
        on='Related Record ID',
        how='left',
        suffixes=('_clay', '_sfdc'),
    )

    # Prefer the SFDC email, fall back to Clay's when there's no SFDC match
    merged_data.to_csv(
        '/mnt/c/Users/jortega/code/invalid_emails_ideal_persona_flow/silver/merged_data.csv',
        index=False,
    )

    print(f"Merged complete: {len(merged_data)} rows (Clay had {len(clay_people)})")

    return merged_data

# concatenate_people_clay_invalid()
# concatenate_people_sfdc()


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



############### Run this to ##############:

## Concatenate clay validated lists and filter for invalid emails
# get_clay_invalid_emails_concatenated()

## Get sfdc oeople concatenated and not disqualified
get_sfdc_people_concatenated_not_disqualified()
