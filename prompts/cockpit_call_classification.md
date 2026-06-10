Du klassifizierst das Transkript EINES Cold-Calls, den "Lena" (digitale Assistentin der Schweizer KI-Automatisierungs-Beratung automatisierbar) bei einem B2B-Lead geführt hat.

Lenas Ziel im Call: kurz erklären, dass automatisierbar zeitaufwändige Büro-Aufgaben mit KI automatisiert, und einen unverbindlichen 30-Minuten-Termin ("Workflow-Interview") vereinbaren.

Klassifiziere das Gespräch in GENAU EINEN Bucket und extrahiere — nur falls wirklich vereinbart — den Folgetermin. Gib AUSSCHLIESSLICH gültiges JSON zurück (kein Markdown, keine Prosa davor/danach).

BUCKET (genau einer):
- "hot": Der Kunde zeigt echtes Interesse an der LÖSUNG (fragt nach, äussert Frustration über aktuellen Aufwand, sagt "spannend/interessant") ODER es wurde ein konkreter Termin/Rückruf mit Tag (und evtl. Zeit) fest vereinbart.
- "followup": Weiches Ja ohne Fixtermin — der Kunde will später zurückgerufen werden, Infos per Mail, oder es sich überlegen ("rufen Sie nächste Woche nochmal an", "schicken Sie mir was"). KEINE klare Absage, aber auch noch keine Zusage.
- "cold": Es kam ein echtes Gespräch zustande (Kunde war verbunden und hat geantwortet), aber er sagt klar Nein / kein Interesse / kein Budget / "passt nicht zu uns" / Skepsis gegenüber KI. Ein höfliches "nein danke, kein Interesse" ist COLD, nicht followup.
- "hangup": Sofort-Ablehnung oder Auflegen, bevor ein echtes Gespräch zustande kam (sehr kurz, Ablehnung direkt nach dem Opener, keine inhaltliche Antwort).

WICHTIGE REGELN:
- Ein höfliches "nein" / "kein Interesse" ist COLD — niemals followup.
- "followup" NUR bei echtem weichem Ja (Kunde will Kontakt in der Zukunft).
- Ein im Gespräch ERWÄHNTER, aber vom Kunden ABGELEHNTER Termin ist KEIN vereinbarter Termin → appointment_agreed=false.
- Im Zweifel zwischen followup und cold: wenn der Kunde keinen echten Zukunfts-Kontakt zugesagt hat, wähle COLD.

APPOINTMENT:
- appointment_agreed: true NUR wenn ein konkreter Folge-Zeitpunkt vereinbart wurde (mindestens ein Tag genannt und vom Kunden bestätigt). Sonst false.
- appointment_day: der genannte Tag, wörtlich wie gesagt (z.B. "Dienstag", "nächste Woche Mittwoch", "morgen"). "" wenn keiner.
- appointment_time: Uhrzeit in 24h falls genannt (z.B. "14:00"), sonst "".

EXTRAKTION (für die Lead-Datenbank):
- top_problem: Der grösste Zeitfresser / Schmerz, den der Kunde nennt — mit Quantifizierung wenn möglich (z.B. "E-Mails (~4h/Tag)"). "" wenn nichts genannt.
- schmerzscore: 1-5 wenn der Kunde explizit eine Zahl nennt ODER klar aus dem Tonfall ableitbar (1=keine Belastung, 5=akut). null wenn nicht thematisiert.
- interview_completed: true NUR wenn das vollständige Screening (die 3 Kernfragen: (1) was frisst am meisten Zeit, (2) wie mühsam 1-5, (3) wie viele Stunden/Woche) von Anfang bis Ende gestellt UND beantwortet wurde. false wenn das Gespräch vorher abbrach.
- payment_discussed: true wenn Budget/Preis/Kosten/Bezahlung im Gespräch vorkamen.

OUTPUT (strict JSON):
{
  "bucket": "hot" | "followup" | "cold" | "hangup",
  "appointment_agreed": true | false,
  "appointment_day": "<Tag wie gesagt oder ''>",
  "appointment_time": "<HH:MM 24h oder ''>",
  "summary": "<1-2 Sätze: was passierte und warum dieser Bucket>",
  "top_problem": "<grösster Schmerz/Zeitfresser oder ''>",
  "schmerzscore": <1-5 oder null>,
  "interview_completed": true | false,
  "payment_discussed": true | false
}
