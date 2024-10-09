import sys
import json
import time
#from itertools import chain
#from ast import literal_eval
from pprint import pprint
import requests
from openai import OpenAI
#import tiktoken

from prompts import EXTRACTION_INSTRUCTIONS, EXTRACTION_PROMPT
from minimize_html import remove_cruft


try:
    from config import OPENAI_ORG, OPENAI_PROJECT, OPENAI_KEY, OPENAI_MODEL
    client = OpenAI(
        organization=OPENAI_ORG,
        project=OPENAI_PROJECT,
        api_key=OPENAI_KEY
    )
except Exception as e:
    print(type(e), e)
    exit("Please setup OpenAI API Organization, project, keyand model within config.py such as in config.py.example")


extraction_assistant = client.beta.assistants.create(
  name="Web content extractor",
  model=OPENAI_MODEL,
  instructions=EXTRACTION_INSTRUCTIONS,
  temperature=0.1,
  response_format={"type": "json_object"},
# tools=[{"type": "functions"}],
)
extraction_thread = client.beta.threads.create()


def download_html(url):
    html_content = requests.get(url, headers={"User-Agent": "LLM Web content extractor"}).text
    return html_content


def extract_content_from_html_piece(html_piece, url, piece_index):
    result = {
        "url": url,
        "piece_index": piece_index,
        "extraction_status": None,
        "extraction_duration": None,
        "extraction_result": {}
    }

    t0 = time.time()

    message = client.beta.threads.messages.create(
        thread_id=extraction_thread.id,
        role="user",
        content=EXTRACTION_PROMPT % html_piece
    )

    run = client.beta.threads.runs.create_and_poll(
        thread_id=extraction_thread.id,
        assistant_id=extraction_assistant.id
    )

    while run.status not in ("completed", "failed"):
        time.sleep(0.1)

    result["extraction_duration"] = time.time() - t0

    if run.status == "failed":
        print("FAILED: %s" % run.last_error, file=sys.stderr)
        result["extraction_status"] = "failed"
        return result

    messages = client.beta.threads.messages.list(
        thread_id=extraction_thread.id
    )

    try:
        response = messages.data[0].content[0].text.value.replace("```json\n", "").replace("\n```", "")

        data = json.loads(response)
        result["extraction_status"] = "success"
        result["extraction_result"] = data
    except:
        print("LLM response badly formatted: %s" % messages.data, file=sys.stderr)
        result["extraction_status"] = "partial success"
        result["partial_extraction_data"] = messages.data

    return result


def process_url(url):
    html_content = download_html(url)

    clean_html = remove_cruft(html_content)

    result = extract_content_from_html_piece(clean_html, url, 0)

    pprint(result)


if __name__ == "__main__":
    process_url(sys.argv[1])
