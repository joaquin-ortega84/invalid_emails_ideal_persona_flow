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
    print('Started concatenation of clay invalid emails')
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
SFDC_INPUT_LEADS_PATH = '/mnt/c/Users/jortega/code/invalid_emails_ideal_persona_flow/raw_data/leads and contacts/leads not disqualified.csv'
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



    sfdc_people = sfdc_people[['Full Name', 'Title', 'Job Level', 'Last Response Date', 'Last Meeting Date', \
                'Ideal Persona', 'Automated Persona Match', 'Account Type', 'Ideal_Persona', 'Invalid Email'  ,'lead or contact', \
                'Status', 'Account_Name', 'Account Name', 'Company', 'Converted', 'Related Record ID']]

    sfdc_people.to_csv(SFDC_OUTPUT_PATH, index=False, encoding='utf-8-sig')
    print(f"  Saved {len(sfdc_people)} leads and contacts not disqualified to {SFDC_OUTPUT_PATH}")


    return sfdc_people




############### Run this to ##############:

## Concatenate clay validated lists and filter for invalid emails
get_clay_invalid_emails_concatenated()

## Get sfdc oeople concatenated and not disqualified
get_sfdc_people_concatenated_not_disqualified()
