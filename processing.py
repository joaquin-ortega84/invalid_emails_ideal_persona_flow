import pandas as pd
import numpy as np


def to_bool(series):
    """Convert 0/1 (or 0.0/1.0) to booleans. Blanks and non-numeric values become False."""
    return pd.to_numeric(series, errors='coerce').fillna(0).astype(bool)


# LOAD CLAY OUTPUTS

CLAY_INPUT_LEADS_PATH = '/mnt/c/Users/jortega/code/invalid_emails_ideal_persona_flow/raw_data/validated_leads_list_clay.csv'
CLAY_INPUT_CONTACTS_PATH = '/mnt/c/Users/jortega/code/invalid_emails_ideal_persona_flow/raw_data/validated_contacts_list_clay.csv'
CLAY_OUTPUT_PATH = '/mnt/c/Users/jortega/code/invalid_emails_ideal_persona_flow/bronze/clay_invalid_emails_true.csv'


CLAY_LEAD_ID_COL = 'Lead ID'        # change to your renamed column
CLAY_CONTACT_ID_COL = 'Contact ID'  # change to your renamed column


def concatenate_people_clay_invalid():
    leads_df = pd.read_csv(CLAY_INPUT_LEADS_PATH)
    contacts_df = pd.read_csv(CLAY_INPUT_CONTACTS_PATH)

    leads_df['lead or contact'] = 'lead'
    contacts_df['lead or contact'] = 'contact'

    clay_people = pd.concat([leads_df, contacts_df], axis=0, ignore_index=True)

    clay_people['Related Record ID'] = np.where(
        clay_people['lead or contact'] == 'lead',
        clay_people[CLAY_LEAD_ID_COL],
        clay_people[CLAY_CONTACT_ID_COL],
    )

    clay_invalid_email = clay_people[to_bool(clay_people['Invalid Email (Output)'])].copy()

    clay_invalid_email = clay_invalid_email[[
        'Related Record ID', 'Email', 'Status (Zerobounce)', 'Sub Status (Zerobounce)',
        'Invalid Email (Output)', 'Description (Output)', 'lead or contact',
    ]]

    clay_invalid_email.to_csv(CLAY_OUTPUT_PATH, index=False)
    print(f"  Saved {len(clay_invalid_email)} invalid rows to {CLAY_OUTPUT_PATH}")

    return clay_invalid_email


# LOAD SFDC OUTPUTS

SFDC_INPUT_LEADS_PATH = '/mnt/c/Users/jortega/code/invalid_emails_ideal_persona_flow/raw_data/sfdc_invalid_emails_leads.csv'
SFDC_INPUT_CONTACTS_PATH = '/mnt/c/Users/jortega/code/invalid_emails_ideal_persona_flow/raw_data/sfdc_invalid_emails_contacts.csv'
SFDC_OUTPUT_PATH = '/mnt/c/Users/jortega/code/invalid_emails_ideal_persona_flow/bronze/sfdc_people.csv'


def concatenate_people_sfdc():
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
    sfdc_people['Full Name'] = sfdc_people['First Name'].fillna('') + " " + sfdc_people['Last Name'].fillna('')
    sfdc_people = sfdc_people.drop(columns=['First Name', 'Last Name', 'Lead ID', 'Contact ID'])

    print(f"  Combined: {len(sfdc_people)} rows | Ideal_Persona TRUE: {(sfdc_people['Ideal_Persona'] == 'TRUE').sum()}")

    # print('leads_df columns', leads_df.columns)
    # print('contacts__df columns', contacts_df.columns)
    print(sfdc_people.columns)

    sfdc_people = sfdc_people[['Full Name', 'Title', 'Job Level', 'Email', 'Last Response Date', 'Last Meeting Date', \
                'Ideal Persona', 'Automated Persona Match', 'Account Type', 'Ideal_Persona', 'Invalid Email'  ,'lead or contact', \
                'Status', 'Account Name', 'Company', 'Converted', 'Related Record ID']]

    sfdc_people.to_csv('/mnt/c/Users/jortega/code/invalid_emails_ideal_persona_flow/bronze/sfdc_people_list.csv')

    return sfdc_people


CLAY_PEOPLE_PATH = '/mnt/c/Users/jortega/code/invalid_emails_ideal_persona_flow/bronze/clay_validated_list.csv'
SFDC_PEOPLE_PATH = '/mnt/c/Users/jortega/code/invalid_emails_ideal_persona_flow/bronze/sfdc_people_list.csv'

def merge_clay_sfdc_people():

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
concatenate_people_sfdc()
