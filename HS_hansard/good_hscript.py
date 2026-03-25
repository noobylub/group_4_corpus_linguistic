# Whole script for Hansard generating csv for right context stuff only
# UPDATES 21/03/26
# Removed regex deleting punctuation straight after help; replaced with moving punvtuation to right context

"""
This script generates a CSV file for right context analysis only.
"""

import time

import re

import pandas as pd
import csv

import spacy
nlp = spacy.load("en_core_web_lg")
nlp.max_length = 2000000

import nltk
nltk.download("punkt")
nltk.download("punkt_tab")
from nltk.tokenize import word_tokenize

import os

# ---------------------------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------------------
# START
# ---------------------------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------------------
start_time = time.time()

# --------------------------------------------------------------------------------------------------
# FUNCTIONS
# --------------------------------------------------------------------------------------------------

# Function to gets KWICs out as csv file and metadata
def find_kwics(directory, pattern, output_path):
    """
        Find KWICs and output csv file

        Args:
            directory = folder containing the .txt files to anaalyse
            pattern = the regex pattern to search for keyword (in our case, 'help')
            output_path = filepath where you want .csv file to be saved

        Output:
            A .csv file of all the concordances (Saved in directory)
            Nb: The column "File" should be removed and replaced with metadata in the final KWIC sheet
        """
    file_list = [] # List of .txt files

    # Dataframe
    df = pd.DataFrame(columns=["File", "Hit", "LeftContext", "TargetWord", "RightContext", "DepVar", "HelpClass",
                               "HelpInflection", "VerbLemma", "InterveningWords", "ObjPresent",
                               "ObjPronoun", "ObjLength", "ObjHead",'WordCount','SittingType','SittingDate','FileId'])

    total_matches = 0 # Total help matches found

    # Checking have text files
    for filename in os.listdir(directory):
        # checks if needed
        if filename.endswith('.txt'):
            file_list.append(filename)
        else:
            print(f"{filename} could not be processed.")

    for filename in file_list:
        f = os.path.join(directory, filename)
        with (open(f, 'r', encoding="utf8") as textfile):
            text_content = textfile.read()

            # Splitting the double spacing
            parts = re.split(r"\n\s*\n", text_content, maxsplit=1)
            metadata = parts[0]
            contents = parts[1] if len(parts) > 1 else ""

            try:
                file_id_match = re.search(r'<FileID>(.*?)</FileID>', metadata)
                url_match = re.search(r'<URL>(.*?)</URL>', metadata)
                title_match = re.search(r'<Title>(.*?)</Title>', metadata)
                sitting_date_match = re.search(r'<SittingDate>(.*?)</SittingDate>', metadata)
                sitting_type_match = re.search(r'<SittingType>(.*?)</SittingType>', metadata)
                word_count_match = re.search(r'<WordCount>(.*?)</WordCount>', metadata)
                title_match = re.search(r'<Title>(.*?)</Title>',metadata)


                # Extract the capture text 
                file_id = file_id_match.group(1) if file_id_match else 'N/A'
                url = url_match.group(1) if url_match else 'N/A'
                title = title_match.group(1) if title_match else 'N/A'
                sitting_date = sitting_date_match.group(1) if sitting_date_match else 'N/A'
                sitting_type = sitting_type_match.group(1) if sitting_type_match else 'N/A'
                word_count = word_count_match.group(1) if word_count_match else 'N/A'
                
            except Exception as e:
                print(f"Error parsing metadata for {filename}: {e}")
                continue
 


            # --------------------------------------------------------------------
            # Pre-processing
            # --------------------------------------------------------------------
            # TODO: More pre-processing needed

            # Replacing with space
            repl_with_space = ["\n", "^", 'â€”']

            for item in repl_with_space:
                contents = contents.replace(item, ' ')

            # Replacing *+ with pound symbol
            contents = contents.replace("*+", "£")

            # Replacing with nothing:
            repl_with_nothing = [r'\*\<\*\d+', r'\*\d+']

            for item in repl_with_nothing:
                contents = re.sub(item, "", contents)

            # Replacing speaker tags with nothing
            contents = contents.replace('<speaker>', '').replace('</speaker>', '')

            # words = word_tokenize(contents)
            words = contents.split()

            #--------------------------------------------------------------------
            # Finding KWICs
            # --------------------------------------------------------------------
            help_positions = []  # Positions here help found

            # Getting list of help positions
            for i, word in enumerate(words):
                if re.search(pattern, word, re.IGNORECASE):
                    help_positions.append(i)

            for pos in help_positions:
                # Getting left context words
                left_start = max(0, pos - 30)
                left_words = words[left_start:pos]

                # Getting right context words
                right_end = min(len(words), pos + 61)
                right_words = words[pos + 1:right_end]

                # Joining words
                left_context = ' '.join(left_words)
                right_context = ' '.join(right_words)

                # Creating row for KWIC
                total_matches += 1

                # Remove punctuation at end of target, if present (eg, "Helpfully, she flagged the issue".
                # And move to beginning of right context
                target_wd = words[pos]
                if not words[pos][-1].isalpha():
                    target_wd = words[pos][:-1]
                    right_context = words[pos][-1] + " " + right_context # Append last character to right context

                new_row = pd.DataFrame([{"File": filename, "Hit": total_matches, 
                        'LeftContext': left_context,
                        'TargetWord': target_wd, 'RightContext': right_context,
                        'WordCount': word_count, 'SittingType': sitting_type,
                        'SittingDate': sitting_date, 'FileId': file_id, 'Title':title}])

                df = pd.concat([df, new_row], ignore_index=True)

    # Technically we do not need to write so early, we just need to store it in df variable 
    df.to_csv(output_path, index=False, encoding='utf-8')

    print(f"\nExtraction complete. Total matches found: {total_matches}")


# Function to find the object head
# Internal function to find the head of the object
def head_hunting(tagged_text_words, obj_words_list, desired_dependency, desired_parent_lemma):
    """
        Find the head of the object. Potentially could be used to find the subject head too.

        Args:
            tagged_text_words = a list of tagged words (example tagged word: NN_boy_44_dobj_42_boy_noNE)
            obj_words_list = a list of the words in the object
            desired_dependency = a string of the desired dependency relation (eg, dobj, nsubj)
            desired_parent_lemma = a string of the desired lemma of the parent (in our case, help)

        Returns:
            One of two strings can be returned:
            (1) the word that is the head (eg, NN_boy_44_dobj_42_boy_noNE)
            (2) the string "TODO_TODO_TODO_TODO_TODO_TODO_TODO" if the head cannot be found (in which case, may need to evaluate manually)
        """
    # If only one word in list, that word is the head
    if len(obj_words_list) == 1:
        return obj_words_list[0]

    # Below runs if len(obj_words_list) > 1
    for word in obj_words_list:
        parts = word.split('_')

        # If dependency relation == 'dobj'
        if parts[3].lower() == desired_dependency or parts[3].lower() == "obj":

            # Get the index of word's dependency relation
            parent_index = int(parts[4])

            # Go to the parent token see if its lemma is help
            parent_parts = tagged_text_words[parent_index].split('_')

            # Return word if its parent's lemma is 'help'
            if parent_parts[5].lower() == desired_parent_lemma:
                return word

        # To account for examples like: It might help the West Indies to tide over immediate difficulties.
        else:
            # If dependency relation is nsubj
            if parts[3] == "nsubj":

                # Get the index of word's dependency relation
                parent_index = int(parts[4])

                # Go to the parent token see its dependency relation
                parent_parts = tagged_text_words[parent_index].split('_')

                # Return word if its dependency relation is xcomp, ccomp
                if parent_parts[3].lower() in ["ccomp", "xcomp"]:
                    return word

    # If have not found head from above, return 7-part to-do string for further review
    return "TODO_TODO_TODO_TODO_TODO_TODO_TODO"

# Function for analysing the right_context
def analyse_right_context(tagged_kwic_words, pos):
    """
    All right context checks

    Args:
        tagged_kwic_words = list of the tagged words in the KWIC
        pos = position of help instance within the tagged_KWIC_words

    Returns:
        Dictionary of various help verb and right context properties
    """
    # Getting help parts
    tagged_help_word = tagged_kwic_words[pos]  # Ex: VB_help_35_ROOT_35_help_noNE
    help_parts = tagged_help_word.split('_')
    help_tag = help_parts[0]  # Ex: VB, VBN
    help_word = help_parts[1]  # Ex: helping, helps
    help_index = help_parts[2]  # Ex: 11 (if 11th word in whole file)
    # Above tags are all we need???? <-----------------------------------------------------------------------

    # -------------------------------------------
    # Variables
    # -------------------------------------------
    # Filler value "CHECK" so can filter in csv if manual changes needed

    help_dv = "CHECK"  # TO, BARE, ING, INING, NA
    help_class = "CHECK"  # VERB, NOUN, ADJ, ADV, OTHER
    intervening_words = 0  # Intervening words between help and infinitive
    obj_present = "CHECK"  # Is there a dobj argument for 'help'?
    obj_pronoun = "CHECK"
    obj_length = "CHECK"
    obj_head = "CHECK"
    words_to_review = 30  # how many words after "help" are we going to consider?
    verb_after_help = "CHECK"

    # List for storing words in object to facilitate finding head
    obj_words = []

    # -------------------------------------------
    # Flags and counters
    # -------------------------------------------
    obj_length_counter = 0  # How long is the object?
    obj_pn_len_1 = False  # Flag for if found pn like 'them', 'him' (so obj_length must be 1)
    found_to = False
    found_bare = False
    found_ing = False
    found_in = False
    found_verb = False
    found_object = False
    apostrophe_s = False

    # -------------------------------------------
    # Looping through 30 words after help
    # -------------------------------------------
    for i in range(1, words_to_review + 1):
        if pos + i >= len(tagged_kwic_words):
            break

        next_tagged_word = tagged_kwic_words[pos + i]  # PRP_them_550_dobj_549_they_noNE
        parts = next_tagged_word.split('_')
        next_tag = parts[0]  # Ex: PRP, TO, IN, VB
        next_word = parts[1]  # token text
        next_index = parts[2]  # index within whole file
        next_depend = parts[3]  # dependency relation (eg, dobj, aux, xcomp)
        next_head_index = parts[4]  # index of next word's head
        next_lemma = parts[5]  # lemma

        # -------------------------------------------------------------------
        # Break if encounter items likely to be irrelevant
        # -------------------------------------------------------------------
        # Break if the help_tag does not start with VB: expect VB, VBN, VBP, VBP, etc
        if not help_tag.startswith('VB'):
            break
        # Break if hit terminating punctuation
        if next_tag in ['.', ',', '``', 'HYPH', ':', ")"]:
            break
        # Break if get something like help sits
        if next_tag in ["VBP", "VBD", "VBZ"]:
            break
        # Break if get something like helps that
        if next_tag.startswith('MD') or (next_word == 'that') or next_tag.startswith('WP'):
            break
        # Break if encounter these words
        if next_word.lower() in ['and', 'or', 'are', 'if']:
            break
        # Break if get 'helping hand'
        if help_word.lower() == "helping" and next_word.lower() == "hand":
            help_dv = "NA"
            help_class = "ADJ"
            help_tag = "JJ"
            intervening_words = "NA"
            obj_present = "NA"
            obj_pronoun = "NA"
            obj_length = "NA"
            obj_head = "NA"
            break

        # -------------------------------------------------------------------
        # Object-related properties
        # -------------------------------------------------------------------
        # If haven't found a verb yet, potentially have an object
        if not found_verb:
            # If next word id a pronoun
            if (next_tag == 'PRP' or
                    next_word.lower() in ['myself', 'yourself', 'herself', 'himself',
                                          'themself', 'themselves', 'itself']):
                obj_pronoun = "PRO"
                obj_pn_len_1 = True
                found_object = True
            elif next_word.lower() in ['someone', 'anyone', 'who', 'this', 'that']:
                obj_pronoun = "PRO"
                found_object = True
            # If not a pronoun, check other potential object types
            else:
                if next_tag in ['NN', 'NP', 'NNS', 'NNP', 'NNPS', 'DT', 'CD', 'WP', 'PRP$']:
                    found_object = True

        # if found an object
        if found_object:
            if next_tag == 'POS':
                apostrophe_s = True
            else:
                # Don't want to increment if one of the items in list holds (ie, if hit the end of the obj clause)
                if not (next_word.lower() in ['to'] or next_tag in ['RB', 'TO', 'POS'] or next_tag.startswith(
                        'VB')):
                    obj_length_counter += 1
                    obj_words.append(tagged_kwic_words[pos + i])

        # -------------------------------------------------------------------
        # Finding verb in complement
        # -------------------------------------------------------------------

        # Check for '"to": helps to supply
        if not found_bare and not found_in and not found_ing and (next_tag == 'TO' or next_word.lower() == 'to'):
            # Look over next few words from position i
            for j in range(1, 3):
                # Only proceed if next few words won't exceed remaining words in text
                if pos + i + j < len(tagged_kwic_words):
                    potential_verb = tagged_kwic_words[pos + i + j]
                    verb_parts = potential_verb.split('_')
                    verb_tag = verb_parts[0]
                    verb_word = verb_parts[1]
                    verb_lemma = verb_parts[5]
                    # Getting verb lemma of the complement verb (supplies --> supply)
                    if verb_tag in ['VB', 'HV', 'BE']:
                        found_to = True
                        verb_after_help = verb_lemma
                        found_verb = True

                        if apostrophe_s:
                            # Subtract 3 so as not to include apostrophe 's' ('s) as an intervening word
                            intervening_words = i + j - 3
                        else:
                            intervening_words = i + j - 2

                        break

        # Check for -ing form verbs: help doing
        # Exclude according: help according to,
        elif not found_to and not found_in and not found_bare and next_tag in ['VBG',
                                                                               'HVG', 'BEG'] and next_word not in [
            "according"]:

            found_ing = True
            verb_after_help = next_lemma
            found_verb = True
            if apostrophe_s:
                # Subtract 3 so as not to include apostrophe 's' ('s) as an intervening word
                intervening_words = i - 2
            else:
                intervening_words = i - 1

            break

        # Check for bare infinitive
        elif not found_to and not found_in and not found_ing and next_tag in ['VB', 'HV', 'BE']:
            found_bare = True
            verb_after_help = next_lemma
            found_verb = True
            if apostrophe_s:
                # Subtract 3 so as not to include apostrophe 's' ('s) as an intervening word
                intervening_words = i - 2
            else:
                intervening_words = i - 1

            break

        # Break loop looking at words after help if verb found
        if found_verb:
            break

    # -------------------------------------------------------------------
    # Recording variables
    # -------------------------------------------------------------------
    # Record variables once finished looking over items after help at position tagged_kwic_words[pos]

    # Recording dependent variable
    if found_to:
        help_dv = "TO"
    elif found_bare:
        help_dv = "BARE"
    elif found_in:
        help_dv = "INING"
    elif found_ing:
        help_dv = "ING"
    else:
        help_dv = "NA"

    # Recording object properties
    if found_verb:
        if found_object:
            obj_present = "Yes"  # dobj present
            # Ensuring pronouns like 'them', 'him' are obj_length = 1
            if obj_pn_len_1:
                obj_length = 1
            else:
                obj_length = obj_length_counter

            # Add "NP" if obj present but it is not a "PRO"
            if obj_pronoun != "PRO":
                obj_pronoun = "NP"

            # Recording obj head
            obj_head_parts = head_hunting(tagged_kwic_words, obj_words, "dobj", "help").split('_')
            obj_head = obj_head_parts[1] if len(obj_head_parts) > 1 else "NA"

        # If have something like "She helps bake."
        else:
            intervening_words = 0
            obj_present = "No"
            obj_pronoun = "NA"
            obj_length = "NA"
            obj_head = "NA"
    # no complement after help
    else:
        verb_after_help = "NA"
        intervening_words = "NA"
        obj_present = "NA"
        obj_pronoun = "NA"
        obj_length = "NA"
        obj_head = "NA"

    # Recording the part of speech of help
    if help_tag.startswith('VB'):
        help_class = "VERB"
    elif help_tag.startswith('NN'):
        help_class = "NOUN"
    elif help_tag.startswith('JJ'):
        help_class = "ADJ"
    elif help_tag.startswith('RB'):
        help_class = "ADV"
    else:
        help_class = "OTHER"

    # TODO: Could insert a check here to confirm none of the variables are NoneTypes
    ## and if nonetype, then insert string "CHECK"

    return {
        "helpDV": help_dv,
        "helpClass": help_class,
        "helpTag": help_tag,
        "verbAfterHelp": verb_after_help,
        "interveningWords": intervening_words,
        "objPresent": obj_present,
        "objPronoun": obj_pronoun,
        "objLength": obj_length,
        "objHead": obj_head
    }

# Function to start the right_checks
def start_right_checks(tagged_kwic_words, help_hit, following_word_of_hit):
    """
        All right context checks

        Args:
            tagged_kwic_words = list of the tagged words in the KWIC
            help_hit = the particular help hit we're looking for (since there may be more than one in a given KWIC)
                (eg, help, helps)
            preceding_word_of_hit = word before help (used to ensure correct help occurrence chosen)
                Will always have something in right comtext since punctuation in there
        Returns:
            Dictionary of various help verb and right context properties
        """
    # -------------------------------------------
    # Getting help positions
    # -------------------------------------------
    # Finding all instances of help in tagged KWICs
    help_pattern = r'\w+_help\w*_\d+_\w+_\d+_\w+_\w+'
    help_positions = [] # list of places in tagged_kwic_words where help found

    # Since may be more than one hit
    for i, word in enumerate(tagged_kwic_words):
        if re.search(help_pattern, word, re.IGNORECASE):
            help_positions.append(i)

    # -------------------------------------------
    # Start loop for right checks
    # -------------------------------------------
    # Going through each occurrence of help
    for pos in help_positions:
        if len(help_positions) == 1:
            return analyse_right_context(tagged_kwic_words, pos)
        elif pos + 1 < len(tagged_kwic_words) and tagged_kwic_words[pos].split('_')[1] == help_hit and tagged_kwic_words[pos+1].split('_')[1] == following_word_of_hit:
            return analyse_right_context(tagged_kwic_words, pos)
        else:
            continue

    # Return flags to check hit variables if cannot find correct occurrence of hit
    return {
        "helpDV": "CHECK",
        "helpClass": "CHECK",
        "helpTag": "CHECK",
        "verbAfterHelp": "CHECK",
        "interveningWords": "CHECK",
        "objPresent": "CHECK",
        "objPronoun": "CHECK",
        "objLength": "CHECK",
        "objHead": "CHECK"
    }

# Dylan's analysis 
"""
Primarily looks at left context texts
"""
# help_polarity *DV
def check_help_polarity(left_context_tokens, window_size=5):
    """Checks for negation words before 'help'."""
    negation_words = {'not', "n't", 'nor', 'never', 'hardly', 'scarcely', 'barely', 'no', 'nobody', 'nothing', 'nowhere', 'none', 'neither'}
    window = left_context_tokens[-window_size:]
    window_lower = [word.lower() for word in window]
    for word in window_lower:
        if word in negation_words:
            return 'NEG'
    return 'POS'

# preceding_to *DV
def check_preceding_to(left_context_tokens, is_help_verb=True):
    """Checks if 'to' appears within the 4 words immediately preceding 'help'."""
    if not is_help_verb:
        return 'NA'
    window = left_context_tokens[-4:]
    window_lower = [word.lower() for word in window]
    if 'to' in window_lower:
        return 'YEStoBefore'
    return 'NOtoBefore'



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
            "voice": "NA"
        }

    # --- Analysis for Verbs Only ---
    # --- Voice Analysis (Active/Passive) ---
    voice = "Active"
    # Check for passive auxiliary verb attached to the target token
    for child in target_token.children:
        if child.dep_ == "auxpass":
            voice = "Passive"
            break
    # Also check if the subject is a passive subject
    if voice == "Active": # no need to check if already found
        for child in target_token.children:
            if child.dep_ == "nsubjpass":
                voice = "Passive"
                break
    
    left_context_tokens = [t.text for t in doc[:target_idx]]
    polarity = check_help_polarity(left_context_tokens)
    preceding_to = check_preceding_to(left_context_tokens, is_help_verb=True)

    # subj_type, subj_head, subj_animacy *DV
    
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
    # lemma_verb *DV
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
        "voice": voice
    }


# ---------------------------------------------------------------------------------------------------------
# PROCESSING LOGIC
# ---------------------------------------------------------------------------------------------------------

# Folder containing files to analyse
hansard_dir = "/Users/muhammadmushoffa/Desktop/corpus_linguistic/Hansard 2000 file sample"

kwics_file = "/Users/muhammadmushoffa/Desktop/corpus_linguistic/hansard_kwics_only.csv"

complete_kwics_file = "/Users/muhammadmushoffa/Desktop/corpus_linguistic/hansard_results.csv"

# New csv file to write results to
df = pd.DataFrame(columns=["File", "Hit", "LeftContext", "TargetWord", "RightContext", 
                           "DepVar", "HelpClass", "HelpInflection", "VerbLemma", 
                           "InterveningWords", "ObjPresent", "ObjPronoun", "ObjLength", "ObjHead",
                           "HelpPolarity", "PrecedingTo", "SubjType", "SubjHead", "SubjAnimacy",
                           "CompLemma", "CompTag", "Voice"])
# Making csv of KWICs
print("Now finding KWICs")
find_kwics(hansard_dir, r'[^ ]*help\w*\b', kwics_file)

# Calculating time taken for extraction stage
stage_1_end_time = time.time()
elapsed = stage_1_end_time - start_time
hours1, remainder = divmod(elapsed, 3600)
minutes1, seconds1 = divmod(remainder, 60)

print(f"Elapsed time so far: {int(hours1):02d}:{int(minutes1):02d}:{seconds1:05.2f}")

# Opening kwics_file to read off rows
print("KWICs found. Now analysing them.")
csvKwics = pd.read_csv(kwics_file, encoding = 'utf8')

rows = csvKwics.shape[0]
# Going through each KWIC
for i in range(rows):
    full_kwic = f"{csvKwics['LeftContext'][i]} {csvKwics['TargetWord'][i]} {csvKwics['RightContext'][i]}"
    # Retrieve Metadata here
    
    
    
    #  Tag KWIC
    tagged_kwic = nlp(full_kwic)
    
    
    
    # Failed try :( 
    # left_analysis['help_polarity'] = check_help_polarity(csvKwics['LeftContext'][i].split())
    # left_analysis['preceding_to'] = check_preceding_to(csvKwics['LeftContext'][i].split())
  
    # # Left context words 
    # left_text = csvKwics['LeftContext'][i]
    # left_token_count = len(left_text.split())
    # target_start_idx = left_token_count
    
    # left_context_tokens = [token for token in tagged_kwic if token.i < target_start_idx]
    # right_context_tokens = [token for token in tagged_kwic if token.i > target_start_idx]
    # target_token = tagged_kwic[target_start_idx]
    # left_analysis = {}
    # right_analysis_do = {}
    # # Always do polarity and preceeding_to 
    # left_analysis['help_polarity'] = check_help_polarity(left_text.split())
    # left_analysis['preceding_to'] = check_preceding_to(left_text.split())
    
    # if target_token.pos_ != 'VERB':
    #     left_analysis['subj_type'] = 'NA'
    #     left_analysis['subj_head'] = 'NA'
    #     left_analysis['subj_animacy'] = 'NA'
    #     right_analysis_do['comp_lemma'] = 'NA'
    #     right_analysis_do['comp_tag'] = 'NA'
    # else:
    #     left_analysis['help_polarity'] = check_help_polarity(left_text.split())
    #     left_analysis['preceding_to'] = check_preceding_to(left_text.split())
    #     left_analysis['subj_type'],left_analysis['subj_head'],left_analysis['subj_animacy'] = check_subject(left_context_tokens)
    #     right_analysis_do['comp_lemma'], right_analysis_do['comp_tag'] = check_lemma_comp_tag(right_context_tokens)
  
    # New try 
    dylan_analysis = analyze_hansard_hit(full_kwic, csvKwics['TargetWord'][i])
    print("Analysis")
    print("---"*20)
    print(dylan_analysis)
    print("---"*20)
    
    

    





    # Right context words 
    # right_context_words = csvKwics['RightContext'][i].split()

    # Getting individual tokens
    string = ""
    for sentence in tagged_kwic.sents:
        
        for token in sentence:
            # I omit _SP_ here!
            if not token.is_space:
                # noNE if no named entity
                ne = token.ent_type_ if token.ent_type_ else 'noNE'
                # Add final space to separate token from next one
                string += f'{token.tag_}_{token.text}_{token.i}_{token.dep_}_{token.head.i}_{token.lemma_}_{ne} '
    
    # List comprehension possibly faster idk lol :) 
    # Instead of the nested for loop, use list comprehension
    # string = ' '.join([
    #     f'{token.tag_}_{token.text}_{token.i}_{token.dep_}_{token.head.i}_{token.lemma_}_{token.ent_type_ if token.ent_type_ else "noNE"} '
    #     for sentence in tagged_kwic.sents
    #     for token in sentence
    #     if not token.is_space
    # ])
    
    tagged_words = string.split()

    # Getting right context stuff
    # If last character of the following word is not a letter or number and length of following word does not equal 1,
    # remove that punctuation
    if not csvKwics['RightContext'][i].split()[0][-1].isalpha() and len(csvKwics['RightContext'][i].split()[0]) != 1:
        right_analysis = start_right_checks(tagged_words, csvKwics['TargetWord'][i],
                                            re.sub(r'[^\w\s]$', '', csvKwics['RightContext'][i].split()[0]))
    # if it is alphanumeric, just use the following word as is
    else:
        right_analysis = start_right_checks(tagged_words, csvKwics['TargetWord'][i],
                                            csvKwics['RightContext'][i].split()[0])



    


    # Writing results
    # TODO: Replace "File" with metadata
    # 
    # if right_analysis or left_analysis:
    #     new_row = pd.DataFrame(
    #         [{"File": csvKwics["File"][i], 
    #          "Hit": csvKwics["Hit"][i],
    #           "LeftContext": csvKwics["LeftContext"][i],
    #           "TargetWord": csvKwics["TargetWord"][i], 'RightContext': csvKwics['RightContext'][i],
    #           "DepVar": right_analysis["helpDV"], "HelpClass": right_analysis["helpClass"],
    #           "HelpInflection": right_analysis["helpTag"], "VerbLemma": right_analysis["verbAfterHelp"],
    #           "InterveningWords": right_analysis["interveningWords"], "ObjPresent": right_analysis["objPresent"],
    #           "ObjPronoun": right_analysis["objPronoun"], "ObjLength": right_analysis["objLength"],
    #           "ObjHead": right_analysis["objHead"]}])

    #     df = pd.concat([df, new_row], ignore_index=True)

        # Writing results
    if dylan_analysis:
        new_row = pd.DataFrame(
            [{"File": csvKwics["File"][i], 
            "Hit": csvKwics["Hit"][i],
            "LeftContext": csvKwics["LeftContext"][i],
            "TargetWord": csvKwics["TargetWord"][i], 
            'RightContext': csvKwics['RightContext'][i],
            "DepVar": right_analysis.get("helpDV", "NA") if right_analysis else "NA", 
            "HelpClass": right_analysis.get("helpClass", "NA") if right_analysis else "NA",
            "HelpInflection": right_analysis.get("helpTag", "NA") if right_analysis else "NA", 
            "VerbLemma": right_analysis.get("verbAfterHelp", "NA") if right_analysis else "NA",
            "InterveningWords": right_analysis.get("interveningWords", "NA") if right_analysis else "NA", 
            "ObjPresent": right_analysis.get("objPresent", "NA") if right_analysis else "NA",
            "ObjPronoun": right_analysis.get("objPronoun", "NA") if right_analysis else "NA", 
            "ObjLength": right_analysis.get("objLength", "NA") if right_analysis else "NA",
            "ObjHead": right_analysis.get("objHead", "NA") if right_analysis else "NA",
            "HelpPolarity": dylan_analysis.get('polarity', 'NA'),
            "PrecedingTo": dylan_analysis.get('preceding_to', 'NA'),
            "SubjType": dylan_analysis.get('subj_type', 'NA'),
            "SubjHead": dylan_analysis.get('subj_head', 'NA'),
            "SubjAnimacy": dylan_analysis.get('subj_animacy', 'NA'),
            "Voice": dylan_analysis.get('voice', 'NA'),
            "CompLemma": dylan_analysis.get('comp_lemma', 'NA'),
            "CompTag": dylan_analysis.get('comp_tag', 'NA'),
            "WordCount": csvKwics.get("WordCount", "NA")[i] if "WordCount" in csvKwics.columns else "NA",
            "SittingType": csvKwics.get("SittingType", "NA")[i] if "SittingType" in csvKwics.columns else "NA",
            "SittingDate": csvKwics.get("SittingDate", "NA")[i] if "SittingDate" in csvKwics.columns else "NA",
            "FileId": csvKwics.get("FileId", "NA")[i] if "FileId" in csvKwics.columns else "NA",
            "Title": csvKwics.get("Title", "NA")[i] if "Title" in csvKwics.columns else "NA"}])
    
        df = pd.concat([df, new_row], ignore_index=True)


# Record results
df.to_csv(complete_kwics_file, index=False, encoding='utf-8')

# Calculating time taken
end_time = time.time()
elapsed = end_time - start_time
hours, remainder = divmod(elapsed, 3600)
minutes, seconds = divmod(remainder, 60)

print(f"Start time: {start_time}")
print(f"End time: {end_time}")
print(f"Running time: {int(hours):02d}:{int(minutes):02d}:{seconds:05.2f}")

# ---------------------------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------------------
# END
# ---------------------------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------------------