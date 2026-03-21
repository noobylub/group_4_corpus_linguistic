# Whole script for Hansard generating csv for right context stuff only
# UPDATES 21/03/26
# Removed regex deleting punctuation straight after help; replaced with moving punvtuation to right context

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

# Function to gets KWICs out as csv file
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
                               "ObjPronoun", "ObjLength", "ObjHead"])

    total_matches = 0 # Total help matches found

    # Checking have text files
    for filename in os.listdir(directory):
        # checks if needed
        if filename.endswith('.txt'):
            file_list.append(filename)
        else:
            print(f"{filename} could not be processed.")

    for filename in file_list:
        f = rf"{directory}\{filename}"
        with (open(f, 'r', encoding="utf8") as textfile):
            text_content = textfile.read()

            # --------------------------------------------------------------------
            # Pre-processing
            # --------------------------------------------------------------------
            # TODO: More pre-processing needed

            # Replacing with space
            repl_with_space = ["\n", "^", 'â€”']

            for item in repl_with_space:
                text_content = text_content.replace(item, ' ')

            # Replacing *+ with pound symbol
            text_content = text_content.replace("*+", "£")

            # Replacing with nothing:
            repl_with_nothing = [r'\*\<\*\d+', r'\*\d+']

            for item in repl_with_nothing:
                text_content = re.sub(item, "", text_content)

            # Replacing speaker tags with nothing
            text_content = text_content.replace('<speaker>', '').replace('</speaker>', '')

            # words = word_tokenize(text_content)
            words = text_content.split()

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

                new_row = pd.DataFrame([{"File": filename, "Hit": total_matches, 'LeftContext': left_context,
                      'TargetWord': target_wd, 'RightContext': right_context}])

                df = pd.concat([df, new_row], ignore_index=True)


    df.to_csv(output_path, index=False, encoding='utf-8')

    print(f"\nExtraction complete. Total matches found: {total_matches}")


# Function to find the object head
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
        if parts[3] == desired_dependency:

            # Get the index of word's dependency relation
            parent_index = int(parts[4])

            # Go to the parent token see if its lemma is help
            parent_parts = tagged_text_words[parent_index].split('_')

            # Return word if its parent's lemma is 'help'
            if parent_parts[5].lower() == desired_parent_lemma:
                return word

    # If have not found head from above, return 7-part to-do string for further review
    return "TODO_TODO_TODO_TODO_TODO_TODO_TODO"


def analyse_right_context(tagged_kwic_words):
    """
    All right context checks

    Args:
        tagged_kwic_words = list of the tagged words in the KWIC

    Returns:
        Dictionary of various help verb and right context properties
    """
    # -------------------------------------------
    # Getting help positions
    # -------------------------------------------
    # Finding all instances of help in tagged KWICs
    help_pattern = r'\w+_help\w*_\d+_\w+_\d+_\w+_\w+'
    help_positions = []

    # Since may be more than one hit
    for i, word in enumerate(tagged_kwic_words):
        if re.search(help_pattern, word, re.IGNORECASE):
            help_positions.append(i)

    # -------------------------------------------
    # Start loop for right checks
    # -------------------------------------------
    # Going through each occurrence of help
    for pos in help_positions:
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

        help_dv = "CHECK" # TO, BARE, ING, INING, NA
        help_class = "CHECK" # VERB, NOUN, ADJ, ADV, OTHER
        intervening_words = 0 # Intervening words between help and infinitive
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
        obj_pn_len_1 = False # Flag for if found pn like 'them', 'him' (so obj_length must be 1)
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

            next_tagged_word = tagged_kwic_words[pos + i] # PRP_them_550_dobj_549_they_noNE
            parts = next_tagged_word.split('_')
            next_tag = parts[0] # Ex: PRP, TO, IN, VB
            next_word = parts[1] # token text
            next_index = parts[2] # index within whole file
            next_depend = parts[3] # dependency relation (eg, dobj, aux, xcomp)
            next_head_index = parts[4] # index of next word's head
            next_lemma = parts[5] # lemma

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
                                              'themself', 'themselves', 'itself',
                                              'this', 'that']):
                    obj_pronoun = "PRO"
                    obj_pn_len_1 = True
                    found_object = True
                elif next_word.lower() in ['someone', 'anyone', 'who', 'this', 'that']:
                    obj_pronoun = "PRO"
                    found_object = True
                # If not a pronoun, check other potential object types
                else:
                    if next_tag in ['NN', 'NP', 'NNS', 'NNP', 'NNPS', 'DT', 'CD', 'WP','PRP$']:
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
            if not found_bare and not found_in and not found_ing and next_tag == 'TO' or next_word.lower() == 'to':
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
                                                                                   'HVG','BEG'] and next_word not in [
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
                obj_present = "Yes" # dobj present
                # Ensuring pronouns like 'them', 'him' are obj_length = 1
                if obj_pn_len_1:
                    obj_length = 1
                else:
                    obj_length = obj_length_counter

                # Recording obj head
                obj_head_parts = head_hunting(tagged_kwic_words, obj_words, "dobj", "help").split('_')
                obj_head = obj_head_parts[1]

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


# ---------------------------------------------------------------------------------------------------------
# PROCESSING LOGIC
# ---------------------------------------------------------------------------------------------------------

# Folder containing files to analyse
hansard_dir = r"C:\Users\helen\OneDrive - The University of Manchester\Corpus Linguistics\Hansard_samples\Hansard Medium Sample"

kwics_file = r"C:\Users\helen\OneDrive - The University of Manchester\Corpus Linguistics\Hansard_samples\hansard_med_kwics_only_v2.csv"

complete_kwics_file = r"C:\Users\helen\OneDrive - The University of Manchester\Corpus Linguistics\Hansard_samples\hansard_med_results_v2.csv"

# New csv file to write results to
df = pd.DataFrame(columns=["File", "Hit", "LeftContext", "TargetWord", "RightContext", "DepVar", "HelpClass",
                               "HelpInflection", "VerbLemma", "InterveningWords", "ObjPresent",
                               "ObjPronoun", "ObjLength", "ObjHead"])

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

    # Tag KWIC
    tagged_kwic = nlp(full_kwic)

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

    tagged_words = string.split()

    # Getting right context stuff
    right_analysis = analyse_right_context(tagged_words)

    # TODO: Get left context stuff

    # Writing results
    # TODO: Replace "File" with metadata
    if right_analysis:
        new_row = pd.DataFrame(
            [{"File": csvKwics["File"][i], "Hit": csvKwics["Hit"][i], "LeftContext": csvKwics["LeftContext"][i],
              "TargetWord": csvKwics["TargetWord"][i], 'RightContext': csvKwics['RightContext'][i],
              "DepVar": right_analysis["helpDV"], "HelpClass": right_analysis["helpClass"],
              "HelpInflection": right_analysis["helpTag"], "VerbLemma": right_analysis["verbAfterHelp"],
              "InterveningWords": right_analysis["interveningWords"], "ObjPresent": right_analysis["objPresent"],
              "ObjPronoun": right_analysis["objPronoun"], "ObjLength": right_analysis["objLength"],
              "ObjHead": right_analysis["objHead"]}])

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