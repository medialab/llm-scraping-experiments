import sys
import json
import time
#from itertools import chain
#from ast import literal_eval
from pprint import pprint
import requests
from openai import OpenAI, BadRequestError
import tiktoken

from prompts import SPLITTING_INSTRUCTIONS, SPLITTING_PROMPT, EXTRACTION_INSTRUCTIONS, EXTRACTION_PROMPT
from minimize_html import remove_cruft

MAX_LENGTH = 256000
MAX_TOKENS = 100000

try:
    from config import OPENAI_ORG, OPENAI_PROJECT, OPENAI_KEY, OPENAI_MODEL
    client = OpenAI(
        organization=OPENAI_ORG,
        project=OPENAI_PROJECT,
        api_key=OPENAI_KEY
    )
except Exception as e:
    print(type(e), e, file=sys.stderr)
    exit("Please setup OpenAI API Organization, project, keyand model within config.py such as in config.py.example")


extraction_assistant = client.beta.assistants.create(
  name="Web content extractor",
  model=OPENAI_MODEL,
  instructions=EXTRACTION_INSTRUCTIONS,
  temperature=0,
  response_format={"type": "json_object"},
# tools=[{"type": "functions"}],
)
extraction_thread = client.beta.threads.create()


def download_html(url):
    html_content = requests.get(url, headers={"User-Agent": "LLM Web content extractor"}).text
    return html_content


def get_tokens_len(text):
    tokenizer = tiktoken.encoding_for_model(OPENAI_MODEL)
    tokens = tokenizer.encode(text)
    tokens_len = len(tokens)
    return(tokens_len)


## Function for truncating content (LLM might not need full content to ascertain relevance)
def truncate_content(data, max_length):
    if isinstance(data, dict):
        # If the current element is a dictionary, recursively process its values
        return {key: truncate_content(value, max_length) for key, value in data.items()}
    elif isinstance(data, list):
        # If the current element is a list, recursively process its elements
        return [truncate_content(item, max_length) for item in data]
    elif isinstance(data, str):
        # If the current element is a string, truncate it
        return data[:max_length]
    # If it's not a dict, list, or string, return it as-is (e.g., numbers)
    return data


def extract_content_from_html_piece(html_piece, url, piece_index):
    result = {
        "url": url,
        "piece_index": piece_index,
        "extraction_status": None,
        "extraction_duration": None,
        "extraction_result": {}
    }

    t0 = time.time()

    try:
        message = client.beta.threads.messages.create(
            thread_id=extraction_thread.id,
            role="user",
            content=EXTRACTION_PROMPT % html_piece
        )
    except BadRequestError as e:
        print("%s: %s" % (type(e), e))
        result["extraction_status"] = "failed"
        result["extraction_error"] = e.body
        return result

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
        result["extraction_error"] = run.last_error
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
        print("WARNING: LLM response badly formatted", file=sys.stderr)
        result["extraction_status"] = "partial success"
        result["partial_extraction_data"] = messages.data

    return result


def process_url(url):
    html_content = download_html(url)

    clean_html = remove_cruft(html_content)

    if len(clean_html) + len(SPLITTING_PROMPT) > MAX_LENGTH:
        print("WARNING: HTML string too long (%s for max %s), truncating it..." % (len(clean_html), MAX_LENGTH - len(SPLITTING_PROMPT)))
    clean_html = truncate_content(clean_html, MAX_LENGTH - len(SPLITTING_PROMPT))

    tokens_length = get_tokens_len(clean_html)
    if tokens_length > MAX_TOKENS:
        exit("too many tokens: %s" % (tokens_length, MAX_TOKENS))

    result = extract_content_from_html_piece(clean_html, url, 0)

    pprint(result, width=200, sort_dicts=False)


if __name__ == "__main__":
    process_url(sys.argv[1])
