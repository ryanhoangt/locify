import json
import os
from collections import namedtuple

from dotenv import load_dotenv
from litellm import completion

load_dotenv()

ExtractedIdent = namedtuple(
    'ExtractedIdent', ('class_name', 'function_name', 'rel_file_name')
)

EXTRACT_PROMPT = """I'm extracting relevant code snippets in the source code from the Github issue description, e.g. definition of class names, method/function names, and optional relative file path if having.
- None of the 3 fields are compulsory, but it's encourage to fill as many as possible.
- If the method is global, let the class field empty. If there're no methods of class mentioned, just fill in class field and let method field empty.
- Either class or method field can be empty, but not both.
- Don't include class attributes or global variables.
- If there are identifiers that are only exist in the examples for demonstration and not in the
  source code, please ignore them.
- Consider inheritance and polymorphism when extracting class names.
Can you help me parse the text and extract into json format, with field "identifiers" containing a
list of object with following fields: "class_name", "function_name", "rel_file_name". Please return
only the JSON output, don't include any other text.

--- Issue Description ---
{issue_description}
"""


def extract_identifiers_from_text(
    issue_description: str,
    litellm_config: dict | None = None,
) -> set[ExtractedIdent]:
    messages = []

    messages.append(
        {
            'role': 'user',
            'content': EXTRACT_PROMPT.format(issue_description=issue_description),
        }
    )
    response = completion(
        model=litellm_config['model']
        if litellm_config
        else os.environ['LITELLM_MODEL'],
        messages=messages,
        api_key=litellm_config['api_key']
        if litellm_config
        else os.environ['LITELLM_API_KEY'],
        base_url=litellm_config['base_url']
        if litellm_config
        else os.environ['LITELLM_BASE_URL'],
        temperature=0.0,
        # top_p=0.7,
        max_tokens=8192,
        stream=False,
    )
    json_str = response.choices[0].message.content.strip()
    extracted_identifiers = json.loads(json_str)['identifiers']
    results = []
    for ident in extracted_identifiers:
        results.append(ExtractedIdent(**ident))
    return set(results)


if __name__ == '__main__':
    issue_description = """
    Modeling's `separability_matrix` does not compute separability correctly for nested CompoundModels Consider the following model: ```python from astropy.modeling import models as m from astropy.modeling.separable import separability_matrix cm = m.Linear1D(10) & m.Linear1D(5) ``` It's separability matrix as you might expect is a diagonal: ```python >>> separability_matrix(cm) array([[ True, False], [False, True]]) ``` If I make the model more complex: ```python >>> separability_matrix(m.Pix2Sky_TAN() & m.Linear1D(10) & m.Linear1D(5)) array([[ True, True, False, False], [ True, True, False, False], [False, False, True, False], [False, False, False, True]]) ``` The output matrix is again, as expected, the outputs and inputs to the linear models are separable and independent of each other. If however, I nest these compound models: ```python >>> separability_matrix(m.Pix2Sky_TAN() & cm) array([[ True, True, False, False], [ True, True, False, False], [False, False, True, True], [False, False, True, True]]) ``` Suddenly the inputs and outputs are no longer separable? This feels like a bug to me, but I might be missing something?
    """
    extracted_identifiers = extract_identifiers_from_text(issue_description)
    print(extracted_identifiers)
