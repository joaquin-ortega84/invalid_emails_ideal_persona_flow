import pandas as pd
import numpy as np


def to_bool(series):
    """Convert 0/1 (or 0.0/1.0) to booleans. Blanks and non-numeric values become False."""
    return pd.to_numeric(series, errors='coerce').fillna(0).astype(bool)


# LOAD CLAY OUTPUTS

CLAY_INPUT_LEADS_PATH = '/mnt/c/Users/jortega/code/invalid_emails_ideal_persona_flow/raw_data/validated_leads_list_clay.csv'
CLAY_INPUT_CONTACTS_PATH = '/mnt/c/Users/jortega/code/invalid_emails_ideal_persona_flow/raw_data/validated_contacts_list_clay.csv'
CLAY_OUTPUT_PATH = '/mnt/c/Users/jortega/code/invalid_emails_ideal_persona_flow/bronze/clay_validated_list.csv'


def concatenate_people_clay():
    print("Loading Clay files...")
    leads_df = pd.read_csv(CLAY_INPUT_LEADS_PATH)
    contacts_df = pd.read_csv(CLAY_INPUT_CONTACTS_PATH)
    print(f"  Leads: {len(leads_df)} rows | Contacts: {len(contacts_df)} rows")

    leads_df['lead or contact'] = "lead"
    contacts_df['lead or contact'] = "contact"

    clay_people = pd.concat([leads_df, contacts_df], axis=0, ignore_index=True)

    clay_people["Related Record ID"] = np.where(
        clay_people["lead or contact"] == "lead",
        clay_people["Lead_id"],
        clay_people["Contact_id"],
    )

    clay_people = clay_people[['Related Record ID', 'Email', 'Status (Zerobounce)', 'Sub Status (Zerobounce)',
                               'Invalid Email (Output)', 'Description (Output)', 'lead or contact']]

    clay_people['Source'] = "Clay"


    clay_people.to_csv(CLAY_OUTPUT_PATH, index=False)
    print(f"  Saved to {CLAY_OUTPUT_PATH}")

    return clay_people


# LOAD SFDC OUTPUTS

SFDC_INPUT_LEADS_PATH = '/mnt/c/Users/jortega/code/invalid_emails_ideal_persona_flow/raw_data/invalid_emails_leads.csv'
SFDC_INPUT_CONTACTS_PATH = '/mnt/c/Users/jortega/code/invalid_emails_ideal_persona_flow/raw_data/invalid_emails_contacts' \
'.csv'
SFDC_OUTPUT_PATH = '/mnt/c/Users/jortega/code/invalid_emails_ideal_persona_flow/bronze/sfdc_people.csv'


def concatenate_people_sfdc():
    print("Loading SFDC files...")
    leads_df = pd.read_csv(SFDC_INPUT_LEADS_PATH)
    contacts_df = pd.read_csv(SFDC_INPUT_CONTACTS_PATH)
    print(f"  Leads: {len(leads_df)} rows | Contacts: {len(contacts_df)} rows")

    leads_df['lead or contact'] = "lead"
    contacts_df['lead or contact'] = "contact"

    contacts_df.rename(columns={'Account': 'Account Name'}, inplace=True)

    sfdc_people = pd.concat([leads_df, contacts_df], axis=0, ignore_index=True)

    sfdc_people["Related Record ID"] = np.where(
        sfdc_people["lead or contact"] == "lead",
        sfdc_people["Lead ID"],
        sfdc_people["Contact ID"],
    )

    sfdc_people['Ideal_Persona'] = np.where(
        to_bool(sfdc_people['Automated Persona Match']) | to_bool(sfdc_people['Ideal Persona']),
        'TRUE', 'FALSE',
    )
    sfdc_people['Full Name'] = sfdc_people['First Name'].fillna('') + " " + sfdc_people['Last Name'].fillna('')
    sfdc_people = sfdc_people.drop(columns=['First Name', 'Last Name', 'Lead ID', 'Contact ID'])

    print(f"  Combined: {len(sfdc_people)} rows | Ideal_Persona TRUE: {(sfdc_people['Ideal_Persona'] == 'TRUE').sum()}")

    sfdc_people.to_csv(SFDC_OUTPUT_PATH, index=False)
    print(f"  Saved to {SFDC_OUTPUT_PATH}")

    return sfdc_people


CLAY_PEOPLE_PATH = '/mnt/c/Users/jortega/code/invalid_emails_ideal_persona_flow/bronze/clay_validated_list.csv'
SFDC_PEOPLE_PATH = '/mnt/c/Users/jortega/code/invalid_emails_ideal_persona_flow/bronze/sfdc_people.csv'

def merge_clay_sfdc_people():

    clay_people = pd.read_csv(CLAY_PEOPLE_PATH, dtype=str)
    sfdc_people = pd.read_csv(SFDC_PEOPLE_PATH, dtype=str)

    for df in (clay_people, sfdc_people):
        df['Related Record ID'] = df['Related Record ID'].str.strip()

    # Keep only the Clay columns you need, and leave out Email so the SFDC one is used
    clay_people = clay_people.drop(columns=['Email', 'lead or contact'])

    merged_data = pd.merge(sfdc_people, clay_people, on='Related Record ID', how='left')
    merged_data.to_csv(
        '/mnt/c/Users/jortega/code/invalid_emails_ideal_persona_flow/silver/merged_data.csv',
        index=False,
    )

    print('Merged complete')

    return merged_data



MERGED_DATA_PATH = '/mnt/c/Users/jortega/code/invalid_emails_ideal_persona_flow/silver/merged_data.csv'

def get_invalid_emails():

    invalid_emails = pd.read_csv(MERGED_DATA_PATH)

    print(invalid_emails.columns)

    return None








if __name__ == "__main__":
    print("=== Clay ===")
    clay_concat = concatenate_people_clay()

    print("\n=== SFDC ===")
    sfdc_concat = concatenate_people_sfdc()

    print("\nDone.")
    print(f"Clay people: {len(clay_concat)} rows | SFDC people: {len(sfdc_concat)} rows")

    print("=== SFDC & Clay ")
    merged_data = (merge_clay_sfdc_people())
    print("=== SFDC & Clay data is now merged===")

    print("===Get invalid emails across")
    get_invalid_emails()
