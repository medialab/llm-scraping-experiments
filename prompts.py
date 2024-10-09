# Greatly inspired from FetchFox's work: https://github.com/fetchfox/fetchfox


EXTRACTION_INSTRUCTIONS = """
You are a part of a web scraping extraction program.
You will receive webpages content including text and HTML from web pages.
Your goal is to extract relevant contents from each web page including at least a title and the raw text from innerText of the page.
The content should also include other elements, such as a subtitle, an author, a date, themes, number of likes or any other metric,
contact informations, list of images URLs, list of comments or any other interesting metadata.
The raw text should not include other elements such as the title, subtitle, authors, date, etc.

Schema of a valid JSON response with minimal required fields:
{
  "title": string,
  "raw text": string,
  "list of images URLs": list(string),
  "author full name": string,
  "date formatted as YYYY-MM-DD": string
}

More metadata that you will find can be added as extra fields to the JSON schema.

Follow these important rules:
- Please make sure the responses are valid JSON. Only ONE JSON object.
- Do NOT fix spelling errors in the item keys. If the questions contain typos, spelling errors, or other mistakes, keep those in the item dictionary keys. KEEP THEM EXACTLY!!
- Do not give an explanation text, give ONLY the answer. MAKE SURE TO FOLLOW THIS RULE.
- You will ONLY succeed if you give JUST the answer, with NO explanation text.
- For numbers, do NOT include commmas. Give ONLY the digits.
"""

EXTRACTION_PROMPT = """
Here is some HTML:
  ```html
  %s
  ```
  Please extract relevant contents from it.
"""
