import json
from tqdm import tqdm
from nltk.tokenize import word_tokenize

# NI = no index (preds only have string, no index)


def calculate_metrics(tp, partials, fp, fn):
    f1, p, r = 0.0, 0.0, 0.0

    if tp + len(partials) + fp > 0:
        p = (tp + sum(partials)) / (tp + len(partials) + fp)
    if tp + len(partials) + fn > 0:
        r = (tp + sum(partials)) / (tp + len(partials) + fn)

    if p > 0 and r > 0:
        f1 = 2*p*r / (p+r)

    return f1, p, r

def is_discontinuous(idxs):
    return not all(idxs[i] - idxs[i-1] == 1 for i in range(1, len(idxs)))

def is_discontinuous_NI(sentence, entity_text):
    b = word_tokenize(entity_text)
    return " ".join(b) not in " ".join(sentence)


def get_exact_matches(gold_spans, pred_spans, is_preds_NI=False):
    matches = []

    if is_preds_NI:
        estim_index_preds = [p_i for p_i,p in enumerate(pred_spans) if len(p["estim_index"]) == 1]
        text_preds = [p_i for p_i,p in enumerate(pred_spans) if len(p["estim_index"]) != 1]

        unmatched_golds_idxs = []
        matches_index = []
        
        for i,g in enumerate(gold_spans):
            g_found = False
            for p in estim_index_preds:
                if g["index"] == list(range(pred_spans[p]["estim_index"][0][0], pred_spans[p]["estim_index"][0][1])):
                    matches_index.append((i,p))
                    g_found = True
                    break

            if not g_found:
                unmatched_golds_idxs.append(i)

        unmatched_estim_index_preds = [p for p in estim_index_preds if p not in [m[1] for m in matches_index]]
        matches_NI = []

        for i in unmatched_golds_idxs:
            for p in text_preds + unmatched_estim_index_preds:
                if p in [m[1] for m in matches_NI]:
                    continue

                if gold_spans[i]["text"] == pred_spans[p]["text"]:
                    matches_NI.append((i,p))
                    break

        matches = matches_index + matches_NI

    else:
        for i,g in enumerate(gold_spans):
            for j,p in enumerate(pred_spans):
                if g["index"] == p["index"]:
                    matches.append((i,j))
                    break

    return matches

def process_instance_exact_match(gold_ents, pred_ents, label, sentence, is_disc=False, is_preds_NI=False):
    gold_ents = [g for g in gold_ents if g["type"] == label]
    pred_ents = [p for p in pred_ents if p["type"] == label]

    exact_matches_idxs = get_exact_matches(gold_ents, pred_ents, is_preds_NI)

    if is_disc:
        exact_matches_idxs = [m for m in exact_matches_idxs if is_discontinuous(gold_ents[m[0]]["index"])]

    exact_match_ents = []

    for m in exact_matches_idxs:
        if gold_ents[m[0]]["text"] != pred_ents[m[1]]["text"]:
            raise Exception("Error in exact match")
        
        exact_match_ents.append({"text": gold_ents[m[0]]["text"], "index": gold_ents[m[0]]["index"]})

    if is_disc:
        gold_ents = [g for g in gold_ents if is_discontinuous(g["index"])]

        if is_preds_NI:
            pred_ents = [p for p in pred_ents if is_discontinuous_NI(sentence, p["text"])]
        else:
            pred_ents = [p for p in pred_ents if is_discontinuous(p["index"])]

    return exact_matches_idxs, exact_match_ents, {
        "tp": len(exact_matches_idxs),
        "fn": len(gold_ents) - len(exact_matches_idxs),
        "fp": len(pred_ents) - len(exact_matches_idxs)
    }


def get_estim_index(entity_text, sentence):
    n, m = len(entity_text.split(" ")), len(sentence)
    return [(i, i + n) for i in range(m - n + 1) if sentence[i : i + n] == entity_text.split(" ")]


def get_matches(pred_file):
    calc_disc = True
    output_file_name = pred_file.split("/")[1]

    with open(pred_file, encoding="utf-8") as f1:
        data = json.load(f1)

        labels = [[g["type"] for g in i["golds"]] + [p["type"] for p in i["preds"]] for i in data]
        labels = list(set([j for sub in labels for j in sub]))

        pred_att_list = list(set([j for sub in [list(y.keys()) for x in data for y in x["preds"]] for j in sub]))

        is_preds_NI = False

        if "index" not in pred_att_list:
            is_preds_NI = True

        for i,d in enumerate(data):
            if d["sentence"] == ["'"]:
                data[i]["preds"] = []

            for j,g in enumerate(d["golds"]):
                data[i]["golds"][j]["text"] = " ".join([d["sentence"][idx] for idx in g["index"]])
            
            for k,p in enumerate(d["preds"]):
                if "text" not in pred_att_list and "index" in pred_att_list:
                    data[i]["preds"][k]["text"] = " ".join([d["sentence"][idx] for idx in p["index"]])

                if is_preds_NI:
                    estim_index = get_estim_index(data[i]["preds"][k]["text"], d["sentence"])
                    data[i]["preds"][k]["estim_index"] = estim_index

                    if len(estim_index) == 1:
                        if p["text"] != " ".join(d["sentence"][estim_index[0][0]:estim_index[0][1]]):
                            raise Exception(p["text"], " ".join(d["sentence"][estim_index[0][0]:estim_index[0][1]]))

        stats_exact = { k: {"tp": 0, "fp": 0, "fn": 0}  for k in labels+["total"]}

        if calc_disc:
            stats_exact_disc = { k: {"tp": 0, "fp": 0, "fn": 0}  for k in labels+["total"]}

        for idx,instance in tqdm(enumerate(data), total=len(data)):
            exact_matches_instance = { k: [] for k in labels }

            if calc_disc:
                exact_matches_instance_disc = { k: [] for k in labels }
            
            for label in labels:
                # EXACT MATCHES (CONTINUOUS + DISCONTINUOUS)
                exact_matches_idxs, exact_match_ents, instance_stats = process_instance_exact_match(instance["golds"], instance["preds"], label, instance["sentence"], is_disc=False, is_preds_NI=is_preds_NI)

                exact_matches_instance[label] += exact_match_ents

                stats_exact[label]["tp"] += instance_stats["tp"]
                stats_exact[label]["fn"] += instance_stats["fn"]
                stats_exact[label]["fp"] += instance_stats["fp"]
                stats_exact["total"]["tp"] += instance_stats["tp"]
                stats_exact["total"]["fn"] += instance_stats["fn"]
                stats_exact["total"]["fp"] += instance_stats["fp"]

                if calc_disc:
                    # DISCONTINUOUS ONLY (EXACT-MATCH)
                    _, exact_match_disc_ents, instance_stats_disc = process_instance_exact_match(instance["golds"], instance["preds"], label, instance["sentence"], is_disc=True, is_preds_NI=is_preds_NI)

                    exact_matches_instance_disc[label] += exact_match_disc_ents

                    stats_exact_disc[label]["tp"] += instance_stats_disc["tp"]
                    stats_exact_disc[label]["fn"] += instance_stats_disc["fn"]
                    stats_exact_disc[label]["fp"] += instance_stats_disc["fp"]
                    stats_exact_disc["total"]["tp"] += instance_stats_disc["tp"]
                    stats_exact_disc["total"]["fn"] += instance_stats_disc["fn"]
                    stats_exact_disc["total"]["fp"] += instance_stats_disc["fp"]
                

            instance["exact_matches"] = exact_matches_instance

            if calc_disc:
                instance["exact_matches_disc"] = exact_matches_instance_disc

            data[idx] = instance
        
        with open(f"final_{output_file_name}_matches{"_NI" if is_preds_NI else ""}.json", 'w', encoding="utf8") as f2:
            json.dump(data, f2, indent=4, ensure_ascii=False)


        for l in labels + ["total"]:
            stats_exact[l]["f1"], stats_exact[l]["p"], stats_exact[l]["r"] = calculate_metrics(stats_exact[l]["tp"], [], stats_exact[l]["fp"], stats_exact[l]["fn"])

        final_results = {
            "stats_exact": stats_exact,
        }

        if calc_disc:
            for l in labels + ["total"]:
                stats_exact_disc[l]["f1"], stats_exact_disc[l]["p"], stats_exact_disc[l]["r"] = calculate_metrics(stats_exact_disc[l]["tp"], [], stats_exact_disc[l]["fp"], stats_exact_disc[l]["fn"])


            final_results["stats_exact_disc"] = stats_exact_disc

        with open(f"final_{output_file_name}_results{"_NI" if is_preds_NI else ""}.json", 'w', encoding="utf8") as f3:
            json.dump(final_results, f3, indent=4, ensure_ascii=False)


get_matches("../outputs/bart/final_bart_golds_preds.json")
get_matches("../outputs/w2/final_w2_golds_preds.json")
get_matches("../outputs/promptner-chatgpt/final_promptner-chatgpt.json")
get_matches("../outputs/promptner-gemini/final_promptner-gemini.json")
