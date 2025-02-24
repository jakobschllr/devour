from shorten_transcript import shorten_transcript
import json
import re
from pathlib import Path
from nltk.tokenize import sent_tokenize


def get_sentences(text):
    sentences = sent_tokenize(text, language="german")
    # save each sentence separate in list
    for i in range(0, len(sentences)):
        sentences[i] = re.sub('\n', '', sentences[i]).lstrip().lower()
        sentences[i] = sentences[i].replace("#", "").replace("*", "")
    return sentences

def save_as_json(data, departement_name, num):

    try:
        whole_text = ""
        separate_paragraphs = []

        for key, value in data.items():
            if key.lower() != 'meeting_subject' and key.lower() != 'meeting_info' and key.lower() != 'departement_info' and key.lower() != 'participants_info':
                whole_text += value
                whole_text += " "

                label = data['meeting_subject'] + " " + key.replace("_", " ")
                text = value

                paragraph = {
                    label: text
                }

                separate_paragraphs.append(paragraph)


        separate_sentences = get_sentences(whole_text)

        whole_text_with_label = {
            data['meeting_subject']: whole_text
        }

        data_for_vector_db = {
            "whole_text": whole_text_with_label,
            "paragraphs": separate_paragraphs,
            "sentences": separate_sentences,
            "persons_info": data["participants_info"],
            "meeting_data": data["meeting_info"]
        }

    except Exception as e:
        return "Exception occured when parsing json data: ", e


    try:
        with open(f"/home/jakobschiller/devour/data_extraction/vector-database/{departement_name}/data_{num}.json", "w") as file:
            json.dump(data_for_vector_db, file)
            return f"Summary saved to data_{num}.json ✅"
        
    except Exception as e:
        return "Exception occured when trying to save file: " + e
    
def start_data_extraction():
    departement_name = "purchasing_departement"
    departement_path = Path(f"/home/jakobschiller/devour/data_extraction/transcripts/{departement_name}")
    transcripts_paths = [str(datei) for datei in departement_path.iterdir() if datei.is_file()]

    print("\nThese transcripts will be analyzed: ")
    for transcript in transcripts_paths:
        print("- ", transcript)

    print("\n")
    for i in range(0, len(transcripts_paths)):
        path = transcripts_paths[i]
        transcript_data = shorten_transcript(path)
        transcript_data_dict = json.loads(transcript_data.split('json')[1].replace('\n', '').replace("```", ""))
        response = save_as_json(transcript_data_dict, departement_name, i+1)
        print(response)
    
    print("\n")

start_data_extraction()