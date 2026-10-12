import google.generativeai as genai
import os
import json
from openai import OpenAI
from tqdm import tqdm

os.environ["OPENAI_API_KEY_JUS"] = "API-KEY"
genai.configure(api_key="API-KEY")


def get_data_doc():

  data_dict = {
    "train": [],
    "dev": [],
    "test": [],
  }

  for spl in list(data_dict.keys()):
    with open(f"../CITAR-NER-Br/parsed/docs/final_{spl}.json", encoding="utf-8") as splits_file:
      splits_data = json.load(splits_file)

      n_docs = 0
      n_doc_words = 0

      for doc_i,data in enumerate(splits_data):
        doc_ents = {"LEGISLACAO": [], "ARTIGO": [], "PARAGRAFO": [], "INCISO": [], "ALINEA": [], "CAPUT": []}

        doc_words = data["text"]

        n_docs += 1
        n_doc_words += len(doc_words)

        doc_text = " ".join(doc_words)

        for doc_ent in data["ner"]:
          doc_ents[doc_ent["type"]].append({"text": " ".join([doc_words[i] for i in doc_ent["index"]]), "index": doc_ent["index"]})

        data_dict[spl].append({"document_name": data["doc_id"], "text": doc_text, "result": doc_ents})

      print(n_docs, round(n_doc_words/n_docs,2))  
  return data_dict


def request_llm(llm):
  if llm == "chatgpt":
      client = OpenAI(api_key=os.environ['OPENAI_API_KEY_JUS'])
  elif llm == "gemini":
      client = genai.GenerativeModel("models/gemini-3.1-pro-preview")

  data_dict = get_data_doc()

  train_data = data_dict["train"].copy()
  test_data = data_dict["test"].copy()

  print(f"!!!!!!!!!!!! Beginning iteration !!!!!!!!!!!!!!!!!!!!!!!")

  with open("./prompt_with_negs.txt", encoding="utf-8") as pf:
    prompt = pf.read()

    for idx,test_obj in tqdm(enumerate(test_data), total=len(test_data)):
      final_prompt = prompt + f"\nInput:\n\n{test_obj["text"]}"

      print(f"\rRequesting {llm}: ", f"{idx+1}/{len(test_data)}", end='', flush=True)

      tries = 10

      parseable_response = False

      while tries>0:
          if llm == "chatgpt":
              response = client.chat.completions.create(
                model="gpt-5-2025-08-07",
                temperature=1,
                messages=[{"role": "user", "content": final_prompt}],
              )

              output = response.choices[0].message.content

          elif llm == "gemini":
              response = client.generate_content(final_prompt)
              output = response.text
          
          if len(output) > 0:
              tries = 0
              parseable_response = True
          else:
              print("Error loading response. ")
              tries -= 1
              continue
        
      if not parseable_response:
        print(f"Max req tries, skipping doc n. {idx+1}.")
        test_data[idx][f"preds"] = "Failed"
      else:
        test_data[idx][f"preds"] = output

    with open(f'./promptner-{llm}/preds_promptner_{llm}.json', 'w', encoding="utf8") as f:
        json.dump(test_data, f, ensure_ascii=False)


request_llm("chatgpt")
request_llm("gemini")
