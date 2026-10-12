import json

def format(pred_file, gold_file, final_file):
    with open(pred_file, encoding="utf-8") as f1, open(gold_file, encoding="utf-8") as f2:
        pred_data = f1.readlines()
        gold_data = json.load(f2)

        final = []

        for i,pred in enumerate(pred_data):
            pred_json = json.loads(pred)

            if pred_json["sentence"] != " ".join(gold_data[i]["sentence"]):
                print(pred_json, gold_data[i]["sentence"])
                raise Exception("Unmatched sentences")
            
            final.append({
                "sentence": pred_json["sentence"].split(),
                "golds": [{"index": gold["index"], "type": gold["type"].lower()} for gold in gold_data[i]["ner"]],
                "preds": [{"index": s[0], "type": s[1].lower()} for s in pred_json["pred_spans"]],
            })

        with open(final_file, "w", encoding="utf8") as f3:
            json.dump(final, f3, indent=4, ensure_ascii=False)


format("preds_test.out", "../../../CITAR-NER-Br/parsed/chunks/final_w2_test.json", "final_bart_golds_preds.json")