from pre_processing import get_clay_invalid_emails_concatenated, get_sfdc_people_concatenated_not_disqualified
from to_silver import augment_clay_with_sfdc, concatenate_inbound_reply
from to_gold import get_activity_check_data



############### Run this to ##############:

# Concatenate clay validated lists and filter for invalid emails
get_clay_invalid_emails_concatenated()

## Get sfdc oeople concatenated and not disqualified
get_sfdc_people_concatenated_not_disqualified()

## Augment clay with sfdc people and accounts data
augment_clay_with_sfdc()

## concatenate inbound replies
concatenate_inbound_reply()

## run against activity check()
get_activity_check_data()
