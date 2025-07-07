from datetime import datetime, timedelta
from django.conf import settings
from django.utils.timezone import now

# my_set = []

# my_set.append("Bing")
# my_set.append("Bang")

# para = [
#         {
#             "Digitalisierung der Bestellprozesse im Einkauf Testphase und Probleme": "Eine Testphase mit 25 simulierten automatischen Bestellungen im neuen ERP-Modul zeigte in 20% der F\u00e4lle Probleme.  Insbesondere traten doppelte Bestellereing\u00e4nge und Unstimmigkeiten bei der Budgetzuordnung auf. Fehlermeldungen resultierten aus Schnittstellenproblemen zur Finanzabteilung, was zu Freigabeverz\u00f6gerungen f\u00fchrte.  Die daraus resultierenden finanziellen Herausforderungen bestehen in m\u00f6glichen Budget\u00fcberschreitungen im laufenden Quartal aufgrund fehlerhafter Budgetzuordnungen bei Bestellungen."
#         },
#         {
#             "Digitalisierung der Bestellprozesse im Einkauf IT-Anpassungen und Dashboard": "Die IT-Abteilung arbeitet an der Verbesserung der Daten-Synchronisation zwischen dem Bestellmodul und der Finanzbuchhaltung. Ein Update soll innerhalb der n\u00e4chsten zwei Wochen ausgerollt werden.  Ein tempor\u00e4rer Filter blockiert bis dahin doppelte Bestellungen.  Parallel dazu wird ein Echtzeit-Dashboard entwickelt, das den \u00dcberblick \u00fcber automatische Bestellungen, Warteschlangen, Fehler und die Budgetzuordnung erm\u00f6glicht und bei Abweichungen Warnmeldungen ausgibt. Ein erster Prototyp soll in K\u00fcrze vorgestellt werden."
#         },
#         {
#             "Digitalisierung der Bestellprozesse im Einkauf Operative Herausforderungen und Qualit\u00e4tsmanagement": "Aus operativer Sicht k\u00f6nnen in Sto\u00dfzeiten bei vielen manuellen Eingaben Verz\u00f6gerungen bei der Daten\u00fcbertragung auftreten.  Eine kontinuierliche \u00dcberwachung der Systemauslastung soll Engp\u00e4sse fr\u00fchzeitig erkennen.  Aus der Logistik wird ein automatisiertes Sendungsverfolgungssystem als Vorbild genannt, welches durch Mitarbeiterschulungen und ein manuelles Override-System erg\u00e4nzt wird.  Das Qualit\u00e4tsmanagement hat bisher keine signifikanten qualit\u00e4tsrelevanten Fehler festgestellt, aber kleinere Unstimmigkeiten in den Daten.  Ein regelm\u00e4\u00dfiger Datenabgleich zur Sicherstellung der Datenkorrektheit wird angestrebt."
#         },
#         {
#             "Digitalisierung der Bestellprozesse im Einkauf Dokumentation Schulungen und Notfallmanagement": "Es wird ein detailliertes Fehlerprotokoll mit allen Problemen und deren zeitlicher Einordnung gef\u00fchrt.  Schulungen zum neuen System mit Fokus auf Dashboard-Bedienung und manuelles Override sind geplant, inklusive eines Schulungsvideos und praktischer Workshops. Ein Notfallplan f\u00fcr einen Totalausfall des automatisierten Systems existiert in Form eines ersten Entwurfs, der einen Fallback auf das alte System und eine Notfall-Taskforce vorsieht.  Im Notfall m\u00fcssen alle Prozesse dokumentiert sein und ein klarer Kommunikationsplan existieren, um finanzielle Unstimmigkeiten zu vermeiden. "
#         },
#         {
#             "Digitalisierung der Bestellprozesse im Einkauf Systemintegration und weitere Ma\u00dfnahmen": "Ein interdisziplin\u00e4rer Workshop soll die Integration des neuen Systems in den gesamten Beschaffungsprozess (Einkauf, IT, Logistik, Produktion, Finanz) optimieren und Schnittstellenprobleme fr\u00fchzeitig l\u00f6sen.  Regelm\u00e4\u00dfige Feedbackrunden nach dem Live-Betrieb des Systems zur schnellen Reaktion auf unerwartete Probleme sind angedacht.  Alle auftretenden Probleme sollen zentral erfasst werden, um beim n\u00e4chsten Update eine fundierte Analyse zu erm\u00f6glichen."
#         }
#     ]
# paragraphs = []
# paragraph_titel = []

# for elem in para:
#     item = elem.popitem()
#     paragraphs.append(item[1])
#     paragraph_titel.append(item[0])
# print(paragraphs, paragraph_titel)

settings.configure()
print(str(datetime.now() + timedelta(days=1)))