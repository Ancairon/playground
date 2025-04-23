import openai
from openai import OpenAI
import os
import sys
from pathlib import Path
import shutil
import re
import pandas as pd
import requests

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def fetch_mib_csv(mib_name: str):
    """
    Downloads the CSV for a given MIB from mibbrowser.online and returns a DataFrame.
    """
    url = f"https://mibbrowser.online/mibs_csv/{mib_name}.csv"
    try:
        response = requests.get(url)
        response.raise_for_status()
        print(response.text)
        return response.text
    except requests.RequestException as e:
        print(f"✗ Failed to fetch CSV for {mib_name}: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"✗ Error processing CSV for {mib_name}: {e}", file=sys.stderr)
        return None



def extract_mibs_from_text(text):
    """
    Extracts distinct MIB names from a text that includes lines like 'MIB: ENTITY-MIB'
    """
    mib_pattern = r"MIB:\s*([A-Z0-9\-]+)"
    matches = re.findall(mib_pattern, text)
    unique_mibs = sorted(set(matches))
    return unique_mibs

def load_mib_csv(csv_path: Path):
    """
    Loads a CSV file that contains MIB data.
    """
    try:
        df = pd.read_csv(csv_path)
        print(f"Successfully loaded CSV from {csv_path}")
        return df
    except Exception as e:
        print(f"Failed to load CSV: {e}", file=sys.stderr)
        sys.exit(1)

def process_yaml_with_chatgpt(input_yaml_path: Path, output_yaml_path: Path, model_name="gpt-4.1-mini"):
    try:
        input_yaml_content = input_yaml_path.read_text(encoding='utf-8')
        print(f"Successfully read input file: {input_yaml_path}")
    except Exception as e:
        print(f"Error reading input file {input_yaml_path}: {e}", file=sys.stderr)
        sys.exit(1)

    metrics_present = ("metrics:" in input_yaml_content)
    print(metrics_present)

    # Step 1: Extract MIBs
    mibs = extract_mibs_from_text(input_yaml_content)

    if len(mibs) == 1:
        print("in")
        # mib_csv_path = Path(f"./mib-browser/{mibs[0]}.csv")
        csv_txt = fetch_mib_csv(mibs[0])
        print(csv_txt)






    prompt = f"""
Take the following input YAML file content and update it by adding a "description" and "unit" field for each metric entry under the `metrics:` section. DO NOT REMOVE ANY KEY FROM THE YAML, ONLY ADD

Take also the input CSV where it has details about the OIDs of the MIB, and inside there are descriptions (OBJECT_DESCRIPTION) and units (OBJECT_DATA_TYPE).

Input CSV:
```csv
{csv_txt}
```

IF THERE IS NO METRICS KEY IN THE YAML, DON'T ADD IT. YOU ONLY SHOULD ADD UNITS AND DESCRIPTIONS WHEN THE METRICS KEY IS PRESENT.

FOR ENTRIES INSIDE THE METRICS SECTION:
    - The "description" should use verbatim. 

    generate a concise description based on the symbol's `name` and `OID`. The description should explain what the metric is or represents. Do not explain if it was extracted or matched or originated from. **Use verbatim.**

    If for example you would generate

    'aristaEgressQueuePktsDropped metric with OID 1.3.6.1.4.1.30065.3.6.1.2.1.6 represents the number of packets dropped in the egress queue.'

    this is wrong, we want just:

    'number of packets dropped in the egress queue'

    short and concise

    - For the unit:

    Choose UCUM case sensitive ("c/s") approved symbols and standard units. Read https://ucum.org/ucum to see the case sensitive versions for specific units. All generated units must comply with UCUM rules.

    Note that some UCUM types like bytes are "By" and percent "%", so take care, make sure ALL the returned types fall under UCUM support

    standard UCUM c/s units should not have curly brackets.

    enclose ALL units under double quotes, to ensure compatibility

    if the item is an object or entity (e.g access point) you should use  curly braces to annotate a quantity that will match the grammatical number of the quantity it represents. 

    For example if measuring the number of individual requests to a process the unit would be in the singular clause, not plural. Session not sessions and access_point instead of access_points. Another example is measuring Number of XYZ instances, when doing number of same thing the unit is in singluar clause as per UCUM

    encapsulate it in curly brackets and use underscores as spaces (as per UCUM instructions). 

    Example: "{{<UNIT>}}"

    If no unit can be found then add it as "TBD".


    - Ensure the output is valid YAML.
    - Preserve the original structure, indentation, and comments where possible, only adding the new fields.

Input YAML:
```yaml
{input_yaml_content}
```




Provide *only* the complete, updated YAML content enclosed within triple backticks (```yaml ... ```). Do not include any introductory text, explanations, or summaries outside the YAML block.
"""

    try:
        if metrics_present:
            print(f"Calling OpenAI ChatCompletion with model: {model_name}...")
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful YAML assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )

            generated_text = response.choices[0].message.content.strip()
    except Exception as e:
        print(f"OpenAI API call failed: {e}", file=sys.stderr)
        sys.exit(1)

    if metrics_present:
        # Try to extract YAML block
        start_marker = "```yaml\n"
        end_marker = "\n```"
        start_index = generated_text.find(start_marker)
        end_index = generated_text.rfind(end_marker)

        if start_index != -1 and end_index != -1 and start_index < end_index:
            extracted_yaml = generated_text[start_index + len(start_marker):end_index].strip()
            print("Successfully extracted YAML block from response.")
        else:
            print("Warning: Could not find ```yaml delimiters. Using entire response as YAML.", file=sys.stderr)
            extracted_yaml = generated_text.strip()

        try:
            output_yaml_path.parent.mkdir(parents=True, exist_ok=True)
            output_yaml_path.write_text(extracted_yaml, encoding='utf-8')
            print(f"Successfully wrote processed YAML to: {output_yaml_path}")
        except Exception as e:
            print(f"Error writing output file {output_yaml_path}: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        shutil.copyfile(input_yaml_path, output_yaml_path)



# --- Main Execution ---
if __name__ == "__main__":
    # parser = argparse.ArgumentParser(
    #     description="Update a YAML file by adding 'description' and 'unit' fields to metrics using the Gemini API.",
    #     formatter_class=argparse.ArgumentDefaultsHelpFormatter
    # )
    # parser.add_argument(
    #     "-i", "--input",
    #     required=True,
    #     type=Path,
    #     help="Path to the input YAML file."
    # )
    # parser.add_argument(
    #     "-o", "--output",
    #     required=True,
    #     type=Path,
    #     help="Path where the output YAML file will be saved."
    # )
    # parser.add_argument(
    #     "-m", "--model",
    #     default=DEFAULT_GEMINI_MODEL,
    #     help="Name of the Gemini model to use (e.g., 'gemini-1.5-pro-latest', 'gemini-pro')."
    # )

    # args = parser.parse_args()

    # Basic validation
    # if args.input == args.output:
    #     print("Error: Input and output file paths cannot be the same.", file=sys.stderr)
    #     sys.exit(1)




    # for dirpath, _, filenames in os.walk("default_bak"):
    #     for filename in filenames:
    #         if filename.startswith("_"):
    #             process_yaml_with_chatgpt(Path("default_bak/"+filename), Path("default/"+filename))

    process_yaml_with_chatgpt(Path("default_bak/"+"_generic-sip.yaml"), Path("default/"+"_generic-sip.yaml"))


    print("Processing complete.")
