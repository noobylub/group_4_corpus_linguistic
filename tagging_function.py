# Import libraries, resources, initialise spacy nlp pipeline

import nltk
nltk.download("punkt")
nltk.download("punkt_tab")
from nltk.tokenize import word_tokenize

import spacy
nlp = spacy.load("en_core_web_lg")
nlp.max_length = 2000000

# --------------------------------------------------------------------------
# POS TAGGING AND DEPENDENCY PARSING
#---------------------------------------------------------------------------
def tag_file(file_path):
    """
    Tags and dependency parses a pre-processed .txt file

    Args:
        Pre-processed .txt file

    Returns:
        Saves a .txt file of the tagged and dependency-parsed corpus

        Example of tagged word: NNS_contents_17_dobj_15_content_noNE
        0: Penn POS tag
        1: token text
        2: index within whole file (17th token in this case)
        3: its dependency relation
        4: index of its head
        5: token lemma
        6: named entity (eg, PERSON if token is someone's name, as in NNP_Komaroff_75_pobj_73_Komaroff_PERSON)
    """
    # Open file
    with open(file_path, "r", encoding="utf8") as textfile:
        string = textfile.read()

        # Tag file
        print("Now tagging file")
        tagged = nlp(string)

    # Write a new .txt file for tagged and dependency parsed text
    # New file saved in same directory as original file
    print("Now creating tagged file")
    with open(file_path.replace('.txt', '') + "_parsed.txt", "w", encoding="utf8") as f:
        # Go through each sentence
        for sentence in tagged.sents:
            # New line for each sentence
            f.write("\n")
            for token in sentence:
                # Ignore _SP_
                if not token.is_space:
                    # noNE if no named entity
                    ne = token.ent_type_ if token.ent_type_ else 'noNE'
                    # Add final space to separate token from next one
                    f.write(f'{token.tag_}_{token.text}_{token.i}_{token.dep_}_{token.head.i}_{token.lemma_}_{ne} ')


# --------------------------------------------------------------------------
# CALLING FUNCTION
#---------------------------------------------------------------------------
# Location of help KWIC file
Hansard_2000_KWIC = r"C:\Users\helen\Downloads\help_all_files.txt"

# Calling function on above file
tag_file(Hansard_2000_KWIC)






