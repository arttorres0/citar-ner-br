import os
from openai import OpenAI
from tqdm import tqdm
import ast
import json

os.environ["OPENAI_API_KEY"] = "API-KEY"

final_dict = {"lener": {}, "diario_judic_stj": {}, "diario_judic_trf5": {}}

base_prompt = """
Role: You are an expert Brazilian Legal Analyst and Data Verifier specialized in legal citations (referenciação jurídica).

Task: Validate legal identifiers. You must answer a question verifying if the "text" corresponds correctly to the "class" and if the legal reference actually exists in the Brazilian Legal System. You must be extremely accurate, meaning you have to check official sources in the internet, such as https://www.planalto.gov.br/, https://www.jusbrasil.com.br/, https://www.al.sp.gov.br/repositorio/legislacao/constituicao/1989/compilacao-constituicao-0-05.10.1989.html, among others.

Verification Variables:

Primary Fields: Use text and class.

Validation Criteria:

Class-Text Alignment: The class must be the most specific level mentioned in the text and must match the existing legal code.

LEGISLACAO Allowlist: This class strictly includes: Constituição, Leis, Decreto-Leis, and Emendas Constitucionais.

Invalid for LEGISLACAO: Súmulas, Jurisprudência, Recomendações, Portarias, Medidas Provisórias (MP), Decretos, Instruções Normativas (IN), and Resoluções.

Factual Existence (Critical): You must verify if the specific subdivision (Article, Paragraph, Inciso) actually exists within the cited Law or Code.

Example: If a text cites "Art. 489, § 11 of the CPC," and the CPC only goes up to § 3 for that article, it is invalid.

Resolvability: The text must be unique. "CPC" is valid as LEGISLACAO, but "Artigo do CPC" is invalid because the number is missing.

Invalidation Rules:
Mark resolved: false if:
- The legal subdivision does not exist in the official Brazilian text.
- The class is mismatched (e.g., text describes an Inciso but class says ARTIGO).
- The item belongs to a forbidden category (e.g., a Portaria).
- Vital information (numbers/years) is missing.

Output Format:
Return a JSON object, which must contain:
- resolved: Boolean (true or false).
- reason: A brief, technical explanation in Portuguese (only if resolved is false).

Here are some examples:

Input:
Na legislação brasileira, existe "art . 240 , do CPC"? Esse item jurídico é um "ARTIGO"?
Output:
{"resolved": True}

Input:
Na legislação brasileira, existe "CPC"? Esse item jurídico é um "LEGISLACAO"?
Output:
{"resolved": True}

Input:
Na legislação brasileira, existe "art . 240 CPC"? Esse item jurídico é um "ARTIGO"?
Output:
{"resolved": True}

Input:
Na legislação brasileira, existe "art . 489, § 11, IV, do CPC"? Esse item jurídico é um "INCISO"?
Output:
{"resolved": False, "reason": "Não existe parágrafo 11 no artigo 489 do CPC"}

Input:
Na legislação brasileira, existe "Código de Processo Civil"? Esse item jurídico é um "LEGISLACAO"?
Output:
{"resolved": True}

Input:
Na legislação brasileira, existe "artigo 240 Código de Processo Civil"? Esse item jurídico é um "ARTIGO"?
Output:
{"resolved": True}

Input:
Na legislação brasileira, existe "artigo 240 , §§ 1º Código de Processo Civil"? Esse item jurídico é um "PARAGRAFO"?
Output:
{"resolved": True}

Input:
Na legislação brasileira, existe "artigo 240 , §§ 2º , do Código de Processo Civil"? Esse item jurídico é um "PARAGRAFO"?
Output:
{"resolved": True}

Input:
Na legislação brasileira, existe "Lei n.º 10.931/2004"? Esse item jurídico é um "LEGISLACAO"?
Output:
{"resolved": True}

Input:
Na legislação brasileira, existe "ART. 966, VII, § 2º, DO CPC/2015"? Esse item jurídico é um "PARAGRAFO"?
Output:
{"resolved": False, "reason": "Não existe parágrafo 2º, do inciso VII, do artigo 966 do CPC"}

Input:
Na legislação brasileira, existe "ART. 966, VII CPC/2015"? Esse item jurídico é um "INCISO"?
Output:
{"resolved": True}

Input:
Na legislação brasileira, existe "ART. 966 § 2º, DO CPC/2015"? Esse item jurídico é um "PARAGRAFO"?
Output:
{"resolved": True}

"""

def get_prompt(ann):
    prompt = base_prompt

    prompt += f"""
Input:
Na legislação brasileira, existe "{ann[2].replace("\n", "").strip()}"? Esse item jurídico é um "{ann[1].split(" ")[0].strip()}"?
Output:
"""

    return prompt

for d in list(final_dict.keys()):
    print(f"!!!!!!!!!!!! Beginning iteration - {d} !!!!!!!!!!!!")
    if d != "lener":
        d0 = f"tesemo/{d}"
    else:
        d0 = d

    ann_files = [f for f in os.listdir(f"./raw_data/{d0}") if f[-4:] == ".ann"]

    for _,ann_file in tqdm(enumerate(ann_files), total=len(ann_files)):
        doc_id = ann_file.split(".ann")[0]

        final_dict[d][doc_id] = {}

        with open(f"./raw_data/{d0}/{ann_file}", encoding="utf8") as f1:
            ann_data = [l.split("\t") for l in f1.readlines()]

            for ann in ann_data:
                ann_failed = False

                client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

                final_prompt = get_prompt(ann)

                tries = 10
                parseable_response = False

                while tries>0:
                    try:
                        response = client.chat.completions.create(
                                model="gpt-4o-2024-08-06",
                                temperature=0,
                                messages=[{"role": "user", "content": final_prompt}],
                                response_format={ "type": "json_object" }
                        )

                    except Exception as e:
                        print("Error in API request: ", e)
                        tries -= 1
                        continue

                    output = response.choices[0].message.content

                    if ": true" in output:
                        output = output.replace(": true", ": True")
                    if ":true" in output:
                        output = output.replace(":true", ":True")
                    if ": false" in output:
                        output = output.replace(": false", ": False")
                    if ":false" in output:
                        output = output.replace(":false", ":False")

                    if output[:7] == "```json" and output[-3:] == "```":
                        # print("OK")
                        try:
                            output = ast.literal_eval(output[7:-3])
                            tries = 0
                            parseable_response = True
                        except Exception as e:
                            # raise Exception("Error loading json. ", e)
                            print("Error loading json. ", e)
                            tries -= 1
                        continue
                    else:
                        try:
                            output = ast.literal_eval(output)
                            tries = 0
                            parseable_response = True
                        except Exception as e:
                            # raise Exception("Error loading json. ", e)
                            print("Error loading json. ", e)
                            tries -= 1
                        continue

                if not parseable_response:
                    print(f"Max req tries, skipping doc id: {doc_id}, ann_id: {ann[0]}.")
                    ann_failed = True
                    final_dict[d][doc_id][ann[0]] = "Failed"
                else:
                    # =====================================
                    if output["resolved"] == False:
                        # print(ann[2], output)
                        final_dict[d][doc_id][ann[0]] = {"llm": output, "user": {"valid": False, "changed": False}}


with open(f"final_gpt.json", "w", encoding="utf8") as f3:
    json.dump(final_dict, f3, indent=4, ensure_ascii=False)