import spacy
import csv
import os
from tqdm import tqdm
import pandas as pd

nlp = spacy.load("en_core_web_sm")

###### CODE FROM TEXT AGG (Corrected) #####################################################
"""
Extracts all the Hits, and KWIC
Output the result to a CSV file
Already completed in Helen's implementation, we are using hers  
"""
def extract_from_all_files(directory, word_list):
    """Iterate through all .txt files in directory and extract word context."""
    output_file = f"/Users/muhammadmushoffa/Desktop/corpus_linguistic/help_all_medium_sample_files.csv"
    
    word_list_lower = [word.lower() for word in word_list]
    all_rows = []
    total_matches = 0

    files_to_process = [f for f in sorted(os.listdir(directory)) if f.endswith('.txt')]

    for filename in tqdm(files_to_process, desc="Extracting contexts"):
        file_path = os.path.join(directory, filename)
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                contents = f.read()
            
            contents = contents.replace('<speaker>', '').replace('</speaker>', '')
            words = contents.split()

            for i, word in enumerate(words):
                if word.lower() in word_list_lower:
                    start = max(0, i - 30)
                    left_context = ' '.join(words[start:i])
                    end = min(len(words), i + 61)
                    right_context = ' '.join(words[i+1:end])
                    
                    all_rows.append({'left_context': left_context, 'target_word': word, 'right_context': right_context})
                    total_matches += 1
        except Exception as e:
            print(f"\nError processing {filename}: {e}")

    df = pd.DataFrame(all_rows)
    df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"\nExtraction complete. Total matches found: {total_matches}")

# --- Run the function above ---
hansard_dir = "/Users/muhammadmushoffa/Desktop/corpus_linguistic/Hansard 2000 file sample"
help_forms = [
    'help', 'helps', 'helped', 'helping', 'helpful', 'helpless', 
    'helpfully', 'helplessness', 'helper', 'helpeth', 'helpst', 'unhelpful'
]
extract_from_all_files(hansard_dir, help_forms)


###### ANALYSIS CODE (Corrected) #########################################################
def check_help_polarity(left_context_tokens, window_size=5):
    """Checks for negation words before 'help'."""
    negation_words = {'not', "n't", 'nor', 'never', 'hardly', 'scarcely', 'barely', 'no', 'nobody', 'nothing', 'nowhere', 'none', 'neither'}
    window = left_context_tokens[-window_size:]
    window_lower = [word.lower() for word in window]
    for word in window_lower:
        if word in negation_words:
            return 'NEG'
    return 'POS'

def check_preceding_to(left_context_tokens, is_help_verb=True):
    """Checks if 'to' appears within the 4 words immediately preceding 'help'."""
    if not is_help_verb:
        return 'NA'
    window = left_context_tokens[-4:]
    window_lower = [word.lower() for word in window]
    if 'to' in window_lower:
        return 'YEStoBefore'
    return 'NOtoBefore'

# This takes the entire sequence, both right and left context
def analyze_hansard_hit(full_kwic, target_word_text):
    """
    Analyzes a KWIC line for Subject, Complement, Polarity, and Preceding 'to'.
    """
    doc = nlp(full_kwic)
    
    target_token, target_idx = None, None
    # Find the specific target word instance from the CSV row
    for i, token in enumerate(doc):
        if token.text == target_word_text:
            if target_token is None or abs(i - len(doc)//2) < abs(target_idx - len(doc)//2):
                target_token = token
                target_idx = i
            
    if target_idx is None:
        return None

    # --- Key Logic: Check if the target is a verb. If not, return NA for most fields. ---
    if target_token.pos_ != 'VERB':
        return {
            "help_hit": target_token.text, "hit_pos": target_token.tag_,
            "subj_type": "NA", "subj_head": "NA", "subj_animacy": "NA",
            "comp_lemma": "NA", "comp_tag": "NA", "polarity": "NA", "preceding_to": "NA",
        }

    # --- Analysis for Verbs Only ---
    left_context_tokens = [t.text for t in doc[:target_idx]]
    polarity = check_help_polarity(left_context_tokens)
    preceding_to = check_preceding_to(left_context_tokens, is_help_verb=True)

    # This part looks towards the left
    subj_type, subj_head = "NA", "NA"
    for i in range(target_idx - 1, -1, -1):
        t = doc[i]
        if t.pos_ in ["NOUN", "PROPN", "PRON"]:
            subj_type = "PRON" if t.pos_ == "PRON" else "NP"
            subj_head = t.lemma_
            break

    subj_animacy = "NA"
    if subj_head != "NA":
        animate_pronouns = ['i', 'you', 'he', 'she', 'we', 'they', 'who', 'whom','himself', 'herself', 'themselves']
        inanimate_pronouns = ['it', 'what', 'which', 'that']
        if subj_type == "PRON":
            if subj_head.lower() in animate_pronouns: subj_animacy = "Animate"
            elif subj_head.lower() in inanimate_pronouns: subj_animacy = "Inanimate"
        else:
            subj_animacy = "Inanimate"

    

    
    # This part looks towards the right
    comp_lemma, comp_tag = "NA", "NA"
    for i in range(target_idx + 1, len(doc)):
        t = doc[i]
        if t.pos_ == "VERB":
            comp_lemma = t.lemma_
            comp_tag = t.tag_
            break

    return {
        "help_hit": target_token.text, "hit_pos": target_token.tag_,
        "subj_type": subj_type, "subj_head": subj_head, "subj_animacy": subj_animacy,
        "comp_lemma": comp_lemma, "comp_tag": comp_tag,
        "polarity": polarity, "preceding_to": preceding_to,
    }

# --- Main Processing Logic ---
input_csv = "/Users/muhammadmushoffa/Desktop/corpus_linguistic/help_all_medium_sample_files.csv" 
output_file = '/Users/muhammadmushoffa/Desktop/corpus_linguistic/comprehensive_analysis.csv'

with open(input_csv, 'r', encoding='utf-8') as f_in, \
     open(output_file, 'w', newline='', encoding='utf-8') as f_out:
    
    reader = csv.DictReader(f_in)
    writer = csv.writer(f_out)
    
    header = [
        "left_context", "target_word", "right_context", "help_hit", "hit_pos", 
        "subj_type", "subj_head", "subj_animacy", "comp_lemma", "comp_tag", 
        "polarity", "preceding_to"
    ]
    writer.writerow(header)

    for row in tqdm(reader, desc="Analyzing contexts"):
        full_line = f"{row['left_context']} {row['target_word']} {row['right_context']}"
        print("Parameter")
        print("---"*20)
        print(row['target_word'])
        analysis_results = analyze_hansard_hit(full_line, row['target_word'])

        if analysis_results:
            output_row = [
                row['left_context'], row['target_word'], row['right_context'],
                analysis_results["help_hit"], analysis_results["hit_pos"],
                analysis_results["subj_type"], analysis_results["subj_head"],
                analysis_results["subj_animacy"], analysis_results["comp_lemma"],
                analysis_results["comp_tag"], analysis_results["polarity"],
                analysis_results["preceding_to"]
            ]
            writer.writerow(output_row)

print(f"Comprehensive analysis complete. Results saved to {output_file}")