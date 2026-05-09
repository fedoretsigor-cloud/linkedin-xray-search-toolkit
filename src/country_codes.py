import re

import pycountry

from src.text_utils import clean_text


def split_location_parts(location):
    return [
        clean_text(part)
        for part in re.split(r"[,;/\n]+", clean_text(location))
        if clean_text(part)
    ]


def lookup_country(value):
    text = clean_text(value)
    if not text:
        return None
    try:
        return pycountry.countries.lookup(text)
    except LookupError:
        return None


def country_metadata_from_target_locations(target_locations):
    first_location = clean_text((target_locations or [""])[0])
    if not first_location:
        return None

    parts = split_location_parts(first_location)
    # Only country-level searches may use linkedin country subdomains as proof.
    # City-level searches still need city evidence from the profile/snippet.
    if len(parts) != 1:
        return None

    country = lookup_country(parts[0])
    if not country:
        return None

    return {
        "location_type": "Country",
        "location_name": country.name,
        "country_iso_code": country.alpha_2,
        "source": "local_country_code",
    }
