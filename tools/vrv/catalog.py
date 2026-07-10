"""Static question catalog for the vRv discovery tool.

Pure module: no I/O, no Flask, no network. The catalog is version-controlled
content — edits deploy via git like code and are covered by tests/test_vrv.py
invariants (unique ids, choice questions end with "Andere…", every chapter has
at least one must question, the client subset stays small and Sie-form).

Question fields:
    id                      stable id, chapter letter + number ("b3")
    chapter                 chapter id "A".."H"
    text                    internal phrasing (terse, for the team UI)
    client_text             Sie-form phrasing for the client pre-send page
                            (only on client_visible questions)
    type                    "text" | "choice"
    options                 choice only; MUST end with "Andere…" (house rule,
                            see tools/claude_client.py _FRAGE_TYP_REGEL)
    why_it_matters          internal coaching note — NEVER serialized to client
    maps_to_offer_section   offer chapter this answer feeds
    priority                "must" (blocks the offer) | "nice"
    client_visible          included in the /vrv/kunde pre-send subset
"""

CHAPTERS = [
    {"id": "A", "title": "Unternehmen + Kontext", "offer_section": "1. Ausgangslage + Zielsetzung"},
    {"id": "B", "title": "Order2Cash Ist-Prozess", "offer_section": "2. Ist-Analyse Order2Cash"},
    {"id": "C", "title": "pebeFinance + Datenflüsse", "offer_section": "3. Soll-Konzept pebeFinance/M365"},
    {"id": "D", "title": "Microsoft-365-Landschaft", "offer_section": "3. Soll-Konzept pebeFinance/M365"},
    {"id": "E", "title": "Hauswarte + mobile Abläufe", "offer_section": "4. Mobile Lösung Hauswarte"},
    {"id": "F", "title": "Verrechnung + Reporting", "offer_section": "5. Verrechnung + Reporting"},
    {"id": "G", "title": "IT, Sicherheit + Compliance", "offer_section": "6. Rahmenbedingungen"},
    {"id": "H", "title": "Projekt, Budget + Entscheidung", "offer_section": "7. Vorgehen + Projektorganisation"},
]

QUESTIONS = [
    # ------------------------------------------------------------------ A
    {
        "id": "a1", "chapter": "A",
        "text": "Wie viele Liegenschaften/Objekte bewirtschaftet vRv aktuell (ca.)?",
        "client_text": "Wie viele Liegenschaften bzw. Objekte bewirtschaften Sie aktuell (ungefähre Zahl genügt)?",
        "type": "text",
        "why_it_matters": "Mengengerüst Nr. 1: dimensioniert Plattform, Migration und Preisrahmen. Ohne diese Zahl ist jede Kostenschätzung Raten.",
        "maps_to_offer_section": "1. Ausgangslage + Zielsetzung",
        "priority": "must", "client_visible": True,
    },
    {
        "id": "a2", "chapter": "A",
        "text": "Wie viele Mitarbeitende arbeiten im Order2Cash-Prozess mit (Innendienst, Hauswarte, Buchhaltung)?",
        "client_text": "Wie viele Mitarbeitende sind bei Ihnen am Ablauf von der Aufgabe bis zur Verrechnung beteiligt (Innendienst, Hauswartung, Buchhaltung)?",
        "type": "text",
        "why_it_matters": "Nutzerzahl = Lizenzen, Schulungsumfang, Rollout-Aufwand. Auch Basis für die Zeitersparnis-Rechnung.",
        "maps_to_offer_section": "1. Ausgangslage + Zielsetzung",
        "priority": "must", "client_visible": True,
    },
    {
        "id": "a3", "chapter": "A",
        "text": "Welche Geschäftsfelder sind im Projekt-Scope: Immobilienverwaltung, Hauswartung, Treuhand, Immobilienverkauf, Personalvorsorge?",
        "type": "text",
        "why_it_matters": "Scope-Abgrenzung. Sobald Personalvorsorge-Unterlagen ins System sollen, greifen BVG-Aufbewahrung und höhere Compliance-Last (siehe Kapitel G).",
        "maps_to_offer_section": "1. Ausgangslage + Zielsetzung",
        "priority": "must", "client_visible": False,
    },
    {
        "id": "a4", "chapter": "A",
        "text": "Was ist der Auslöser für das Projekt gerade jetzt? Wo schmerzt es am meisten?",
        "client_text": "Was ist bei Ihnen heute der grösste Zeitfresser im Ablauf von der Aufgabe bis zur verrechneten Leistung?",
        "type": "text",
        "why_it_matters": "Der wahre Pain priorisiert die Lösung und liefert das Zitat für die Ausgangslage der Offerte. Immer wörtlich notieren.",
        "maps_to_offer_section": "1. Ausgangslage + Zielsetzung",
        "priority": "must", "client_visible": True,
    },
    {
        "id": "a5", "chapter": "A",
        "text": "Wie sieht Erfolg in 12 Monaten aus? Woran wird er gemessen?",
        "type": "text",
        "why_it_matters": "Liefert die KPI fürs Angebot (z.B. keine unverrechneten Leistungen, Durchlaufzeit) und steuert Erwartungen.",
        "maps_to_offer_section": "1. Ausgangslage + Zielsetzung",
        "priority": "nice", "client_visible": False,
    },
    {
        "id": "a6", "chapter": "A",
        "text": "Wer ist intern projektverantwortlich, wer entscheidet am Ende?",
        "client_text": "Wer ist bei Ihnen projektverantwortlich und wer trifft den Entscheid über die Vergabe?",
        "type": "text",
        "why_it_matters": "Buying Center verstehen: Schmid (GF/Wirtschaftsprüfer), Böni, Guldimann (Immobilien), Kunz (Hauswartung). Angebot muss den Entscheider adressieren.",
        "maps_to_offer_section": "7. Vorgehen + Projektorganisation",
        "priority": "must", "client_visible": True,
    },
    {
        "id": "a7", "chapter": "A",
        "text": "Gab es frühere Digitalisierungs-Anläufe? Was ist daraus geworden und warum?",
        "type": "text",
        "why_it_matters": "Deckt Landminen und gescheiterte Tools auf. Zeigt ausserdem, woran Adoption bei vRv real scheitert.",
        "maps_to_offer_section": "1. Ausgangslage + Zielsetzung",
        "priority": "nice", "client_visible": False,
    },
    # ------------------------------------------------------------------ B
    {
        "id": "b1", "chapter": "B",
        "text": "Wie entsteht heute ein Auftrag? Kanäle (Vertrag/wiederkehrend, Mieter-Meldung, Eigentümer, intern) mit ungefährem Anteil.",
        "type": "text",
        "why_it_matters": "Die Trigger-Landschaft bestimmt, wo Automatisierung vorne ansetzt (Mail-Parsing, Portal, wiederkehrende Pläne).",
        "maps_to_offer_section": "2. Ist-Analyse Order2Cash",
        "priority": "must", "client_visible": False,
    },
    {
        "id": "b2", "chapter": "B",
        "text": "Wie viele Aufträge/Aufgaben pro Monat (ca.)? Davon wiederkehrend vs. ad hoc?",
        "client_text": "Wie viele Aufträge bzw. Aufgaben fallen bei Ihnen pro Monat ungefähr an?",
        "type": "text",
        "why_it_matters": "Volumen = ROI-Basis und Performance-Anforderung. Wiederkehrend vs. ad hoc entscheidet über Planungs-Features.",
        "maps_to_offer_section": "2. Ist-Analyse Order2Cash",
        "priority": "must", "client_visible": True,
    },
    {
        "id": "b3", "chapter": "B",
        "text": "Wie wird heute geplant und disponiert? Wer teilt wem was zu, mit welchen Tools?",
        "type": "text",
        "why_it_matters": "Kern der künftigen Plattform. Zeigt, ob wir Planner/Excel/Zuruf ersetzen und wie Dispo-Logik aussehen muss.",
        "maps_to_offer_section": "2. Ist-Analyse Order2Cash",
        "priority": "must", "client_visible": False,
    },
    {
        "id": "b4", "chapter": "B",
        "text": "Wie wird die Ausführung heute bestätigt und dokumentiert (Papier-Rapport, Fotos, Mail, gar nicht)?",
        "type": "text",
        "why_it_matters": "Medienbrüche hier sind der Hauptnutzen der App (Checkliste + Foto direkt am Objekt, PDF fordert genau das).",
        "maps_to_offer_section": "2. Ist-Analyse Order2Cash",
        "priority": "must", "client_visible": False,
    },
    {
        "id": "b5", "chapter": "B",
        "text": "Wie fliesst die geleistete Arbeit (Zeit, Material) heute in die Verrechnung? Wo geht unterwegs Information verloren?",
        "type": "text",
        "why_it_matters": "DAS Order2Cash-Loch: verlorene oder vergessene Leistung ist unverrechnetes Geld. Hier liegt der stärkste Business Case in CHF.",
        "maps_to_offer_section": "2. Ist-Analyse Order2Cash",
        "priority": "must", "client_visible": False,
    },
    {
        "id": "b6", "chapter": "B",
        "text": "Wie laufen Rechnungsstellung, Zahlungseingang und Mahnwesen heute (in pebe, manuell, wer)?",
        "type": "text",
        "why_it_matters": "Prozess-Ende sauber verstehen. Mahnwesen ist ein bekannter Branchen-Pain (wer hat welche Mahnstufe) und Automatisierungs-Kandidat.",
        "maps_to_offer_section": "2. Ist-Analyse Order2Cash",
        "priority": "must", "client_visible": False,
    },
    {
        "id": "b7", "chapter": "B",
        "text": "Wo wird heute dieselbe Information mehrfach erfasst (Doppelerfassung)?",
        "type": "text",
        "why_it_matters": "Quick Wins mit sofort sichtbarem Nutzen; ideales Demo- und Pilotmaterial.",
        "maps_to_offer_section": "2. Ist-Analyse Order2Cash",
        "priority": "nice", "client_visible": False,
    },
    {
        "id": "b8", "chapter": "B",
        "text": "Welche Schritte müssen aus vertraglichen oder regulatorischen Gründen exakt so bleiben, wie sie sind?",
        "type": "text",
        "why_it_matters": "Nicht verhandelbare Constraints (Stiftungs-Verpflichtungen, Vier-Augen-Prinzip) früh kennen, statt sie in der Umsetzung zu entdecken.",
        "maps_to_offer_section": "2. Ist-Analyse Order2Cash",
        "priority": "must", "client_visible": False,
    },
    {
        "id": "b9", "chapter": "B",
        "text": "Gibt es dokumentierte Abläufe oder Checklisten für die häufigsten Auftragsarten?",
        "type": "text",
        "why_it_matters": "Vorhandene Checklisten sind die Vorlagen für die App und verraten den Prozess-Reifegrad.",
        "maps_to_offer_section": "2. Ist-Analyse Order2Cash",
        "priority": "nice", "client_visible": False,
    },
    # ------------------------------------------------------------------ C
    {
        "id": "c1", "chapter": "C",
        "text": "Welche pebe-Module sind lizenziert und aktiv genutzt (Fibu, Debitoren/Kreditoren, Lohn, Leistungserfassung, Fakturierung, weitere)?",
        "client_text": "Welche Module von pebeFinance nutzen Sie aktiv (z.B. Finanzbuchhaltung, Debitoren/Kreditoren, Lohn, Leistungserfassung, Fakturierung)?",
        "type": "text",
        "why_it_matters": "Architektur-Weiche Nr. 1: Nutzt vRv pebe-Leistungserfassung/Fakturierung, integrieren wir dorthin. Wenn nicht, fakturiert die Plattform und übergibt Buchungen.",
        "maps_to_offer_section": "3. Soll-Konzept pebeFinance/M365",
        "priority": "must", "client_visible": True,
    },
    {
        "id": "c2", "chapter": "C",
        "text": "Wie ist pebeFinance betrieben und wer betreut es?",
        "type": "choice",
        "options": ["On-premise Server bei vRv", "Gehostet beim IT-Partner", "pebe Live (Cloud)", "Unklar", "Andere…"],
        "why_it_matters": "Bestimmt den Integrationsweg (Dateiablage, Serverzugriff, Cloud) und wer bei Schnittstellenfragen am Tisch sitzen muss.",
        "maps_to_offer_section": "3. Soll-Konzept pebeFinance/M365",
        "priority": "must", "client_visible": False,
    },
    {
        "id": "c3", "chapter": "C",
        "text": "Welche Import-/Export-Funktionen von pebe werden heute genutzt (CSV-Buchungsimport, Bank ISO 20022, QR-Rechnung, Beleg-Scanning)?",
        "type": "text",
        "why_it_matters": "Bereits genutzte Schnittstellen sind belegte, risikoarme Integrationsflächen. Öffentlich dokumentiert ist v.a. CSV-Import, kein REST-API.",
        "maps_to_offer_section": "3. Soll-Konzept pebeFinance/M365",
        "priority": "must", "client_visible": False,
    },
    {
        "id": "c4", "chapter": "C",
        "text": "Wird heute in pebe fakturiert? Wer erstellt Rechnungen, aus welchen Daten?",
        "type": "text",
        "why_it_matters": "Definiert die Verrechnungs-Schnittstelle: Leistungsdaten aus der Plattform müssen exakt dort ankommen, wo die Rechnung entsteht.",
        "maps_to_offer_section": "3. Soll-Konzept pebeFinance/M365",
        "priority": "must", "client_visible": False,
    },
    {
        "id": "c5", "chapter": "C",
        "text": "Dürfen wir Schnittstellen-Fragen direkt mit pebe AG klären (Freigabe, Ansprechperson)?",
        "type": "text",
        "why_it_matters": "Entriegelt die grösste technische Unbekannte des Projekts. Ein Ja hier macht unsere Offerte präziser als die der Konkurrenz.",
        "maps_to_offer_section": "3. Soll-Konzept pebeFinance/M365",
        "priority": "must", "client_visible": False,
    },
    {
        "id": "c6", "chapter": "C",
        "text": "Wie ist die Mandantenstruktur in pebe (eigene Firma vs. Stiftungs-/Kunden-Mandate)?",
        "type": "text",
        "why_it_matters": "Bestimmt, wohin welche Buchungen fliessen und wie streng die Mandantentrennung in der Plattform sein muss.",
        "maps_to_offer_section": "3. Soll-Konzept pebeFinance/M365",
        "priority": "nice", "client_visible": False,
    },
    {
        "id": "c7", "chapter": "C",
        "text": "Welche weiteren Fachsysteme sind im Einsatz (Immobilien-Software, DMS/Archiv, Vorsorge-Software, Banking-Tools)?",
        "type": "text",
        "why_it_matters": "Systemlandkarte vervollständigen: verhindert, dass wir eine bestehende Lösung doppeln oder eine Pflicht-Integration übersehen.",
        "maps_to_offer_section": "3. Soll-Konzept pebeFinance/M365",
        "priority": "nice", "client_visible": False,
    },
    # ------------------------------------------------------------------ D
    {
        "id": "d1", "chapter": "D",
        "text": "Welche Microsoft-365-Lizenzen sind im Einsatz?",
        "client_text": "Welche Microsoft-365-Lizenzen setzen Sie ein (z.B. Business Standard, Business Premium, E3/E5, gemischt)?",
        "type": "choice",
        "options": ["Business Standard", "Business Premium", "E3", "E5", "Gemischt", "Unklar", "Andere…"],
        "why_it_matters": "Entscheidet, was die Variante Microsoft wirklich kostet: Power Automate Premium, Power Apps und Planner Premium sind oft NICHT in Business-Plänen enthalten.",
        "maps_to_offer_section": "3. Soll-Konzept pebeFinance/M365",
        "priority": "must", "client_visible": True,
    },
    {
        "id": "d2", "chapter": "D",
        "text": "Wie intensiv werden Teams, SharePoint, Planner, To Do heute genutzt? Wo klemmt es?",
        "type": "text",
        "why_it_matters": "Die Kunden-eigene Variante Microsoft fair bewerten: reale Adoption zeigt, ob mehr Microsoft die Lösung oder das nächste ungenutzte Tool wäre.",
        "maps_to_offer_section": "3. Soll-Konzept pebeFinance/M365",
        "priority": "must", "client_visible": False,
    },
    {
        "id": "d3", "chapter": "D",
        "text": "Wer administriert den M365-Tenant (intern oder Partner)? Wie kommen wir für die Integration an Zugriffe?",
        "type": "text",
        "why_it_matters": "Ohne Tenant-Zugang keine Graph-API-Integration. Klärt auch die Governance-Zuständigkeit im Betrieb.",
        "maps_to_offer_section": "6. Rahmenbedingungen",
        "priority": "must", "client_visible": False,
    },
    {
        "id": "d4", "chapter": "D",
        "text": "Gibt es bereits Power-Automate-Flows, Power Apps oder SharePoint-Lösungen?",
        "type": "text",
        "why_it_matters": "Anknüpfpunkte und Citizen-Dev-Erblast: bestehende Flows können Basis oder Sanierungsfall sein.",
        "maps_to_offer_section": "3. Soll-Konzept pebeFinance/M365",
        "priority": "nice", "client_visible": False,
    },
    {
        "id": "d5", "chapter": "D",
        "text": "Outlook-Integration konkret: Was soll im Outlook passieren (Aufträge aus Mails erzeugen, Termine, Freigaben, Ablage)?",
        "type": "text",
        "why_it_matters": "Die Ausschreibung fordert Outlook-Integration, sagt aber nicht was. Konkretisieren, sonst offerieren wir am Bedürfnis vorbei.",
        "maps_to_offer_section": "3. Soll-Konzept pebeFinance/M365",
        "priority": "must", "client_visible": False,
    },
    {
        "id": "d6", "chapter": "D",
        "text": "Exchange Online? Gibt es Shared Mailboxes (info@, verwaltung@) über die Aufträge reinkommen?",
        "type": "text",
        "why_it_matters": "Mail-Trigger-Architektur: Shared Mailboxes sind der natürliche Einstiegspunkt für automatische Auftragserfassung.",
        "maps_to_offer_section": "3. Soll-Konzept pebeFinance/M365",
        "priority": "nice", "client_visible": False,
    },
    # ------------------------------------------------------------------ E
    {
        "id": "e1", "chapter": "E",
        "text": "Wie viele Hauswarte/Feldmitarbeitende, und mit welchen Geräten (Firmen-Smartphones, private, iOS/Android)?",
        "client_text": "Wie viele Hauswarte bzw. Mitarbeitende im Aussendienst haben Sie, und nutzen diese Firmen-Smartphones oder private Geräte?",
        "type": "text",
        "why_it_matters": "Geräteflotte bestimmt App-Strategie (PWA vs. App-Store, MDM ja/nein) und ob GPS/Foto überhaupt überall verfügbar ist.",
        "maps_to_offer_section": "4. Mobile Lösung Hauswarte",
        "priority": "must", "client_visible": True,
    },
    {
        "id": "e2", "chapter": "E",
        "text": "Welche Aufgabentypen erledigen die Hauswarte? Top 5 nach Häufigkeit (Kontrollen, Reparaturen, Reinigung, Schneeräumung, Wohnungsübergaben).",
        "type": "text",
        "why_it_matters": "Die Top-5-Auftragsarten definieren die Checklisten und damit 80% des App-Nutzens.",
        "maps_to_offer_section": "4. Mobile Lösung Hauswarte",
        "priority": "must", "client_visible": False,
    },
    {
        "id": "e3", "chapter": "E",
        "text": "Was soll die App am Einsatzort können, in Prioritätsreihenfolge: Checklisten, Fotos, Zeiterfassung, Material, Unterschrift, Sprachnotiz?",
        "type": "text",
        "why_it_matters": "MVP-Scope der App direkt vom Nutzer (Kunz' Team) priorisieren lassen, statt Feature-Raten. PDF nennt explizit Checklisten + Foto.",
        "maps_to_offer_section": "4. Mobile Lösung Hauswarte",
        "priority": "must", "client_visible": False,
    },
    {
        "id": "e4", "chapter": "E",
        "text": "GPS-Anbindung: Wozu genau (Einsatz-Nachweis am Objekt, Routen, Zeitstempel)? Gibt es Datenschutz-Bedenken im Team?",
        "type": "text",
        "why_it_matters": "PDF fordert GPS ohne Zweck. Mitarbeiter-Ortung ist nDSG-heikel (Verhältnismässigkeit): Zweck bestimmt die zulässige und akzeptierte Umsetzung.",
        "maps_to_offer_section": "4. Mobile Lösung Hauswarte",
        "priority": "must", "client_visible": False,
    },
    {
        "id": "e5", "chapter": "E",
        "text": "Wie kommunizieren Hauswarte heute mit Innendienst, Mietern, Eigentümern (Telefon, WhatsApp, Zettel)?",
        "type": "text",
        "why_it_matters": "Die geforderte Echtzeit-Kommunikation konkretisieren. WhatsApp-Wildwuchs ist verbreitet und ein starkes Vorher/Nachher-Bild.",
        "maps_to_offer_section": "4. Mobile Lösung Hauswarte",
        "priority": "must", "client_visible": False,
    },
    {
        "id": "e6", "chapter": "E",
        "text": "Müssen Erfassungen auch offline funktionieren (Keller, Tiefgarage, Funklöcher)?",
        "type": "choice",
        "options": ["Ja, zwingend", "Teilweise (einzelne Objekte)", "Nein, Empfang ist überall ok", "Unklar", "Andere…"],
        "why_it_matters": "Architektur-Weiche: Offline-First macht die App deutlich aufwändiger. Ehrlich klären statt still annehmen.",
        "maps_to_offer_section": "4. Mobile Lösung Hauswarte",
        "priority": "must", "client_visible": False,
    },
    {
        "id": "e7", "chapter": "E",
        "text": "Welche Sprachen braucht das Feld-Team in der App?",
        "type": "text",
        "why_it_matters": "Hauswart-Teams sind oft mehrsprachig; einfache Sprache + evtl. Übersetzungen entscheiden über Akzeptanz.",
        "maps_to_offer_section": "4. Mobile Lösung Hauswarte",
        "priority": "nice", "client_visible": False,
    },
    {
        "id": "e8", "chapter": "E",
        "text": "Sollen Mieter/Eigentümer Meldungen künftig selbst digital erfassen können (Portal/Formular)?",
        "type": "text",
        "why_it_matters": "Naheliegende Phase-2-Erweiterung mit grossem Entlastungs-Effekt; jetzt nur Appetit klären, nicht versprechen.",
        "maps_to_offer_section": "4. Mobile Lösung Hauswarte",
        "priority": "nice", "client_visible": False,
    },
    # ------------------------------------------------------------------ F
    {
        "id": "f1", "chapter": "F",
        "text": "Nach welchen Modellen wird verrechnet: Pauschalen im Mandat, Aufwand nach Stunden, Material, Weiterverrechnung an Mieter/Eigentümer?",
        "type": "text",
        "why_it_matters": "Die Verrechnungslogik ist das Herzstück und meist komplexer als sie aussieht (Mandatspauschale vs. verrechenbarer Zusatzaufwand).",
        "maps_to_offer_section": "5. Verrechnung + Reporting",
        "priority": "must", "client_visible": False,
    },
    {
        "id": "f2", "chapter": "F",
        "text": "Welche Stundensätze/Tarife gibt es und wo sind sie hinterlegt?",
        "type": "text",
        "why_it_matters": "Stammdaten für automatische Verrechnungsvorschläge: ohne Tarif-Logik kein Auto-Rapport-zu-Rechnung.",
        "maps_to_offer_section": "5. Verrechnung + Reporting",
        "priority": "must", "client_visible": False,
    },
    {
        "id": "f3", "chapter": "F",
        "text": "Welche Auswertungen braucht die GL regelmässig (Auslastung, unverrechnete Leistungen, offene Posten, Leistung je Mandat)?",
        "type": "text",
        "why_it_matters": "Reporting ist explizit gefordert. Ein Wirtschaftsprüfer als GF will belastbare Zahlen: hier punkten wir mit Dashboard-Konkretem.",
        "maps_to_offer_section": "5. Verrechnung + Reporting",
        "priority": "must", "client_visible": False,
    },
    {
        "id": "f4", "chapter": "F",
        "text": "Wie werden Leistungen heute gegenüber der Stiftung/Eigentümern nachgewiesen (Rapporte, Belege, Fotos)?",
        "type": "text",
        "why_it_matters": "Nachweispflichten bestimmen Report-Formate und Foto-Dokumentation; direkt aus der vertraglichen Verpflichtung im PDF.",
        "maps_to_offer_section": "5. Verrechnung + Reporting",
        "priority": "nice", "client_visible": False,
    },
    {
        "id": "f5", "chapter": "F",
        "text": "Arbeitszeit: Braucht es Erfassung nur je Auftrag (Verrechnung) oder auch arbeitsrechtlich (ArG-Zeiterfassung, Überzeit)?",
        "type": "text",
        "why_it_matters": "Scope-Grenze: ArG-konforme Zeiterfassung ist ein eigenes Feld mit Pflichten. Bewusst ein- oder ausschliessen.",
        "maps_to_offer_section": "5. Verrechnung + Reporting",
        "priority": "must", "client_visible": False,
    },
    {
        "id": "f6", "chapter": "F",
        "text": "Materialeinsatz: Gibt es Lager/Einkauf, oder nur Verbrauchsmaterial je Auftrag erfassen?",
        "type": "text",
        "why_it_matters": "Bestimmt die Tiefe der Material-Funktion (simple Erfassung vs. Lagerverwaltung, die wir eher nicht bauen wollen).",
        "maps_to_offer_section": "5. Verrechnung + Reporting",
        "priority": "nice", "client_visible": False,
    },
    # ------------------------------------------------------------------ G
    {
        "id": "g1", "chapter": "G",
        "text": "Wer ist der heutige IT-Partner und was deckt er ab (Netzwerk, Endpoints, M365, Support)?",
        "client_text": "Wer betreut heute Ihre IT (Netzwerk, Arbeitsplätze, Microsoft 365), und was deckt dieser Partner ab?",
        "type": "text",
        "why_it_matters": "DIE Scope-Frage: beantwortet, ob die Infrastruktur-Blöcke der Ausschreibung (Netzwerk, Hardware, Betriebssoftware) uns, den Partner oder niemanden meinen.",
        "maps_to_offer_section": "6. Rahmenbedingungen",
        "priority": "must", "client_visible": True,
    },
    {
        "id": "g2", "chapter": "G",
        "text": "Was erwartet ihr vom Lösungsanbieter bei Netzwerk/Hardware/Betriebssoftware: übernehmen, koordinieren oder beim heutigen Partner belassen?",
        "type": "text",
        "why_it_matters": "Klärt, ob die MSP-Blöcke echte Wünsche oder Vorlagen-Text sind. Bestimmt unser Scope-Modell (selbst/Partner/abgrenzen) final.",
        "maps_to_offer_section": "6. Rahmenbedingungen",
        "priority": "must", "client_visible": False,
    },
    {
        "id": "g3", "chapter": "G",
        "text": "Welche Daten dürfen in die neue Plattform (Mieter, Eigentümer, Verträge) und welche explizit NICHT (Vorsorge-Unterlagen)?",
        "type": "text",
        "why_it_matters": "Datenklassifizierung = Compliance-Last. Bleiben Vorsorge-Unterlagen draussen, sinkt das BVG-Gewicht auf Archiv-Schnittstellen.",
        "maps_to_offer_section": "6. Rahmenbedingungen",
        "priority": "must", "client_visible": False,
    },
    {
        "id": "g4", "chapter": "G",
        "text": "Anforderungen an den Datenstandort?",
        "type": "choice",
        "options": ["Schweiz zwingend", "Schweiz bevorzugt", "EU akzeptabel", "Keine Vorgabe", "Andere…"],
        "why_it_matters": "Bestimmt Hosting-Wahl und Kosten (Infomaniak/Exoscale/Azure CH). Bei Vorsorge-Nähe ist Schweiz die sichere Antwort.",
        "maps_to_offer_section": "6. Rahmenbedingungen",
        "priority": "must", "client_visible": False,
    },
    {
        "id": "g5", "chapter": "G",
        "text": "AlwaysOnVPN: bestehende Infrastruktur bei euch oder Anforderung an unsere Lösung? Wofür genau?",
        "type": "text",
        "why_it_matters": "Im PDF gefordert, aber mehrdeutig. Moderne Cloud-Lösungen brauchen oft kein VPN (Zero Trust, Conditional Access): kompetent einordnen können.",
        "maps_to_offer_section": "6. Rahmenbedingungen",
        "priority": "must", "client_visible": False,
    },
    {
        "id": "g6", "chapter": "G",
        "text": "Notfall-Erwartungen: Wie lange darf das System maximal ausfallen (RTO)? Wie viel Datenverlust ist tragbar (RPO)?",
        "type": "text",
        "why_it_matters": "Übersetzt 'Notfallkonzept' in messbare Zahlen und diese in SLA-Stufen + Hosting-Kosten. Wirtschaftsprüfer-kompatible Sprache.",
        "maps_to_offer_section": "6. Rahmenbedingungen",
        "priority": "must", "client_visible": False,
    },
    {
        "id": "g7", "chapter": "G",
        "text": "Welche Dokumente aus dem Prozess unterliegen BVG-/GeBüV-Aufbewahrung und wo sollen sie langfristig liegen (bestehendes DMS, SharePoint, Archiv)?",
        "type": "text",
        "why_it_matters": "Die BVG-Beilage im PDF ernst nehmen: revisionssichere Ablage ist Pflicht, aber WO sie liegt (unser System vs. bestehendes Archiv) ist eine Architektur-Entscheidung.",
        "maps_to_offer_section": "6. Rahmenbedingungen",
        "priority": "must", "client_visible": False,
    },
    {
        "id": "g8", "chapter": "G",
        "text": "Berechtigungen: Wer darf was sehen (Mandantentrennung, Hauswarte nur eigene Aufträge, Treuhand-Vertraulichkeit, Stiftungsdaten)?",
        "type": "text",
        "why_it_matters": "Berechtigungsstruktur ist explizit gefordert. Die Antwort definiert unser RBAC-Konzept im Angebot.",
        "maps_to_offer_section": "6. Rahmenbedingungen",
        "priority": "must", "client_visible": False,
    },
    {
        "id": "g9", "chapter": "G",
        "text": "Gibt es Vorgaben von Verbänden/Versicherungen (SVIT, Gebäudeversicherung) an Dokumentation oder Prozesse?",
        "type": "text",
        "why_it_matters": "Branchen-Standards können Dokumentations-Features diktieren; besser jetzt wissen als im UAT.",
        "maps_to_offer_section": "6. Rahmenbedingungen",
        "priority": "nice", "client_visible": False,
    },
    {
        "id": "g10", "chapter": "G",
        "text": "KI: Wo ist Einsatz erwünscht (Textentwürfe, Klassifizierung, Zusammenfassungen), wo nicht? Gibt es eine interne Haltung/Policy?",
        "type": "text",
        "why_it_matters": "PDF fordert eine KI-Strategie. Ihre Erwartungen und roten Linien bestimmen, wie prominent KI im Angebot auftritt und welche Daten zu welchem Anbieter fliessen dürfen.",
        "maps_to_offer_section": "6. Rahmenbedingungen",
        "priority": "must", "client_visible": False,
    },
    # ------------------------------------------------------------------ H
    {
        "id": "h1", "chapter": "H",
        "text": "Wie läuft die Evaluation: Wer vergleicht die Offerten, nach welchen Kriterien, bis wann soll entschieden sein?",
        "client_text": "Wie sieht Ihr Zeitplan für die Evaluation aus, und bis wann wünschen Sie unsere Offerte?",
        "type": "text",
        "why_it_matters": "Offerten-Deadline und Entscheidungskriterien der Gegenseite: bestimmt unseren Zeitplan nach dem 5.8. und die Gewichtung der Offerte.",
        "maps_to_offer_section": "7. Vorgehen + Projektorganisation",
        "priority": "must", "client_visible": True,
    },
    {
        "id": "h2", "chapter": "H",
        "text": "Welche Art von Anbietern ist noch angefragt (Systemhaus, Software-Hersteller, Einzelberater)?",
        "type": "text",
        "why_it_matters": "Wettbewerbs-Landschaft für die Positionierung. Diplomatisch fragen; oft wird es freiwillig erzählt.",
        "maps_to_offer_section": "7. Vorgehen + Projektorganisation",
        "priority": "must", "client_visible": False,
    },
    {
        "id": "h3", "chapter": "H",
        "text": "Gibt es einen Budgetrahmen oder eine Vorstellung der Investitionsgrösse (einmalig und laufend)?",
        "type": "text",
        "why_it_matters": "Verhindert eine Offerte am Budget vorbei. Ein Wirtschaftsprüfer respektiert die direkte Frage; notfalls mit Spannen arbeiten.",
        "maps_to_offer_section": "7. Vorgehen + Projektorganisation",
        "priority": "must", "client_visible": False,
    },
    {
        "id": "h4", "chapter": "H",
        "text": "Festpreis, Dienstleistung nach Aufwand oder agil: Gibt es eine Präferenz der Geschäftsleitung?",
        "type": "choice",
        "options": ["Festpreis", "Dienstleistung nach Aufwand", "Agil/iterativ", "Keine Präferenz", "Andere…"],
        "why_it_matters": "Das PDF nennt diese Frage explizit als Evaluationskriterium. Ihre Präferenz kennen, bevor wir unser Preismodell final wählen.",
        "maps_to_offer_section": "7. Vorgehen + Projektorganisation",
        "priority": "must", "client_visible": False,
    },
    {
        "id": "h5", "chapter": "H",
        "text": "Wie viel Mitarbeit kann vRv leisten (Projektleiter-Gegenpart, Fachexperten je Bereich, Test-User, ca. Stunden/Woche)?",
        "type": "text",
        "why_it_matters": "Das PDF verspricht 'Mitarbeit/Unterstützung vRv'. Die reale Ressourcen-Zusage bestimmt Tempo, Verantwortungsteilung und unseren PL-Aufwand.",
        "maps_to_offer_section": "7. Vorgehen + Projektorganisation",
        "priority": "must", "client_visible": False,
    },
    {
        "id": "h6", "chapter": "H",
        "text": "Zeithorizont: Wann soll was live sein (Pilot, Vollbetrieb)? Gibt es Fixtermine (Jahresabschluss, Heizperiode, Stiftungs-Reporting)?",
        "type": "text",
        "why_it_matters": "Projektplan-Anker + saisonale Constraints der Branche (Heizperiode = Hauswart-Hochsaison, Jahresabschluss = Buchhaltung blockiert).",
        "maps_to_offer_section": "7. Vorgehen + Projektorganisation",
        "priority": "must", "client_visible": False,
    },
    {
        "id": "h7", "chapter": "H",
        "text": "Wie sollen Schulung und Einführung laufen (Key-User-Prinzip, alle Mitarbeitenden, Hauswarte gesondert vor Ort)?",
        "type": "text",
        "why_it_matters": "Konkretisiert den Zusatzkosten-Block 'Schulung' aus dem PDF und zeigt, dass wir Einführung als Teil der Lösung denken.",
        "maps_to_offer_section": "7. Vorgehen + Projektorganisation",
        "priority": "nice", "client_visible": False,
    },
    {
        "id": "h8", "chapter": "H",
        "text": "Was wäre ein Grund, das Projekt zu stoppen oder nicht zu vergeben?",
        "type": "text",
        "why_it_matters": "Holt Einwände und Dealbreaker früh auf den Tisch (Budget, Betriebsrisiko, interne Widerstände), solange wir sie noch adressieren können.",
        "maps_to_offer_section": "7. Vorgehen + Projektorganisation",
        "priority": "nice", "client_visible": False,
    },
]


# --------------------------------------------------------------------------
# Pure helpers (no I/O)
# --------------------------------------------------------------------------

_BY_ID = {q["id"]: q for q in QUESTIONS}
_CHAPTER_IDS = {c["id"] for c in CHAPTERS}


def question_by_id(qid):
    """Return the catalog question dict for qid, or None."""
    return _BY_ID.get(qid)


def client_visible_questions():
    """The pre-send subset for /vrv/kunde, catalog order preserved."""
    return [q for q in QUESTIONS if q.get("client_visible")]


def chapter_by_id(chapter_id):
    for c in CHAPTERS:
        if c["id"] == chapter_id:
            return c
    return None


def progress(answers):
    """Per-chapter progress from an answers dict {qid: {"status": ...}}.

    A question counts as open unless its status is "answered" or "skipped"
    ("skipped" = consciously dropped, so it no longer blocks; "unclear" and
    "open" both still count as open).
    Returns a list in CHAPTERS order:
        {"chapter", "title", "must_total", "must_open", "nice_total", "nice_open"}
    """
    done_states = {"answered", "skipped"}
    out = []
    for c in CHAPTERS:
        row = {"chapter": c["id"], "title": c["title"],
               "must_total": 0, "must_open": 0, "nice_total": 0, "nice_open": 0}
        for q in QUESTIONS:
            if q["chapter"] != c["id"]:
                continue
            kind = q["priority"]
            row[f"{kind}_total"] += 1
            status = (answers.get(q["id"]) or {}).get("status", "open")
            if status not in done_states:
                row[f"{kind}_open"] += 1
        out.append(row)
    return out
