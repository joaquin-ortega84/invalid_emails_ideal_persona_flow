import pandas as pd
import numpy as np


# LOAD CLAY OUTPUTS

CLAY_INPUT_LEADS_PATH = '/mnt/c/Users/jortega/code/invalid_emails_ideal_persona_flow/new_sfdc_data/validated_leads_list_clay.csv'
CLAY_INPUT_CONTACTS_PATH = '/mnt/c/Users/jortega/code/invalid_emails_ideal_persona_flow/new_sfdc_data/validated_contacts_list_clay.csv'

def concatenate_people_clay():

    leads_df = pd.read_csv(CLAY_INPUT_LEADS_PATH)
    contacts_df = pd.read_csv(CLAY_INPUT_CONTACTS_PATH)

    leads_df['lead or contact'] = "lead"
    contacts_df['lead or contact'] = "contact"

    clay_people = pd.concat([leads_df, contacts_df], axis=0, ignore_index=True)


    clay_people["Related Record ID"] = np.where(
        clay_people["lead or contact"] == "lead",
        clay_people["Lead_id"],
        clay_people["Contact_id"],
    )

    clay_people = clay_people[['Related Record ID','Email', 'Status (Zerobounce)', 'Sub Status (Zerobounce)',
        'Invalid Email (Output)', 'Description (Output)', 'lead or contact']]

    clay_people['Source'] = "Clay"

    invalid_email_clay = clay_people[clay_people['Invalid Email (Output)'] == False]

    invalid_email_clay.to_csv('/mnt/c/Users/jortega/code/invalid_emails_ideal_persona_flow/silver/clay_invalid_emails.csv')

    return print(invalid_email_clay.shape)

# concatenate_people_clay()


SFDC_INPUT_LEADS_PATH = '/mnt/c/Users/jortega/code/invalid_emails_ideal_persona_flow/new_sfdc_data/invalid_emails_contacts_mass_updated.csv'
SFDC_INPUT_CONTACTS_PATH = '/mnt/c/Users/jortega/code/invalid_emails_ideal_persona_flow/new_sfdc_data/invalid_emails_leads_mass_updated.csv'

def concatenate_people_sfdc():

    leads_df = pd.read_csv(SFDC_INPUT_LEADS_PATH)
    contacts_df = pd.read_csv(SFDC_INPUT_CONTACTS_PATH)

    leads_df['lead or contact'] = "lead"
    contacts_df['lead or contact'] = "contact"

    contacts_df.rename(columns={'Account':'Account Name'}, inplace=True)

    sfdc_people = pd.concat([leads_df, contacts_df], axis=0, ignore_index=True)

    sfdc_people["Related Record ID"] = np.where(
            sfdc_people["lead or contact"] == "lead",
            sfdc_people["Lead ID"],
            sfdc_people["Contact ID"],
        )


    sfdc_people['Ideal_Persona'] = np.where(sfdc_people['Automated Persona Match'] | sfdc_people['Ideal Persona'], 'TRUE', 'FALSE')
    sfdc_people['Full Name'] = sfdc_people['First Name'] + " " + sfdc_people['Last Name']
    sfdc_people = sfdc_people.drop(columns=['First Name', 'Last Name', 'Lead ID', 'Contact ID'])

    # return print(sfdc_people[['Ideal_Persona', 'Ideal Persona', 'Automated Persona Match']].sample(7))
    return print(sfdc_people.columns)


# concatenate_people_sfdc()

def merge_clay_sfdc_people():
