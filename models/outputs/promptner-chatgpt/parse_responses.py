import json
import re

ent_types_dict = {
   "legislacao": "LEGISLACAO",
   "legislaçao": "LEGISLACAO",
   "legislação": "LEGISLACAO",
   "artigo": "ARTIGO",
   "paragrafo": "PARAGRAFO",
   "parágrafo": "PARAGRAFO",
   "inciso": "INCISO",
   "alínea": "ALINEA",
   "alinea": "ALINEA",
   "caput": "CAPUT",
}

filename = "preds_promptner_chatgpt"

with open(f"{filename}.json", encoding="utf-8") as f:
  data = json.load(f)

  for idx,instance in enumerate(data):
    # print(instance)

    try:
      preds = instance["preds"]
      pred_lines = preds.split("\n")
      print(pred_lines)
      pred_lines = [l for l in pred_lines if re.match(r"^\d.*\|.*(true|false).*\|.*", l, flags=re.IGNORECASE) ]
      print(pred_lines)

      parsed_preds = []

      for l in pred_lines:
        if l[-1] in [".", ";", ","]:
           l = l[:-1]

        l_split = l.split("|")

        ent_text = re.search(r"^\d+\.\s*(.*)", l_split[0].strip()).group(1)
        is_ent = l_split[1].strip().lower()

        ent_type = None
        if "true" in is_ent:
          ent_type = ent_types_dict[is_ent.split("-")[1].strip()]
          is_ent = "true"
          
        parsed_preds.append({"ent_text": ent_text, "verif": is_ent, "ent_type": ent_type})

      # raise Exception("afaslf")
      instance["preds_parsed"] = parsed_preds
      data[idx] = instance

    except Exception as e:
      print(l)
      print(e)
      raise Exception("parse error")

    # print(instance)

  with open(f"{filename}_parsed.json", "w", encoding="utf-8") as f2:
      json.dump(data, f2, indent=4, ensure_ascii=False)