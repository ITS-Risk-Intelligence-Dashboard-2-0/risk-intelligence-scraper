import os
import json

from celery import shared_task
from maizey_api.api_call import create_conversation, call_api, MaizeyImproperJson

from scraper.retrieval import retrieve_page

# TODO: add feature to disable maizey filtering (for debugging)
def filter_non_ascii(prompt):
    initial_size = len(prompt)
    new_prompt = prompt.encode("ascii", errors="ignore").decode("ascii")
    new_size = len(new_prompt)

    reduction_size = (initial_size - new_size) / initial_size
    return (reduction_size, new_prompt)

@shared_task
def maizey_filter_content(page, categories_config):
    urls, contents = page

    project_pk = os.environ.get("MAIZEY_PROJECT_PK")
    api_key = os.environ.get("MAIZEY_API_KEY")

    relevant_pages = []

    try:
        conversation_pk = create_conversation(project_pk, api_key)
        for url, content in zip(urls, contents):
            reduction, content = filter_non_ascii(content)

            # if content contains too many non-ASCII characters
            if reduction > 0.3:
                continue

            content = f"[begin] {content} [end]"
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
                    best_category = category_item["name"]

            # if best category is not in the list of categories
            if best_category not in categories_config:
                continue

            # if all the category scores are too low
            if highest_score < categories_config[best_category]["min_relevance_threshold"]:
                continue

            # append the page
            relevant_pages.append((url, (best_category, categories_config[best_category]["folder"]), content))

        return relevant_pages

    except Exception as e:
        print(e)
        return []
