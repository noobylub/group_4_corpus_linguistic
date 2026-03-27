import spacy
import csv

nlp = spacy.load("en_core_web_sm")

def analyze_hansard_hit(full_kwic, search_lemma="help"):
    """
    Analyzes a KWIC line for Subject Type & Head, Complement Lemma & Tag
    """
    doc = nlp(full_kwic)
    
    # 1. Find the specific 'help' token in the sentence
    target_token = None
    target_idx = None
    for i, token in enumerate(doc):
        if token.lemma_.lower() == search_lemma:
            target_token = token
            target_idx = i
            break
            
    if target_idx is None:
        return None

    # --- TASK: Subject Type & Head ---
    subj_type, subj_head = "NA", "NA"
    for i in range(target_idx - 1, -1, -1):
        t = doc[i]
        if t.pos_ in ["NOUN", "PROPN", "PRON"]:
            subj_type = "PRON" if t.pos_ == "PRON" else "NP"
            subj_head = t.lemma_
            break


    # --- TASK: Subject Animacy ---
    subj_animacy = "NA"
    if subj_head != "NA":
        animate_pronouns = ['i', 'you', 'he', 'she', 'we', 'they', 'who', 'whom','himself', 'herself', 'themselves']
        inanimate_pronouns = ['it', 'what', 'which', 'that']
        
        if subj_type == "PRON":
            if subj_head.lower() in animate_pronouns:
                subj_animacy = "Animate"
            elif subj_head.lower() in inanimate_pronouns:
                subj_animacy = "Inanimate"
        else: # NP
            # otherwise assuming most will be inanimate (CAN PROBS BE IMPROVED!)
            subj_animacy = "Inanimate"


    # --- TASK: Complement Lemma & Tag ---
    comp_lemma, comp_tag = "NA", "NA"
    for i in range(target_idx + 1, len(doc)):
        t = doc[i]
        if t.pos_ == "VERB":
            comp_lemma = t.lemma_
            comp_tag = t.tag_
            break

    return {
        "help_hit": target_token.text, # e.g., 'helped'
        "hit_pos": target_token.tag_,   # e.g., 'VBD'
        "subj_type": subj_type,
        "subj_head": subj_head,
        "subj_animacy": subj_animacy,
        "comp_lemma": comp_lemma,
        "comp_tag": comp_tag,
    }

# --- TEST CASE: Facilitating 'helped' ---
sentence = "The Members helped us produce a very clear report."
print(analyze_hansard_hit(sentence))
sentence = "The Members began to help us in producing a very clear report"
print(analyze_hansard_hit(sentence))
