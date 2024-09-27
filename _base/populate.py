#!/usr/bin/env python3

import os
import json
import django

# Set the Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_base.settings")  # Update with your actual project name
django.setup()

from listings.models import State, School, Region, Landmark

def create_dummy_data_from_json(json_file):
    """Create or update States, Schools, Regions, and Landmarks from a JSON file."""
    with open(json_file, 'r') as file:
        data = json.load(file)

    for state_data in data['states']:
        state_name = state_data['name']
        state, created = State.objects.get_or_create(name=state_name)
        if created:
            print(f'Created state: {state_name}')

        for school_data in state_data['schools']:
            school_name = school_data['name']
            school_abbr = school_data['abbr']
            school, created = School.objects.get_or_create(
                name=school_name,
                defaults={'abbr': school_abbr, 'state': state}
            )

            # Update school abbreviation if it already exists
            if not created and school.abbr != school_abbr:
                school.abbr = school_abbr
                school.save()
                print(f'Updated school abbreviation: {school_name} to {school_abbr}')

            for region_data in school_data['regions']:
                region_name = region_data['name']
                region, created = Region.objects.get_or_create(
                    name=region_name,
                    defaults={'school': school, 'state': state}
                )

                # If the region already exists, no update needed, but you can handle updates here if necessary
                if created:
                    print(f'Created region: {region_name} in {school_name}')

                # Create Landmarks (currently empty in JSON)
                for landmark_name in region_data['landmarks']:
                    # If there were landmarks, they would be created here
                    landmark, created = Landmark.objects.get_or_create(
                        name=landmark_name,
                        region=region,
                        state=state,
                        school=school
                    )
                    if created:
                        print(f'Created landmark: {landmark_name} in {region_name}')

if __name__ == "__main__":
    json_file_path = 'default-data'
    create_dummy_data_from_json(json_file_path)
