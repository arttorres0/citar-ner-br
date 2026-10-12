import json

def format(pred_file, gold_file, final_file):
    with open(pred_file, encoding="utf-8") as f1, open(gold_file, encoding="utf-8") as f2:
        final = []
        pred_data = json.load(f1)
        gold_data = json.load(f2)

        for i,pred in enumerate(pred_data):
            if pred["sentence"] != gold_data[i]["sentence"]:
                print(pred, gold_data[i]["sentence"])
                raise Exception("Unmatched sentences")
            
            final.append({
                "sentence": pred["sentence"],
                "golds": [{"index": gold["index"], "type": gold["type"].lower()} for gold in gold_data[i]["ner"]],
                "preds": [{"index": pred["idxs"], "type": pred["type"].lower()} for pred in pred["entity"]]
            })

        with open(final_file, "w", encoding="utf8") as f3:
            json.dump(final, f3, indent=4, ensure_ascii=False)


format("output.json", "../../../CITAR-NER-Br/parsed/chunks/final_w2_test.json", "final_w2_golds_preds.json")