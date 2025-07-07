import ollama
import requests
import json
import os
from dotenv import load_dotenv

department = "Einkauf"

def shorten_transcript(transcript):

    prompts = [
        f"""
        Analysiere das folgende Meeting-Transkript und extrahiere präzise das darin enthaltene Wissen.
        Formuliere einen ausführlichen, kohärenten Fließtext auf Deutsch, der die gewonnenen Informationen
        verständlich und detailliert beschreibt. Schreib dabei allgemein über die Informationen, unabhängig vom Meeting,
        man soll nicht sehen, dass die Informationen aus einem Meeting stammen. Konzentriere dich ausschließlich auf fachliche Inhalte und
        dokumentiere Wissen über Personen, Organisationsstrukturen, Prozesse, Anleitungen, Vorgänge, Zuständigkeiten,
        Regularien, Vorgaben und Arbeitsabläufe.
        Stelle sicher, dass jeder Prozess und jeder Ablauf exakt in der Reihenfolge wiedergegeben wird, in der er im
        Transkript erläutert wurde. Der Text soll durchgehend fließend geschrieben sein, ohne Aufzählungen, Stichpunkte,
        Nummerierungen oder sonstige strukturelle Elemente wie Überschriften oder Absätze.
        Falls Namen von Personen vorkommen, verwende stets Vor- und Nachnamen. Unwesentliche oder informelle Gespräche,
        persönliche Meinungen und irrelevante Randinformationen sollen nicht berücksichtigt werden.
        Verwende eine sachliche, professionelle Sprache, die sich für eine strukturierte Wissensdatenbank eignet.
        
        Dein Antwort soll einer JSON-Struktur entsprechen. Ganz am Anfang soll es einen Key geben der immer
        "meeting_subject" heißt und dessen Value ein String ist, der in wenigen Wörten den Inhalt des gesamten Meetings beschreibt.

        Danach sollst du den gesamten Fließtext in einzelne Sinnabschnitte unterteilen und jedem dieser Sinnabschnitte ein kurzes
        prägnantes Label geben, das den jeweiligen Abschnitt beschreibt. Für jeden Abschnitt gibt es dann ein Key-Value-Paar. Das Label eines Abschnitts ist jeweils der Key und der Value
        dazu ist der Abschnitt des Fließtextes als String. Die Labels sollen eindeutig auf den Inhalt des Abschnittes hinweisen, sodass man nur anhand des 
        Labels weiß worum es im Abschnitt geht. Die Labels werde nachher in einer Vektordatenbank darauf hinweisen, worum
        es im Abschnitt geht, daher müssen sie für sich alleine ohne Kontext anderer Labels den Inhalt des Abschnittes beschreiben.
        Die Values sollen immer der Fließtext des Abschnittes sein als String ohne weitere Verschachtelung.

        Danach soll es immer einen Key geben, der immer "department_info" heißt. Der dazugehörige Value kurzer Fließtext als String, der alle Informationen über die
        Abteilung {department} nennt, die man aus dem Transkript über die Abteilung entnehmen kann.

        Danach gibt es einen Key der immer "participants_info" heißt und dessen Value eine Liste ist. Die Liste soll für jeden im Meeting teilnehmenden Teilnehmer einen Text als
        String enthalten der den Namen des Mitarbeiters nennt, was generell seine Aufgaben sind, nicht nur im Bezug auf das Meeting und was seine Position im Unternehmen ist. Falls
        dazu keine Informationen aus dem Transkript ersichtlich sind, lasse es einfach leer.
        
        Am Schluss der JSON-Datei soll noch ein Key mit Informationen zum Meeting stehen. Der Key soll immer "meeting_info" heißen. Der Value immer aus zwei
        zwei Key-Value-Paaren bestehen. Der erste Key heißt immer "date" und hat als Value immer das Wort "meeting" und das Datum des Meeings als String im Format:  Meeting vom DD.MM.YYYY DD. MONATSNAME YYYY.
        Ist das Datum des Meetings nicht ersichtlich schreibe einfach "datum nicht bekannt".
        Das zweite Key-Value-Paar heißt immer "content" und der Value dazu soll ein Fließtext als String sein, der beschreibt wann das Meeting war, wer teilgenommen hat
        und kurz sagt welche Themen besprochen wurden und welche Handlungen und Aufgaben aus dem Meeting resultieren.
        
        
        Hier ist die Vorlage für die JSON-Datei:

        {{
            "meeting_subject": "",
            "detailliertes_label_für_abschnitt": "",
            "detailliertes_label_für_abschnitt": "",
            "detailliertes_label_für_abschnitt": "",
            "department_info": "",
            "participants_info": [],
            "meeting_info": {{
                "date": "",
                "content": "",
            }},
        }}
        
        Antworte nur mit dieser JSON-Datei ohne eine Einleitung oder abschließende Bemerkungen.
        Transkript:\n+ {transcript}""",
        f"""
        Analysiere das folgende Meeting-Transkript und extrahiere präzise das darin enthaltene Wissen.
        Formuliere einen ausführlichen, kohärenten Fließtext auf Deutsch, der die gewonnenen Informationen
        verständlich und detailliert beschreibt. Schreib dabei allgemein über die Informationen, unabhängig vom Meeting,
        man soll nicht sehen, dass die Informationen aus einem Meeting stammen. Konzentriere dich ausschließlich auf fachliche Inhalte und
        dokumentiere Wissen über Personen, Organisationsstrukturen, Prozesse, Anleitungen, Vorgänge, Zuständigkeiten,
        Regularien, Vorgaben und Arbeitsabläufe.
        Stelle sicher, dass jeder Prozess und jeder Ablauf exakt in der Reihenfolge wiedergegeben wird, in der er im
        Transkript erläutert wurde. Der Text soll durchgehend fließend geschrieben sein, ohne Aufzählungen, Stichpunkte,
        Nummerierungen oder sonstige strukturelle Elemente wie Überschriften oder Absätze.
        Falls Namen von Personen vorkommen, verwende stets Vor- und Nachnamen. Unwesentliche oder informelle Gespräche,
        persönliche Meinungen und irrelevante Randinformationen sollen nicht berücksichtigt werden.
        Verwende eine sachliche, professionelle Sprache, die sich für eine strukturierte Wissensdatenbank eignet.
        Deine Antwort soll ausschließlich aus dem geforderten Fließtext bestehen. Schreibe direkt den Inhalt ohne
        eine Einleitung oder abschließende Bemerkungen. Transkript:\n{transcript}
        """, # klappt gut mit Gemini
        f"""
        Erstelle eine sehr detaillierte und ausführliche Zusammenfassung als Fließtext, die das genannte Wissen dieses 
        Transkripts  aufführt und private Dinge die Personen gegebenenfalls gesagt haben weglässt. Nutze keinerlei 
        Aufführungszeichen wie Stichpunkte und auch keine Nummerierung. Nutze die Vor- und Nachnamen aller Teilnehmer, 
        wenn du sie erwähnst. Lasse keine fachlichen Informationen weg. Antworte auf Deutsch und ausschließlich mit 
        der deutschen Zusammenfassung. Transkript:\n{transcript}
        """,
        f"""Schreibe einen langen detaillierten Fließtext auf Deutsch, der das enthaltene Wissen über Personen, 
        Organisationsstrukturen, Prozesse, Anleitungen, Vorgänge, Zuständigkeiten, Regularien, Vorgaben und Arbeitsabläufe, die 
        in dem Transkript genannt werden, genau erklärt. Wenn Prozesse und Abläufe erklärt werden, gebe jeden Schritt wie
        er im Transkript erklärt wird genau in deinem Text wieder. Der Text soll keine Auflistungszeichen wie -, # oder * enthalten und keine 
        Nummerierungen. Wenn du Namen von Teilnehmern nutzt, nutze immer Vor- und Nachname. Lasse Informationen weg, 
        die nicht fachlich sind. Erwähne ansonsten alle Details. Deine Antwort soll ausschließlich aus dem Fließtext 
        bestehen. Hier ist das Transkript:\n{transcript}
        """,
        f"""
        Du bist ein KI-Assistent mit der Aufgabe, eine detaillierte und handlungsorientierte Zusammenfassung aus dem 
        bereitgestellten Besprechungsprotokoll zu erstellen. Bitte analysiere das gesamte Protokoll und liefere Folgendes:
        1. Liste die Hauptthemen auf, die während des Meetings besprochen wurden.
        2. Für jedes identifizierte Thema:
            - liefere detaillierte Notizen
            - erläutere alle verwendeten Akronyme
            - erfasse alle relevanten besprochenen Details, formatiert für einfache Lesbarkeit
            - verwende Aufzählungspunkte, nummerierte Listen und klare Informationshierarchien, wo angemessen
        3. Hebe wichtige Entscheidungen hervor, die während des Meetings getroffen wurden
        4. Erstelle einen separaten Abschnitt für Aktionspunkte, in dem klar angegeben wird:
            - was getan werden muss
            - wer für jede Aufgabe verantwortlich ist
            - alle festgelegten Fristen
        5. Füge Abschnitt für offene Fragen oder Anliegen hinzu, die eine Nachverfolgung erfordern
        6. Fasse die wichtigsten Erkenntnisse aus dem Meeting in 2-3 Sätzen zusammen
        Bitte strebe nach maximaler Detailgenauigkeit und Präzision, formuliert als ein Fließtext in klarer Sprache und auf Deutsch. Vermeide Kürzungen
        oder übermäßige Zusammenfassungen, um sicherzustellen, dass keine wichtigen Informationen verloren gehen. 
        Transkript:\n{transcript}
        """,
    ]

    models = [
        "mistral:7b",
        "zephyr:7b",
        "llama2",
        "deepseek-r1:7b", # if deepseek is used the thinking process in the answer must be filtered out
        "glm4:9b",
        "sroecker/sauerkrautlm-7b-hero",
        "llama3.1:8b",
        "llama3.2:3b"
    ]

    temperature = 0.1 # from 0.1 to 1.0; the higher the temperature the more creative but less prezise answers
    max_tokens = 16384
    top_p = 1.0 # only those next possible tokens are considered, whose cumulated probalities don't extend the top-p value 


    load_dotenv()
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

    headers = {
        "Content-Type": "application/json"
    }

    data = {
        "contents": [{
            "parts": [{"text": prompts[0]}]
        }]
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))
    return response.json()['candidates'][0]['content']['parts'][0]['text']



def get_transcript(path):
    text = ""
    with open(path, "r+") as file:
        lines = file.readlines()

        for line in lines:
            # only look at not empty lines
            if len(line) > 1:
                text += line + " "
        
    return text