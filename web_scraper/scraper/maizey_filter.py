import os
import json

from celery import shared_task
from maizey_api.api_call import create_conversation, call_api, MaizeyImproperJson

from scraper.retrieval import retrieve_page

# TODO: add feature to disable maizey filtering (for debugging)

@shared_task
def maizey_filter_content(page):
    urls, contents = page

    project_pk = os.environ.get("MAIZEY_PROJECT_PK")
    api_key = os.environ.get("MAIZEY_API_KEY")

    try:
        """conversation_pk = create_conversation(project_pk, api_key)
        response = call_api(project_pk, conversation_pk, api_key, content)

        json_response = json.loads(response)

        if type(json_response) is not list:
            raise MaizeyImproperJson(f"Error: Maizey filter returned improper json format {json_response}")

        highest_score = 0
        best_category = ""
        for category_item in json_response:
            if type(category_item) is not dict:
                raise MaizeyImproperJson(f"Error: Maizey filter returned improper json format {json_response}")

            if category_item.get("name") is None or category_item.get("confidence") is None:
                raise MaizeyImproperJson(f"Error: Maizey filter returned improper json format {json_response}")

            if category_item["confidence"] > highest_score:
                highest_score = category_item["confidence"]
                best_category = category_item["name"]"""

        #if highest_score < 0.8:
            #return None

        return urls

    except Exception as e:
        print(e)
        return None
