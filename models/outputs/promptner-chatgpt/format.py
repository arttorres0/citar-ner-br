import json

def format(pred_file, final_file):
    with open(pred_file, encoding="utf-8") as f1, open("../../../CITAR-NER-Br/parsed/docs/final_test.json", encoding="utf8") as f2:
        data = json.load(f1)
        data2 = json.load(f2)
        final = []

        labels = ["legislacao", "artigo", "paragrafo", "alinea", "caput", "inciso"]

        for i,instance in enumerate(data):

            if instance["text"] != " ".join(data2[i]["text"]):
                print(instance["document_name"], i)
                raise Exception("Unmatched sentences")

            preds = []
            golds = []

            for label,gs in instance["result"].items():
                for g in gs:
                    golds.append({"index": g["index"], "type": label.lower()})

            for p in instance["preds_parsed"]:
                if p["verif"] == "true" and p["ent_type"] != None:
                    if p["ent_type"].lower() in labels:
                        preds.append({"text": p["ent_text"], "type": p["ent_type"].lower()})

            final.append({
                "sentence": data2[i]["text"],
                "golds": golds,
                "preds": preds,
            })

        with open(final_file, "w", encoding="utf8") as f3:
            json.dump(final, f3, indent=4, ensure_ascii=False)


format("./preds_promptner_chatgpt_parsed.json", "final_promptner-chatgpt.json")
